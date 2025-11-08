#!/usr/bin/env python3
"""Check a sample document to see the data types."""
import os
import json
from azure.search.documents import SearchClient
from azure.identity import DefaultAzureCredential

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "https://indsolse-dev-srch-okumlm.search.windows.net")
SOURCE_INDEX = "partner-solutions-index"

credential = DefaultAzureCredential()
source_client = SearchClient(endpoint=SEARCH_ENDPOINT, index_name=SOURCE_INDEX, credential=credential)

results = source_client.search(search_text="*", top=1)
for result in results:
    print("Sample document:")
    for key, value in result.items():
        print(f"  {key}: {type(value).__name__} = {repr(value)[:100]}")
    break
