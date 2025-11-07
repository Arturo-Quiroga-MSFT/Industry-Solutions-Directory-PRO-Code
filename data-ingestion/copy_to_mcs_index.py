#!/usr/bin/env python3
"""
Copy data from the existing index to the new MCS-compatible index.
Note: The new index will auto-vectorize on upload, so we don't include vectors in the source.
"""

import os
from azure.search.documents import SearchClient
from azure.identity import DefaultAzureCredential
from tqdm import tqdm

# Configuration
SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "https://indsolse-dev-srch-okumlm.search.windows.net")
SOURCE_INDEX = "partner-solutions-index"
TARGET_INDEX = "partner-solutions-index-mcs"

def copy_documents():
    """Copy documents from source to target index."""
    
    credential = DefaultAzureCredential()
    
    # Source and target clients
    source_client = SearchClient(endpoint=SEARCH_ENDPOINT, index_name=SOURCE_INDEX, credential=credential)
    target_client = SearchClient(endpoint=SEARCH_ENDPOINT, index_name=TARGET_INDEX, credential=credential)
    
    print(f"📥 Fetching documents from: {SOURCE_INDEX}")
    
    # Fetch all documents (without vectors to save bandwidth)
    results = source_client.search(
        search_text="*",
        select=["id", "solution_name", "partner_name", "description", "industries", 
                "technologies", "solution_url", "chunk_text", "metadata"],
        top=10000,  # Adjust if you have more documents
    )
    
    documents = []
    for result in tqdm(results, desc="Reading documents"):
        # Filter out @search.* fields and content_vector (will be auto-generated)
        doc = {}
        for key, value in result.items():
            if not key.startswith('@') and key != 'content_vector':  # Skip internal fields and existing vectors
                if key in ["industries", "technologies"]:
                    # Ensure arrays are properly formatted
                    doc[key] = value if isinstance(value, list) else []
                else:
                    doc[key] = value
        documents.append(doc)
    
    print(f"✅ Found {len(documents)} documents")
    
    if not documents:
        print("❌ No documents to copy!")
        return
    
    print(f"📤 Uploading to: {TARGET_INDEX}")
    print("   (Integrated vectorization will auto-generate embeddings)")
    
    # Debug: Print first document structure
    if documents:
        print("\n🔍 First document structure:")
        for key, value in documents[0].items():
            val_str = str(value)[:50] if not isinstance(value, list) else f"list({len(value)} items)"
            print(f"  {key}: {type(value).__name__} = {val_str}")
        print()
    
    # Upload in batches
    batch_size = 100
    for i in tqdm(range(0, len(documents), batch_size), desc="Uploading batches"):
        batch = documents[i:i + batch_size]
        result = target_client.upload_documents(documents=batch)
        # Check for errors
        for item in result:
            if not item.succeeded:
                print(f"❌ Failed to upload document {item.key}: {item.error_message}")
                print(f"   Document data: {batch[[d['id'] for d in batch].index(item.key)]}")
    
    print(f"✅ Successfully copied {len(documents)} documents to {TARGET_INDEX}")
    print()
    print("🎯 The new index is ready for Microsoft Copilot Studio!")
    print(f"   Index name: {TARGET_INDEX}")
    print()
    print("⚠️  Note: Vectorization happens asynchronously.")
    print("   Wait a few minutes before querying for vectors to be generated.")


if __name__ == "__main__":
    copy_documents()
