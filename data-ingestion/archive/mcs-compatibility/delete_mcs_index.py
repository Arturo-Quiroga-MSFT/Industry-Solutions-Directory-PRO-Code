#!/usr/bin/env python3
"""Delete the MCS index."""
import os
from azure.search.documents.indexes import SearchIndexClient
from azure.identity import DefaultAzureCredential

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "https://indsolse-dev-srch-okumlm.search.windows.net")
INDEX_NAME = "partner-solutions-index-mcs"

credential = DefaultAzureCredential()
index_client = SearchIndexClient(endpoint=SEARCH_ENDPOINT, credential=credential)

print(f"Deleting index: {INDEX_NAME}")
index_client.delete_index(INDEX_NAME)
print("✅ Index deleted")
