#!/usr/bin/env python3
"""
Create an MCS-compatible Azure AI Search index with integrated vectorization.
This index can be used by both pro-code (your FastAPI) and low-code (Microsoft Copilot Studio).
"""

import os
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    VectorSearchProfile,
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters,
    HnswAlgorithmConfiguration,
)
from azure.identity import DefaultAzureCredential

# Configuration
SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "https://indsolse-dev-srch-okumlm.search.windows.net")
OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://indsolse-dev-ai-okumlm.openai.azure.com/")
EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
NEW_INDEX_NAME = "partner-solutions-index-mcs"  # New MCS-compatible index

def create_mcs_compatible_index():
    """Create an index with integrated vectorization for MCS compatibility."""
    
    credential = DefaultAzureCredential()
    index_client = SearchIndexClient(endpoint=SEARCH_ENDPOINT, credential=credential)
    
    # Define fields (matching your existing index schema)
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="solution_name", type=SearchFieldDataType.String, sortable=True, filterable=True),
        SearchableField(name="partner_name", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SearchableField(name="description", type=SearchFieldDataType.String),
        SearchableField(
            name="industries", 
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True, 
            facetable=True
        ),
        SearchableField(
            name="technologies", 
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True, 
            facetable=True
        ),
        SimpleField(name="solution_url", type=SearchFieldDataType.String),
        SearchableField(name="chunk_text", type=SearchFieldDataType.String),  # Combined text for vectorization
        SearchableField(name="metadata", type=SearchFieldDataType.String),
        
        # Vector field with integrated vectorization
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            vector_search_dimensions=3072,  # text-embedding-3-large dimensions
            vector_search_profile_name="mcs-vector-profile",
        ),
    ]
    
    # Configure integrated vectorization
    vector_search = VectorSearch(
        profiles=[
            VectorSearchProfile(
                name="mcs-vector-profile",
                algorithm_configuration_name="hnsw-config",
                vectorizer_name="openai-vectorizer",
            )
        ],
        algorithms=[
            HnswAlgorithmConfiguration(
                name="hnsw-config",
                parameters={
                    "m": 4,
                    "efConstruction": 400,
                    "efSearch": 500,
                    "metric": "cosine"
                }
            )
        ],
        vectorizers=[
            AzureOpenAIVectorizer(
                vectorizer_name="openai-vectorizer",
                parameters=AzureOpenAIVectorizerParameters(
                    resource_url=OPENAI_ENDPOINT,
                    deployment_name=EMBEDDING_DEPLOYMENT,
                    model_name="text-embedding-3-large",
                    auth_identity=None,  # Uses managed identity
                )
            )
        ]
    )
    
    # Create the index
    index = SearchIndex(
        name=NEW_INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
    )
    
    print(f"Creating MCS-compatible index: {NEW_INDEX_NAME}")
    result = index_client.create_or_update_index(index)
    print(f"✅ Index created successfully!")
    print(f"   Index name: {result.name}")
    print(f"   Vector profile: mcs-vector-profile")
    print(f"   Vectorizer: Azure OpenAI (integrated)")
    print()
    print("🎯 This index is now compatible with Microsoft Copilot Studio!")
    print(f"   Your colleague can select: {NEW_INDEX_NAME}")
    print()
    print("📝 Next steps:")
    print("   1. Copy data from your existing index to this new one")
    print("   2. Or re-run ingestion pointing to this new index")
    print("   3. Update your backend config to use both indexes (or just the new one)")
    
    return result


if __name__ == "__main__":
    create_mcs_compatible_index()
