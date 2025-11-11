#!/usr/bin/env python3
"""
Step 2: Create Azure AI Search index with integrated vectorizer AND semantic configuration.

This creates an MCS-compatible index configured with:
- Integrated vectorization for automatic embedding generation
- Semantic configuration for L2 semantic reranking
- Full Microsoft Copilot Studio compatibility
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
    SemanticConfiguration,
    SemanticSearch,
    SemanticPrioritizedFields,
    SemanticField,
)
from azure.identity import DefaultAzureCredential

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def create_index():
    """Create search index with integrated vectorizer AND semantic configuration."""
    print("="*70)
    print("Creating Azure AI Search Index with Integrated Vectorizer + Semantic")
    print("="*70)
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
    
    # Configure semantic search (required for MCS)
    semantic_config = SemanticConfiguration(
        name="default",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="solution_name"),
            content_fields=[
                SemanticField(field_name="description"),
                SemanticField(field_name="chunk_text"),
                SemanticField(field_name="content"),
            ],
            keywords_fields=[
                SemanticField(field_name="partner_name"),
                SemanticField(field_name="industry"),
                SemanticField(field_name="theme"),
            ]
        )
    )
    
    semantic_search = SemanticSearch(
        configurations=[semantic_config],
        default_configuration_name="default"
    )
    
    # Create the index with both vector and semantic search
    index = SearchIndex(
        name=config.INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search,
    )
    
    print("\n📝 Creating index...")
    result = index_client.create_or_update_index(index)
    
    print(f"✅ Index created successfully!")
    print(f"   Name: {result.name}")
    print(f"\n🔍 Vector Search Configuration:")
    print(f"   Profile: integrated-vector-profile")
    print(f"   Vectorizer: openai-vectorizer (Azure OpenAI)")
    print(f"   Embedding Model: {config.EMBEDDING_MODEL}")
    print(f"   Dimensions: {config.EMBEDDING_DIMENSIONS}")
    
    print(f"\n🧠 Semantic Search Configuration:")
    print(f"   Configuration Name: default")
    print(f"   Title Field: solution_name")
    print(f"   Content Fields: description, chunk_text, content")
    print(f"   Keywords Fields: partner_name, industry, theme")
    
    print("\n🎯 Key Features:")
    print("   ✅ Microsoft Copilot Studio compatible (integrated vectorization)")
    print("   ✅ Semantic ranking enabled (L2 reranking)")
    print("   ✅ Automatic query vectorization")
    print("   ✅ Hybrid search (vector + keyword + semantic)")
    print("   ✅ Ready for indexer-based ingestion")
    
    print("\n💡 Benefits:")
    print("   • Better relevance with semantic L2 reranking")
    print("   • Captions and answers extraction")
    print("   • Full MCS Generative Answers support")
    print("   • Pro-code and low-code solutions can share same index")
    
    print("\nNext Step:")
    print("  Run 03_create_skillset.py to create the chunking and embedding skillset")
    
    return result


if __name__ == "__main__":
    create_index()
