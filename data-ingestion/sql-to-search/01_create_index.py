#!/usr/bin/env python3
"""
Step 1: Create Azure AI Search index on aq-mysearch001.

Creates an index with:
- Searchable text fields for solution metadata
- Filterable / facetable fields for structured queries
- A 3072-dim vector field with HNSW + integrated OpenAI vectorizer
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

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
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential


def get_credential():
    if config.SEARCH_API_KEY:
        return AzureKeyCredential(config.SEARCH_API_KEY)
    return DefaultAzureCredential()


def create_index():
    print("=" * 60)
    print("Creating Azure AI Search Index")
    print("=" * 60)
    print(f"  Endpoint : {config.SEARCH_ENDPOINT}")
    print(f"  Index    : {config.INDEX_NAME}")
    print(f"  Embedding: {config.EMBEDDING_MODEL} ({config.EMBEDDING_DIMENSIONS}d)")

    credential = get_credential()
    client = SearchIndexClient(endpoint=config.SEARCH_ENDPOINT, credential=credential)

    fields = [
        # Key
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),

        # Core solution fields
        SearchableField(name="solution_name", type=SearchFieldDataType.String,
                        sortable=True, filterable=True),
        SearchableField(name="solution_description", type=SearchFieldDataType.String),
        SearchableField(name="partner_name", type=SearchFieldDataType.String,
                        filterable=True, facetable=True, sortable=True),
        SearchableField(name="partner_description", type=SearchFieldDataType.String),

        # Classification
        SearchableField(name="industry", type=SearchFieldDataType.String,
                        filterable=True, facetable=True),
        SearchField(
            name="industries",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            searchable=True, filterable=True, facetable=True,
        ),
        SearchableField(name="sub_industry", type=SearchFieldDataType.String,
                        filterable=True, facetable=True),
        SearchableField(name="solution_area", type=SearchFieldDataType.String,
                        filterable=True, facetable=True),
        SearchField(
            name="solution_areas",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            searchable=True, filterable=True, facetable=True,
        ),
        SearchableField(name="theme", type=SearchFieldDataType.String,
                        filterable=True, facetable=True),

        # Links
        SimpleField(name="marketplace_link", type=SearchFieldDataType.String),
        SimpleField(name="partner_website", type=SearchFieldDataType.String),
        SimpleField(name="logo_url", type=SearchFieldDataType.String),

        # Geo
        SearchField(
            name="geos",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            searchable=True, filterable=True, facetable=True,
        ),

        # Status
        SimpleField(name="solution_status", type=SearchFieldDataType.String,
                     filterable=True),

        # Combined text used to generate the embedding
        SearchableField(name="content", type=SearchFieldDataType.String),

        # Vector
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            vector_search_dimensions=config.EMBEDDING_DIMENSIONS,
            vector_search_profile_name="vector-profile",
        ),
    ]

    vector_search = VectorSearch(
        profiles=[
            VectorSearchProfile(
                name="vector-profile",
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
                    "metric": "cosine",
                },
            )
        ],
        vectorizers=[
            AzureOpenAIVectorizer(
                vectorizer_name="openai-vectorizer",
                parameters=AzureOpenAIVectorizerParameters(
                    resource_url=config.OPENAI_ENDPOINT.rstrip("/"),
                    deployment_name=config.EMBEDDING_DEPLOYMENT,
                    model_name=config.EMBEDDING_MODEL,
                    api_key=config.OPENAI_API_KEY,
                ),
            )
        ],
    )

    index = SearchIndex(
        name=config.INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
    )

    result = client.create_or_update_index(index)
    print(f"\n  Index '{result.name}' created/updated successfully.")
    print(f"  Fields: {len(result.fields)}")
    return result


if __name__ == "__main__":
    create_index()
