#!/usr/bin/env python3
"""Check blob storage for solutions with empty content fields"""
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
import json

credential = DefaultAzureCredential()
blob_service_client = BlobServiceClient(
    account_url='https://aqstorage009876.blob.core.windows.net',
    credential=credential
)

container_client = blob_service_client.get_container_client('industry-solutions-data')

# Count blobs and check for empty content
total_blobs = 0
empty_content_list = []

print("Analyzing blob storage...")
for blob in container_client.list_blobs():
    total_blobs += 1
    blob_client = container_client.get_blob_client(blob.name)
    content = blob_client.download_blob().readall()
    doc = json.loads(content)
    
    content_field = doc.get('content', '').strip()
    if not content_field or len(content_field) == 0:
        empty_content_list.append({
            'blob_name': blob.name,
            'solution_id': doc.get('id'),
            'solution_name': doc.get('solution_name'),
            'partner_name': doc.get('partner_name'),
            'description_length': len(doc.get('description', ''))
        })

print(f"\nTotal blobs in storage: {total_blobs}")
print(f"Blobs with empty content field: {len(empty_content_list)}")

if empty_content_list:
    print("\nSolutions with empty content:")
    for i, sol in enumerate(empty_content_list[:10], 1):
        print(f"{i}. {sol['solution_name']} (ID: {sol['solution_id']})")
        print(f"   Partner: {sol['partner_name']}")
        print(f"   Description length: {sol['description_length']}")
        print(f"   Blob: {sol['blob_name']}")
        print()
