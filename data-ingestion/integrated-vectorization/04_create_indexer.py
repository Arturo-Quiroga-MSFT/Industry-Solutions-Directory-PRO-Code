#!/usr/bin/env python3
"""
Step 4: Create data source and indexer to orchestrate the pipeline.

The indexer:
1. Connects to Blob Storage (data source)
2. Runs the skillset (chunking + embedding)
3. Populates the index
"""

import sys
import os
from azure.search.documents.indexes import SearchIndexerClient
from azure.search.documents.indexes.models import (
    SearchIndexerDataContainer,
    SearchIndexerDataSourceConnection,
    SearchIndexer,
    FieldMapping,
    FieldMappingFunction,
    OutputFieldMappingEntry,
    IndexingParameters,
    IndexingSchedule,
)
from azure.identity import DefaultAzureCredential
from datetime import timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    SEARCH_ENDPOINT, DATA_SOURCE_NAME, STORAGE_ACCOUNT_URL,
    STORAGE_CONTAINER_NAME, INDEX_NAME, SKILLSET_NAME, INDEXER_NAME
)


def create_data_source():
    """Create blob storage data source connection."""
    print("\n📁 Creating data source connection...")
    
    credential = DefaultAzureCredential()
    indexer_client = SearchIndexerClient(endpoint=SEARCH_ENDPOINT, credential=credential)
    
    # Create data source connection (uses managed identity)
    # For Azure Search indexers, we need to use ResourceId format for managed identity
    storage_resource_id = f"/subscriptions/7a28b21e-0d3e-4435-a686-d92889d4ee96/resourceGroups/AI-FOUNDRY-RG/providers/Microsoft.Storage/storageAccounts/aqstorage009876"
    connection_string = f"ResourceId={storage_resource_id};"
    
    container = SearchIndexerDataContainer(name=STORAGE_CONTAINER_NAME)
    data_source = SearchIndexerDataSourceConnection(
        name=DATA_SOURCE_NAME,
        type="azureblob",
        connection_string=connection_string,
        container=container,
        description="Industry Solutions Directory data from blob storage",
        data_change_detection_policy=None,
        data_deletion_detection_policy=None
    )
    
    result = indexer_client.create_or_update_data_source_connection(data_source)
    print(f"✅ Data source created: {result.name}")
    print(f"   Type: Azure Blob Storage")
    print(f"   Container: {STORAGE_CONTAINER_NAME}")
    
    return result


def create_indexer():
    """Create indexer to orchestrate the pipeline."""
    print("\n🔄 Creating indexer...")
    
    credential = DefaultAzureCredential()
    indexer_client = SearchIndexerClient(endpoint=SEARCH_ENDPOINT, credential=credential)
    
    # Field mappings from source to index
    # For blob storage, use base64-encoded storage path as the key to avoid invalid characters
    field_mappings = [
        FieldMapping(
            source_field_name="metadata_storage_path",
            target_field_name="id",
            mapping_function=FieldMappingFunction(name="base64Encode")
        ),
        FieldMapping(source_field_name="solution_name", target_field_name="solution_name"),
        FieldMapping(source_field_name="partner_name", target_field_name="partner_name"),
        FieldMapping(source_field_name="description", target_field_name="description"),
        FieldMapping(source_field_name="solution_url", target_field_name="solution_url"),
        FieldMapping(source_field_name="industry", target_field_name="industry"),
        FieldMapping(source_field_name="theme", target_field_name="theme"),
        FieldMapping(source_field_name="industries", target_field_name="industries"),
        FieldMapping(source_field_name="technologies", target_field_name="technologies"),
        FieldMapping(source_field_name="content", target_field_name="content"),
    ]
    
    # Output field mappings from skillset to index
    # Note: With integrated vectorization, vectors are populated automatically
    # The skillset outputs need to be mapped to the index fields
    output_field_mappings = []
    
    # Indexing parameters
    parameters = IndexingParameters(
        batch_size=10,  # Process 10 documents at a time
        max_failed_items=5,  # Allow some failures
        max_failed_items_per_batch=5,
        configuration={
            "parsingMode": "json"  # Parse blobs as JSON documents
        }
    )
    
    # Optional: Schedule indexer to run every 30 minutes
    schedule = IndexingSchedule(interval=timedelta(minutes=30))
    
    # Create indexer
    indexer = SearchIndexer(
        name=INDEXER_NAME,
        description="Indexer for Industry Solutions with integrated vectorization",
        data_source_name=DATA_SOURCE_NAME,
        target_index_name=INDEX_NAME,
        skillset_name=SKILLSET_NAME,
        field_mappings=field_mappings,
        output_field_mappings=output_field_mappings,
        parameters=parameters,
        schedule=schedule,  # Comment out if you don't want scheduled runs
    )
    
    result = indexer_client.create_or_update_indexer(indexer)
    print(f"✅ Indexer created: {result.name}")
    print(f"   Data Source: {DATA_SOURCE_NAME}")
    print(f"   Target Index: {INDEX_NAME}")
    print(f"   Skillset: {SKILLSET_NAME}")
    print(f"   Schedule: Every 30 minutes")
    
    return result


def run_indexer():
    """Run the indexer immediately."""
    print("\n▶️  Running indexer...")
    
    credential = DefaultAzureCredential()
    indexer_client = SearchIndexerClient(endpoint=SEARCH_ENDPOINT, credential=credential)
    
    indexer_client.run_indexer(INDEXER_NAME)
    print(f"✅ Indexer started: {INDEXER_NAME}")
    print("\n⏳ The indexer is now running in the background.")
    print("   This may take several minutes depending on data size.")
    print("\nMonitor progress:")
    print(f"  - Azure Portal → Azure AI Search → Indexers → {INDEXER_NAME}")
    print(f"  - Or run: az search indexer show --name {INDEXER_NAME}")


def main():
    """Main execution."""
    print("="*60)
    print("Creating Data Source and Indexer")
    print("="*60)
    
    # Step 1: Create data source
    create_data_source()
    
    # Step 2: Create indexer
    create_indexer()
    
    # Step 3: Run indexer immediately
    run_indexer()
    
    print("\n" + "="*60)
    print("✅ Setup Complete!")
    print("="*60)
    print("\nThe integrated vectorization pipeline is now active:")
    print("  1. ✅ Blob Storage contains source data")
    print("  2. ✅ Index is configured with vectorizer")
    print("  3. ✅ Skillset handles chunking and embedding")
    print("  4. ✅ Indexer orchestrates everything")
    print("  5. ⏳ Data is being indexed...")
    print("\nNext Steps:")
    print("  1. Wait 5-10 minutes for indexing to complete")
    print("  2. Run 05_test_query.py to test queries")
    print(f"  3. Use index '{INDEX_NAME}' in Microsoft Copilot Studio!")


if __name__ == "__main__":
    main()
