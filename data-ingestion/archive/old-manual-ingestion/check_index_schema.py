#!/usr/bin/env python3
"""
Check the actual schema of the existing index.
"""

import os
from azure.search.documents.indexes import SearchIndexClient
from azure.identity import DefaultAzureCredential

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "https://indsolse-dev-srch-okumlm.search.windows.net")
SOURCE_INDEX = "partner-solutions-index"

credential = DefaultAzureCredential()
index_client = SearchIndexClient(endpoint=SEARCH_ENDPOINT, credential=credential)

index = index_client.get_index(SOURCE_INDEX)

print(f"Index: {index.name}")
print(f"\nFields:")
for field in index.fields:
    print(f"  - {field.name}: {field.type}")
