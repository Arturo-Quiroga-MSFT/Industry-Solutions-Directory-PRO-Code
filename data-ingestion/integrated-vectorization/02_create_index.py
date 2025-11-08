#!/usr/bin/env python3
"""
Step 2: Create Azure AI Search index with integrated vectorizer.

This creates an index configured for integrated vectorization with:
- Vector fields with vectorizer configuration
- Same schema as manual approach for compatibility
- Query-time vectorization support
"""

import sys
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

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def create_index():
    """Create search index with integrated vectorizer."""
    print("="*60)
    print("Creating Azure AI Search Index with Integrated Vectorizer")
    print("="*60)
    print(f"\nIndex Name: {config.INDEX_NAME}")
    print(f"Search Endpoint: {config.SEARCH_ENDPOINT}")
    
    credential = DefaultAzureCredential()
    index_client = SearchIndexClient(endpoint=config.SEARCH_ENDPOINT, credential=credential)
    
    # Define fields
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
        SearchableField(name="industry", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="theme", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SearchableField(name="chunk_text", type=SearchFieldDataType.String),  # Created by Text Split skill
        
        # Vector field with integrated vectorizer
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            vector_search_dimensions=config.EMBEDDING_DIMENSIONS,
            vector_search_profile_name="integrated-vector-profile",
        ),
    ]
    
    # Configure integrated vectorization
    vector_search = VectorSearch(
        profiles=[
            VectorSearchProfile(
                name="integrated-vector-profile",
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
                    resource_url=config.OPENAI_ENDPOINT,
                    deployment_name=config.EMBEDDING_DEPLOYMENT,
                    model_name=config.EMBEDDING_MODEL,
                    auth_identity=None,  # Uses managed identity
                )
            )
        ]
    )
    
    # Create the index
    index = SearchIndex(
        name=config.INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
    )
    
    print("\n📝 Creating index...")
    result = index_client.create_or_update_index(index)
    
    print(f"✅ Index created successfully!")
    print(f"   Name: {result.name}")
    print(f"   Vector Profile: integrated-vector-profile")
    print(f"   Vectorizer: openai-vectorizer (Azure OpenAI)")
    print(f"   Embedding Model: {config.EMBEDDING_MODEL}")
    print(f"   Dimensions: {config.EMBEDDING_DIMENSIONS}")
    
    print("\n🎯 Key Features:")
    print("   ✅ Compatible with Microsoft Copilot Studio")
    print("   ✅ Automatic query vectorization")
    print("   ✅ Same schema as manual approach")
    print("   ✅ Ready for indexer-based ingestion")
    
    print("\nNext Step:")
    print("  Run 03_create_skillset.py to create the chunking and embedding skillset")
    
    return result


if __name__ == "__main__":
    create_index()
