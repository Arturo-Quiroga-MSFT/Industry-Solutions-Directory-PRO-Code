#!/usr/bin/env python3
"""
Step 2: Read solutions from SQL DB, generate embeddings, upload to Azure AI Search.

Flow:
  1. Query dbo.vw_ISDSolution_All (approved solutions only)
  2. Deduplicate – collapse by solutionName, aggregating multi-valued fields
  3. Generate embeddings with text-embedding-3-large
  4. Upload documents to the search index in batches
"""

import sys, os, re, hashlib, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

import pyodbc
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential


# ── helpers ──────────────────────────────────────────────────────────────────

def strip_html(text: str | None) -> str:
    """Remove HTML tags and collapse whitespace."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def make_id(name: str) -> str:
    """Deterministic document id from solution name."""
    return hashlib.sha256(name.encode("utf-8")).hexdigest()[:32]


def get_search_credential():
    if config.SEARCH_API_KEY:
        return AzureKeyCredential(config.SEARCH_API_KEY)
    return DefaultAzureCredential()


# ── Step 1: read from SQL ────────────────────────────────────────────────────

def read_solutions() -> list[dict]:
    """Read all approved solutions from the SQL view and deduplicate."""
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={config.SQL_SERVER};"
        f"DATABASE={config.SQL_DATABASE};"
        f"UID={config.SQL_USERNAME};"
        f"PWD={config.SQL_PASSWORD};"
        f"ApplicationIntent=ReadOnly;"
        f"Encrypt=yes;TrustServerCertificate=no"
    )

    query = f"""
        SELECT
            solutionName,
            solutionDescription,
            orgName,
            orgDescription,
            industryName,
            subIndustryName,
            solutionAreaName,
            theme,
            geoName,
            marketPlaceLink,
            solutionOrgWebsite,
            logoFileLink,
            solutionStatus
        FROM {config.SQL_VIEW}
        WHERE solutionStatus = 'Approved'
    """

    print("Connecting to SQL database …")
    conn = pyodbc.connect(conn_str, timeout=30)
    cursor = conn.cursor()
    cursor.execute(query)
    columns = [desc[0] for desc in cursor.description]
    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    print(f"  Fetched {len(rows):,} rows from {config.SQL_VIEW}")

    # ── deduplicate by solutionName ──────────────────────────────────────
    solutions: dict[str, dict] = {}
    for row in rows:
        name = (row.get("solutionName") or "").strip()
        if not name:
            continue

        if name not in solutions:
            solutions[name] = {
                "solution_name": name,
                "solution_description": strip_html(row.get("solutionDescription")),
                "partner_name": (row.get("orgName") or "").strip(),
                "partner_description": strip_html(row.get("orgDescription")),
                "marketplace_link": row.get("marketPlaceLink") or "",
                "partner_website": row.get("solutionOrgWebsite") or "",
                "logo_url": row.get("logoFileLink") or "",
                "solution_status": row.get("solutionStatus") or "",
                # sets for collecting multi-valued
                "_industries": set(),
                "_sub_industries": set(),
                "_solution_areas": set(),
                "_themes": set(),
                "_geos": set(),
            }

        sol = solutions[name]
        if row.get("industryName"):
            sol["_industries"].add(row["industryName"].strip())
        if row.get("subIndustryName"):
            sol["_sub_industries"].add(row["subIndustryName"].strip())
        if row.get("solutionAreaName"):
            sol["_solution_areas"].add(row["solutionAreaName"].strip())
        if row.get("theme"):
            sol["_themes"].add(row["theme"].strip())
        if row.get("geoName"):
            sol["_geos"].add(row["geoName"].strip())

    # flatten & build content field
    docs = []
    for sol in solutions.values():
        industries = sorted(sol.pop("_industries"))
        sub_industries = sorted(sol.pop("_sub_industries"))
        solution_areas = sorted(sol.pop("_solution_areas"))
        themes = sorted(sol.pop("_themes"))
        geos = sorted(sol.pop("_geos"))

        sol["industry"] = industries[0] if industries else ""
        sol["industries"] = industries
        sol["sub_industry"] = sub_industries[0] if sub_industries else ""
        sol["solution_area"] = solution_areas[0] if solution_areas else ""
        sol["solution_areas"] = solution_areas
        sol["theme"] = themes[0] if themes else ""
        sol["geos"] = geos

        sol["id"] = make_id(sol["solution_name"])

        # Build a rich text block for embedding
        parts = [
            f"Solution: {sol['solution_name']}",
            f"Partner: {sol['partner_name']}",
        ]
        if sol["solution_description"]:
            parts.append(f"Description: {sol['solution_description']}")
        if industries:
            parts.append(f"Industries: {', '.join(industries)}")
        if solution_areas:
            parts.append(f"Solution Areas: {', '.join(solution_areas)}")
        if themes:
            parts.append(f"Themes: {', '.join(themes)}")
        if geos:
            parts.append(f"Geographies: {', '.join(geos)}")
        if sol.get("partner_description"):
            parts.append(f"About partner: {sol['partner_description']}")

        sol["content"] = "\n".join(parts)
        docs.append(sol)

    print(f"  Deduplicated to {len(docs):,} unique solutions")
    return docs


# ── Step 2: generate embeddings ─────────────────────────────────────────────

def generate_embeddings(docs: list[dict]) -> list[dict]:
    """Add content_vector to each document."""
    client = AzureOpenAI(
        azure_endpoint=config.OPENAI_ENDPOINT,
        api_key=config.OPENAI_API_KEY,
        api_version=config.OPENAI_API_VERSION,
    )

    total = len(docs)
    bs = config.EMBEDDING_BATCH_SIZE

    print(f"\nGenerating embeddings ({config.EMBEDDING_MODEL}, {config.EMBEDDING_DIMENSIONS}d) …")
    for i in range(0, total, bs):
        batch = docs[i : i + bs]
        texts = [d["content"] for d in batch]
        try:
            resp = client.embeddings.create(
                input=texts,
                model=config.EMBEDDING_DEPLOYMENT,
                dimensions=config.EMBEDDING_DIMENSIONS,
            )
            for j, emb in enumerate(resp.data):
                docs[i + j]["content_vector"] = emb.embedding
        except Exception as e:
            print(f"  ERROR embedding batch {i // bs}: {e}")
            raise

        done = min(i + bs, total)
        print(f"  {done}/{total} embeddings generated", end="\r")

    print(f"  {total}/{total} embeddings generated ✓")
    return docs


# ── Step 3: upload to search ────────────────────────────────────────────────

def upload_documents(docs: list[dict]):
    """Upload documents to the Azure AI Search index in batches."""
    credential = get_search_credential()
    client = SearchClient(
        endpoint=config.SEARCH_ENDPOINT,
        index_name=config.INDEX_NAME,
        credential=credential,
    )

    total = len(docs)
    bs = config.BATCH_SIZE
    succeeded = 0
    failed = 0

    print(f"\nUploading {total} documents to index '{config.INDEX_NAME}' …")
    for i in range(0, total, bs):
        batch = docs[i : i + bs]
        results = client.upload_documents(documents=batch)
        for r in results:
            if r.succeeded:
                succeeded += 1
            else:
                failed += 1
                print(f"  FAILED: {r.key} – {r.error_message}")
        print(f"  {min(i + bs, total)}/{total} uploaded", end="\r")

    print(f"\n  Succeeded: {succeeded}  |  Failed: {failed}")
    return succeeded, failed


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("SQL → Azure AI Search Ingestion")
    print("=" * 60)
    t0 = time.time()

    docs = read_solutions()
    docs = generate_embeddings(docs)
    ok, fail = upload_documents(docs)

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s  –  {ok} indexed, {fail} failures.")


if __name__ == "__main__":
    main()
