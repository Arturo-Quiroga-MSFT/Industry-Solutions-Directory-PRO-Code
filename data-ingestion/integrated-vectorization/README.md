# Integrated Vectorization Approach

This directory contains an experimental implementation using Azure AI Search's **Integrated Vectorization** feature, which uses indexers and skillsets instead of manual embedding calls.

## Key Differences from Current Manual Approach

### Current Manual Vectorization (`../ingest_data.py`)
```
Python Script → Fetch Data from API → Call Azure OpenAI Embedding → Push Vectors to Index
```

**Pros:**
- Full control over data transformation
- Direct API-to-Index pipeline
- No intermediate storage needed

**Cons:**
- Manual embedding API calls (quota management)
- Custom retry logic required
- Script must handle chunking
- One-time batch process

### New Integrated Vectorization (This Directory)
```
Data Source (Blob/Cosmos) → Indexer → Skillset (Chunk + Vectorize) → Index
```

**Pros:**
- Automatic vectorization (no manual embedding calls)
- Built-in retry and throttling handling
- Scheduled incremental updates
- Works with Microsoft Copilot Studio out-of-the-box
- Projections for secondary indexes (parent-child relationships)

**Cons:**
- Requires data in supported data sources (Blob, Cosmos, SQL, etc.)
- Less control over transformation logic
- More complex setup (indexer + skillset + data source)

## Architecture Components

1. **Data Source**: Azure Blob Storage containing JSON files from ISD API
2. **Indexer**: Pulls data from Blob Storage and drives the pipeline
3. **Skillset**:
   - Text Split Skill: Chunks large documents
   - Azure OpenAI Embedding Skill: Generates vectors from chunks
4. **Index**: Same schema as current, but with integrated vectorizer for queries
5. **Vectorizer**: Azure OpenAI vectorizer for query-time text-to-vector conversion

## Files in This Directory

- `README.md` - This file
- `01_export_to_blob.py` - Export ISD data to Azure Blob Storage
- `02_create_index.py` - Create search index with vectorizer configuration
- `03_create_skillset.py` - Create skillset with chunking and embedding
- `04_create_indexer.py` - Create indexer to orchestrate the pipeline
- `05_test_query.py` - Test queries with automatic vectorization
- `config.py` - Configuration for all components
- `comparison.md` - Detailed comparison with manual approach

## Prerequisites

```bash
# Azure resources needed
- Azure Blob Storage account
- Azure AI Search service
- Azure OpenAI service with text-embedding-3-large deployment

# Environment variables
export AZURE_STORAGE_CONNECTION_STRING="..."
export AZURE_SEARCH_ENDPOINT="https://indsolse-dev-srch-okumlm.search.windows.net"
export AZURE_OPENAI_ENDPOINT="https://indsolse-dev-ai-okumlm.openai.azure.com/"
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-3-large"
```

## Quick Start

```bash
cd integrated-vectorization

# 1. Export ISD data to Blob Storage
python 01_export_to_blob.py

# 2. Create the search index with vectorizer
python 02_create_index.py

# 3. Create the skillset (chunking + embedding)
python 03_create_skillset.py

# 4. Create the indexer and run it
python 04_create_indexer.py

# 5. Test queries (automatic vectorization!)
python 05_test_query.py "Show me healthcare AI solutions"
```

## Benefits for This Use Case

1. **MCS Compatibility**: Works natively with Microsoft Copilot Studio
2. **Incremental Updates**: Indexer can run on schedule to pick up new solutions
3. **No Quota Management**: Azure handles throttling and retries automatically
4. **Chunking Built-in**: Text Split skill handles document chunking
5. **Query Simplification**: Text queries auto-vectorize without code

## When to Use Which Approach?

### Use Manual Vectorization (Current) When:
- You need full control over data transformation
- Your data source is an API (not Blob/Cosmos/SQL)
- You want simpler architecture (no indexers)
- You do one-time batch ingestion

### Use Integrated Vectorization (This) When:
- You need MCS/Copilot Studio compatibility
- You want scheduled incremental updates
- Your data can be staged in Blob/Cosmos/SQL
- You want Azure to handle retry/throttling
- You need secondary indexes (parent-child pattern)

## Cost Comparison

**Manual Vectorization:**
- Pay for embedding API calls per ingestion run
- Pay for your compute to run the script

**Integrated Vectorization:**
- Pay for Blob Storage (~$0.02/GB/month)
- Pay for same embedding API calls (Azure does it for you)
- Pay for indexer execution (included in search tier)

Net difference: ~$1-2/month for blob storage. Otherwise similar.

## Next Steps

1. Run the setup scripts to test integrated vectorization
2. Compare query results with manual approach
3. Test MCS compatibility
4. Decide which approach to use going forward
5. Potentially use both: Manual for initial load, Integrated for updates
