# SQL-to-Search Ingestion Pipeline

> **Created**: February 16, 2026  
> **Purpose**: Read solutions directly from the ISD SQL database, generate vector embeddings, and index into Azure AI Search.

## Overview

This pipeline replaces the old API-scraping approach (`data-ingestion/integrated-vectorization/`) which reverse-engineered the ISD website APIs. That approach was fragile and the old search service (`indsolse-dev-srch-okumlm.search.windows.net`) has been deleted.

This new pipeline connects **directly to the SQL database**, deduplicates the denormalized view, generates embeddings with `text-embedding-3-large`, and uploads to a fresh Azure AI Search index.

---

## Architecture

```
┌──────────────────────┐     ┌──────────────────────┐     ┌──────────────────────────┐
│  SQL Server          │     │  Azure OpenAI        │     │  Azure AI Search         │
│  mssoldir-prd-sql    │────▶│  r2d2-foundry-001    │────▶│  aq-mysearch001          │
│  vw_ISDSolution_All  │     │  text-embedding-3-lg │     │  isd-solutions-v1        │
│  (4,934 rows)        │     │  (3072 dimensions)   │     │  (448 documents)         │
└──────────────────────┘     └──────────────────────┘     └──────────────────────────┘
```

**Flow**:
1. `01_create_index.py` — Creates the search index with schema and vector configuration
2. `02_ingest_from_sql.py` — Reads SQL → deduplicates → generates embeddings → uploads
3. `03_verify_index.py` — Verifies document count, text search, vector search, and facets

---

## Quick Start

```bash
# Activate the project venv
source /path/to/Industry-Solutions-Directory-PRO-Code/.venv/bin/activate

# Navigate to this directory
cd data-ingestion/sql-to-search

# Step 1: Create the index (idempotent — uses create_or_update)
python 01_create_index.py

# Step 2: Ingest solutions (reads SQL, generates embeddings, uploads)
python 02_ingest_from_sql.py

# Step 3: Verify everything works
python 03_verify_index.py
```

---

## Azure Resources

### SQL Database

| Property           | Value                                      |
|--------------------|--------------------------------------------|
| **Server**         | `mssoldir-prd-sql.database.windows.net`    |
| **Database**       | `mssoldir-prd`                             |
| **User**           | `isdapi` (read-only)                       |
| **View**           | `dbo.vw_ISDSolution_All`                   |
| **Raw rows**       | 4,934 (denormalized, as of Feb 2026)       |
| **Unique solutions** | 448 (after deduplication)                |
| **Unique partners**  | ~174                                     |

### Azure OpenAI

| Property           | Value                                      |
|--------------------|--------------------------------------------|
| **Resource**       | `r2d2-foundry-001`                         |
| **Endpoint**       | `https://r2d2-foundry-001.openai.azure.com/` |
| **Embedding model**| `text-embedding-3-large` (3,072 dimensions)|
| **Chat model**     | `gpt-4.1`                                 |
| **API version**    | `2025-04-01-preview`                       |

**Why `text-embedding-3-large`?**  
Both `text-embedding-3-large` and `text-embedding-3-small` are deployed on this resource. We chose `large` because it produces higher-quality embeddings (3,072 vs 1,536 dimensions) which means better search relevance. With only ~448 solutions, the cost difference is negligible.

### Azure AI Search

| Property           | Value                                      |
|--------------------|--------------------------------------------|
| **Service**        | `aq-mysearch001`                           |
| **Endpoint**       | `https://aq-mysearch001.search.windows.net`|
| **Index name**     | `isd-solutions-v1`                         |
| **Auth**           | `DefaultAzureCredential` (az login)        |
| **Document count** | 449 (448 solutions + 1 test doc)           |

> **Note**: The old search service `indsolse-dev-srch-okumlm.search.windows.net` was deleted. DNS resolution fails for it. All references to it in older config files are stale.

---

## SQL Database Schema

### View: `dbo.vw_ISDSolution_All`

This is a **denormalized view** — each solution can appear 10–20+ times because it joins across multiple dimensions (industries, solution areas, geos, resources). Always use `SELECT DISTINCT` or deduplicate in code.

| Column                   | Type         | Description                                      |
|--------------------------|--------------|--------------------------------------------------|
| `SolutionType`           | varchar      | Type of solution (e.g., "Industry")              |
| `solutionName`           | varchar      | Solution name                                    |
| `solutionDescription`    | varchar      | HTML-formatted solution description              |
| `solutionOrgWebsite`     | nvarchar     | Partner's website URL                            |
| `marketPlaceLink`        | varchar      | Azure Marketplace link                           |
| `specialOfferLink`       | varchar      | Special offer URL (if available)                 |
| `logoFileLink`           | varchar      | Solution logo URL                                |
| `industryName`           | varchar      | Industry (e.g., "Healthcare & Life Sciences")    |
| `industryDescription`    | varchar      | HTML-formatted industry description              |
| `subIndustryName`        | varchar      | Sub-industry category                            |
| `SubIndustryDescription` | varchar      | Sub-industry description                         |
| `theme`                  | varchar      | Industry theme/focus area                        |
| `industryThemeDesc`      | varchar      | Theme description                                |
| `solutionAreaName`       | varchar      | "AI Business Solutions", "Cloud and AI Platforms", or "Security" |
| `solAreaDescription`     | varchar      | Solution area description                        |
| `areaSolutionDescription`| varchar      | Additional area description                      |
| `solutionPlayName`       | varchar      | Solution play name (may be NULL)                 |
| `solutionPlayDesc`       | varchar      | Solution play description                        |
| `solutionPlayLabel`      | varchar      | Solution play label                              |
| `orgName`                | varchar      | Partner/organization name                        |
| `orgDescription`         | varchar      | Partner description                              |
| `userType`               | varchar      | Usually "Partner"                                |
| `solutionStatus`         | nvarchar     | Status (e.g., "Approved")                        |
| `displayLabel`           | nvarchar     | Display label for status                         |
| `geoName`                | varchar      | Geographic region (e.g., "United States")        |
| `resourceLinkTitle`      | varchar      | Resource link title                              |
| `resourceLinkUrl`        | varchar      | Resource URL                                     |
| `resourceLinkName`       | varchar      | Resource name/type (e.g., "Blog")                |
| `resourceLinkDescription`| varchar      | Resource description                             |
| `image_thumb`            | varchar      | Thumbnail image URL                              |
| `image_main`             | varchar      | Main image URL                                   |
| `image_mobile`           | varchar      | Mobile-optimized image URL                       |

### Key Data Distributions (as of Feb 2026)

**By Industry** (448 unique solutions):
| Industry                       | Solutions |
|--------------------------------|-----------|
| Financial Services             | 85        |
| Healthcare & Life Sciences     | 74        |
| Manufacturing & Mobility       | 62        |
| (No industry set)              | 59        |
| Retail & Consumer Goods        | 57        |
| Education                      | 46        |
| Energy & Resources             | 38        |
| Government                     | 24        |
| Defense Industrial Base        | 2         |

**By Solution Area**:
| Solution Area              | Solutions |
|----------------------------|-----------|
| Cloud and AI Platforms     | 253       |
| AI Business Solutions      | 145       |
| Security                   | 50        |

---

## Search Index Schema

### Index: `isd-solutions-v1`

| Field                  | Type                          | Searchable | Filterable | Facetable | Sortable | Key |
|------------------------|-------------------------------|:----------:|:----------:|:---------:|:--------:|:---:|
| `id`                   | `Edm.String`                  |            |            |           |          | Yes |
| `solution_name`        | `Edm.String`                  | Yes        | Yes        |           | Yes      |     |
| `solution_description` | `Edm.String`                  | Yes        |            |           |          |     |
| `partner_name`         | `Edm.String`                  | Yes        | Yes        | Yes       | Yes      |     |
| `partner_description`  | `Edm.String`                  | Yes        |            |           |          |     |
| `industry`             | `Edm.String`                  | Yes        | Yes        | Yes       |          |     |
| `industries`           | `Collection(Edm.String)`      | Yes        | Yes        | Yes       |          |     |
| `sub_industry`         | `Edm.String`                  | Yes        | Yes        | Yes       |          |     |
| `solution_area`        | `Edm.String`                  | Yes        | Yes        | Yes       |          |     |
| `solution_areas`       | `Collection(Edm.String)`      | Yes        | Yes        | Yes       |          |     |
| `theme`                | `Edm.String`                  | Yes        | Yes        | Yes       |          |     |
| `marketplace_link`     | `Edm.String`                  |            |            |           |          |     |
| `partner_website`      | `Edm.String`                  |            |            |           |          |     |
| `logo_url`             | `Edm.String`                  |            |            |           |          |     |
| `geos`                 | `Collection(Edm.String)`      | Yes        | Yes        | Yes       |          |     |
| `solution_status`      | `Edm.String`                  |            | Yes        |           |          |     |
| `content`              | `Edm.String`                  | Yes        |            |           |          |     |
| `content_vector`       | `Collection(Edm.Single)`      |            |            |           |          |     |

### Vector Search Configuration

| Setting              | Value                              |
|----------------------|------------------------------------|
| **Profile**          | `vector-profile`                   |
| **Algorithm**        | HNSW (`hnsw-config`)               |
| **HNSW m**           | 4                                  |
| **HNSW efConstruction** | 400                            |
| **HNSW efSearch**    | 500                                |
| **Metric**           | Cosine                             |
| **Vectorizer**       | `openai-vectorizer` (Azure OpenAI) |
| **Dimensions**       | 3,072                              |
| **Model**            | `text-embedding-3-large`           |

The integrated vectorizer means **queries are automatically vectorized** at search time — no need to generate embeddings client-side for vector queries. Use `VectorizableTextQuery` in the SDK.

### Document ID Generation

Document IDs are deterministic SHA-256 hashes of the solution name (first 32 hex chars). This means re-running the pipeline is idempotent — same solutions get the same IDs and are upserted.

### Content Field (used for embedding)

The `content` field is a concatenation of key fields used to generate the embedding vector:

```
Solution: {solution_name}
Partner: {partner_name}
Description: {solution_description}
Industries: {industry1, industry2, ...}
Solution Areas: {area1, area2, ...}
Themes: {theme1, theme2, ...}
Geographies: {geo1, geo2, ...}
About partner: {partner_description}
```

---

## Deduplication Logic

The SQL view `vw_ISDSolution_All` is heavily denormalized — 4,934 rows for 448 unique solutions. The ingestion script deduplicates by `solutionName`:

- **Single-valued fields** (description, partner name, links): taken from the first row encountered
- **Multi-valued fields** (industries, solution areas, geos, themes, sub-industries): collected into sets, then sorted and stored as arrays in `Collection(Edm.String)` fields
- The primary single value (e.g., `industry`) is set to the first item alphabetically from the collected set

---

## Troubleshooting

### "StartArray" upload error
If you see `An unexpected 'StartArray' node was found when reading from the JSON reader`, it means the index schema has `Edm.String` where it should have `Collection(Edm.String)` for array fields. Delete the index and recreate it:

```python
from azure.search.documents.indexes import SearchIndexClient
from azure.identity import DefaultAzureCredential
client = SearchIndexClient('https://aq-mysearch001.search.windows.net', DefaultAzureCredential())
client.delete_index('isd-solutions-v1')
```

Then re-run `01_create_index.py`. **Key lesson**: Use `SearchField(..., searchable=True)` instead of `SearchableField(...)` for `Collection(Edm.String)` fields — the SDK's `SearchableField` helper doesn't properly handle collection types.

### Authentication
The pipeline uses `DefaultAzureCredential` for Azure AI Search (requires `az login`). For Azure OpenAI and SQL DB, credentials are in `config.py` (loaded from env vars with hardcoded fallbacks).

### Re-running the pipeline
The pipeline is **idempotent** — re-running it will upsert all documents. No need to delete the index first unless the schema changes.

---

## Files

| File                   | Purpose                                                    |
|------------------------|------------------------------------------------------------|
| `config.py`            | All configuration (search, OpenAI, SQL, batch sizes)       |
| `01_create_index.py`   | Creates/updates the search index schema                    |
| `02_ingest_from_sql.py`| Full pipeline: SQL read → dedupe → embeddings → upload     |
| `03_verify_index.py`   | Verification: counts, samples, text search, vector search  |
| `test_upload.py`       | Debug script for testing single-document uploads           |

---

## Last Successful Run

```
Date:        February 16, 2026
SQL rows:    4,934 fetched from dbo.vw_ISDSolution_All
Solutions:   448 unique (after deduplication)
Embeddings:  448 generated (text-embedding-3-large, 3072d)
Uploaded:    448 succeeded, 0 failed
Duration:    81.2 seconds
Index docs:  449 (includes 1 test document)
```
