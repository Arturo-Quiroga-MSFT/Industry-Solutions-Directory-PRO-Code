#!/usr/bin/env python3
"""
Step 3: Verify the search index – counts, sample docs, test queries.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential


def get_credential():
    if config.SEARCH_API_KEY:
        return AzureKeyCredential(config.SEARCH_API_KEY)
    return DefaultAzureCredential()


def verify():
    print("=" * 60)
    print("Verify Search Index")
    print("=" * 60)
    print(f"  Endpoint: {config.SEARCH_ENDPOINT}")
    print(f"  Index   : {config.INDEX_NAME}\n")

    credential = get_credential()
    client = SearchClient(
        endpoint=config.SEARCH_ENDPOINT,
        index_name=config.INDEX_NAME,
        credential=credential,
    )

    # ── document count ──
    count = client.get_document_count()
    print(f"Document count: {count}\n")

    # ── sample documents ──
    print("─── Sample documents (first 5) ───")
    results = client.search(search_text="*", top=5, select="id,solution_name,partner_name,industry,solution_area")
    for doc in results:
        print(f"  {doc['solution_name']:50s}  |  {doc.get('partner_name','')}  |  {doc.get('industry','')}  |  {doc.get('solution_area','')}")

    # ── text search ──
    print("\n─── Text search: 'healthcare AI' ───")
    results = client.search(search_text="healthcare AI", top=5,
                            select="solution_name,partner_name,industry,solution_area")
    for doc in results:
        print(f"  {doc['solution_name']:50s}  |  {doc.get('partner_name','')}")

    # ── vector search ──
    print("\n─── Vector search: 'cybersecurity solutions for financial services' ───")
    vector_query = VectorizableTextQuery(
        text="cybersecurity solutions for financial services",
        k_nearest_neighbors=5,
        fields="content_vector",
    )
    results = client.search(
        search_text=None,
        vector_queries=[vector_query],
        top=5,
        select="solution_name,partner_name,industry,solution_area",
    )
    for doc in results:
        print(f"  {doc['solution_name']:50s}  |  {doc.get('partner_name','')}  |  {doc.get('industry','')}")

    # ── facets ──
    print("\n─── Industry facets ───")
    results = client.search(search_text="*", facets=["industry"], top=0)
    for facet in results.get_facets().get("industry", []):
        print(f"  {facet['value']:45s}  ({facet['count']})")

    print("\n─── Solution area facets ───")
    results = client.search(search_text="*", facets=["solution_area"], top=0)
    for facet in results.get_facets().get("solution_area", []):
        print(f"  {facet['value']:45s}  ({facet['count']})")

    print("\nVerification complete.")


if __name__ == "__main__":
    verify()
