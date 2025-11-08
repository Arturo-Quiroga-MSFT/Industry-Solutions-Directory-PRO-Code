#!/usr/bin/env python3
"""
Step 3: Create skillset for chunking and embedding.

The skillset contains:
1. Text Split skill - Chunks documents for embedding
2. Azure OpenAI Embedding skill - Generates vectors from chunks
"""

import sys
import os
from azure.search.documents.indexes import SearchIndexerClient
from azure.search.documents.indexes.models import (
    SearchIndexerSkillset,
    SplitSkill,
    AzureOpenAIEmbeddingSkill,
    InputFieldMappingEntry,
    OutputFieldMappingEntry,
)
from azure.identity import DefaultAzureCredential

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def create_skillset():
    """Create skillset with chunking and embedding skills."""
    print("="*60)
    print("Creating Skillset for Chunking and Embedding")
    print("="*60)
    print(f"\nSkillset Name: {config.SKILLSET_NAME}")
    
    credential = DefaultAzureCredential()
    indexer_client = SearchIndexerClient(endpoint=config.SEARCH_ENDPOINT, credential=credential)
    
    # Skill 1: Text Split (Chunking)
    text_split_skill = SplitSkill(
        name="text-splitter",
        description="Split content into chunks for embedding",
        context="/document",
        text_split_mode="pages",
        maximum_page_length=config.CHUNK_SIZE,
        page_overlap_length=config.CHUNK_OVERLAP,
        inputs=[
            InputFieldMappingEntry(name="text", source="/document/content")
        ],
        outputs=[
            OutputFieldMappingEntry(name="textItems", target_name="chunks")
        ]
    )
    
    # Skill 2: Azure OpenAI Embedding (using managed identity)
    embedding_skill = AzureOpenAIEmbeddingSkill(
        name="azure-openai-embedding",
        description="Generate embeddings using Azure OpenAI",
        context="/document/chunks/*",
        resource_url=config.OPENAI_ENDPOINT,
        deployment_name=config.EMBEDDING_DEPLOYMENT,
        model_name=config.EMBEDDING_MODEL,
        dimensions=config.EMBEDDING_DIMENSIONS,
        auth_identity=None,  # Uses system-assigned managed identity
        inputs=[
            InputFieldMappingEntry(name="text", source="/document/chunks/*")
        ],
        outputs=[
            OutputFieldMappingEntry(name="embedding", target_name="vector")
        ]
    )
    
    # Create the skillset
    skillset = SearchIndexerSkillset(
        name=config.SKILLSET_NAME,
        description="Skillset for chunking text and generating embeddings",
        skills=[text_split_skill, embedding_skill]
    )
    
    print("\n📝 Creating skillset...")
    result = indexer_client.create_or_update_skillset(skillset)
    
    print(f"✅ Skillset created successfully!")
    print(f"   Name: {result.name}")
    print(f"\n🔧 Skills:")
    print(f"   1. Text Split Skill")
    print(f"      - Chunk size: {config.CHUNK_SIZE} characters")
    print(f"      - Overlap: {config.CHUNK_OVERLAP} characters")
    print(f"   2. Azure OpenAI Embedding Skill")
    print(f"      - Model: {config.EMBEDDING_MODEL}")
    print(f"      - Dimensions: {config.EMBEDDING_DIMENSIONS}")
    
    print("\nNext Step:")
    print("  Run 04_create_indexer.py to create the indexer and start ingestion")
    
    return result


if __name__ == "__main__":
    create_skillset()
