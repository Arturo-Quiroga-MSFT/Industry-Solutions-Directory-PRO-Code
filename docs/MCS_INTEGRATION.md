# Microsoft Copilot Studio (MCS) Integration Guide

## Problem

Microsoft Copilot Studio requires Azure AI Search indexes to use **integrated vectorization**. Your current index (`partner-solutions-index`) uses manual vectorization and is therefore unsupported by MCS.

## Solution

Create a parallel MCS-compatible index that both your pro-code solution (FastAPI) and your colleague's low-code solution (MCS) can use.

## Quick Start

### Step 1: Create MCS-Compatible Index

```bash
cd data-ingestion
python create_mcs_compatible_index.py
```

This creates a new index: `partner-solutions-index-mcs` with:
- ✅ Integrated vectorization (MCS compatible)
- ✅ Same schema as your existing index
- ✅ Azure OpenAI vectorizer configured
- ✅ Uses managed identity authentication

### Step 2: Copy Existing Data

```bash
python copy_to_mcs_index.py
```

This copies all documents from `partner-solutions-index` to `partner-solutions-index-mcs`. The integrated vectorizer will automatically generate embeddings.

⚠️ **Wait 5-10 minutes** after copying for vectorization to complete.

### Step 3: Tell Your Colleague

Your CSA colleague can now select `partner-solutions-index-mcs` in Microsoft Copilot Studio! ✅

## Architecture Comparison

### Your Pro-Code Approach (Current)
```
Python Script → Azure OpenAI (embed) → Push vectors → Azure AI Search
```
- ✅ Full control over vectorization
- ✅ Works great for FastAPI
- ❌ Not compatible with MCS

### MCS-Compatible Approach (New)
```
Upload documents → Azure AI Search → Auto-vectorize via integrated vectorizer
```
- ✅ Compatible with MCS
- ✅ Still works with FastAPI
- ✅ Simpler ingestion (no manual embedding calls)
- ⚠️ Slightly slower initial indexing

## Using the New Index in Your FastAPI Backend

Update your backend config to use the new index:

```python
# backend/app/config.py or .env
AZURE_SEARCH_INDEX_NAME=partner-solutions-index-mcs
```

Or support both indexes (fallback):

```python
# In search_service.py
PRIMARY_INDEX = "partner-solutions-index-mcs"  # MCS-compatible
FALLBACK_INDEX = "partner-solutions-index"      # Original
```

## Future Ingestion

**Current Status (v2.8):** You're already using **integrated vectorization** for both indexing and queries! ✅

Your production setup:
- Index: `partner-solutions-integrated` (integrated vectorization enabled)
- Ingestion: REST API approach (manual vectorization during bulk load)
- Queries: Automatic vectorization via `VectorizableTextQuery`

### Comparison: Manual vs Integrated Vectorization

| Aspect | Manual Vectorization | Integrated Vectorization (Current ✅) |
|--------|---------------------|-------------------------------------|
| **MCS Compatible** | ❌ No | ✅ Yes |
| **Query Code** | 15+ lines (manual embed call) | 5 lines (automatic) |
| **Ingestion Setup** | Simple (1 script) | Complex (indexer + skillset) |
| **Incremental Updates** | Re-run entire script | Automatic detection |
| **Maintenance** | Higher (manage retries, quotas) | Lower (Azure handles it) |
| **Data Source** | Any API/source | Blob, Cosmos, SQL required |
| **Cost** | $35/month | $36/month (~same) |
| **Performance** | Same latency | Same latency |

### For Ongoing Data Updates: Two Approaches

#### Option A: Hybrid (Recommended for ISD) ⭐
**What you're doing now!** Best of both worlds:

1. **Bulk Load**: Use manual approach (`ingest_data.py`)
   - Faster initial setup
   - Works directly with ISD API
   - Full control over transformations

2. **Incremental Updates**: Set up automated indexer
   - Export changed data to Blob Storage
   - Indexer auto-detects changes
   - Scheduled refresh (daily/weekly)

3. **Queries**: Use integrated vectorizer
   - Simpler code (already implemented)
   - Automatic query vectorization
   - MCS compatible

```python
# Current query approach (integrated vectorizer)
results = search_client.search(
    vector_queries=[VectorizableTextQuery(
        text=user_query,  # Automatic vectorization!
        k_nearest_neighbors=5
    )]
)
```

#### Option B: Fully Manual (Not Recommended)
Continue using only `ingest_data.py` for all updates:
- ❌ More code to maintain
- ❌ Manual scheduling required
- ❌ Must handle all retries/throttling
- ✅ Simpler architecture (fewer components)

**Why NOT recommended:** You lose MCS compatibility and query simplification benefits.

#### Option C: Fully Integrated (Future Option)
Completely automate the pipeline:

```python
# 1. Export ISD API data to Blob Storage (scheduled)
python export_to_blob.py  # Runs daily via Azure Function

# 2. Indexer automatically:
#    - Detects new/changed files
#    - Chunks documents
#    - Calls embedding API
#    - Updates index
```

**Pros:**
- Zero manual intervention after setup
- Automatic scheduled updates
- Built-in retry and monitoring
- MCS compatible

**Cons:**
- Requires Blob Storage setup
- More complex initial configuration
- Debugging harder (multiple components)

### Decision Matrix

**Stay with Hybrid if:**
- ✅ Updates are infrequent (weekly/monthly)
- ✅ You want maximum flexibility
- ✅ Current approach works well
- ✅ Prefer simpler troubleshooting

**Move to Fully Integrated if:**
- ✅ Need daily automatic updates
- ✅ Want zero-touch maintenance
- ✅ Have DevOps resources for setup
- ✅ Need enterprise-grade monitoring

### Recommended Path Forward

**For Industry Solutions Directory:** ✅ **Keep Hybrid Approach**

**Why:**
1. ISD API updates are infrequent (weekly/monthly)
2. Data source is REST API (not Blob/Cosmos)
3. Current manual bulk + integrated queries works well
4. Simpler to maintain and troubleshoot
5. Already MCS compatible via integrated vectorizer

**Action Items:**
1. ✅ Done: Using integrated vectorization for queries
2. ✅ Done: Index is MCS-compatible
3. 🔄 Optional: Set up blob export for automated incremental updates
4. 🔄 Optional: Schedule indexer to run weekly

**If you want automated updates later:**
```bash
# Add scheduled export to blob
cd data-ingestion/integrated-vectorization
python 01_export_to_blob.py  # Export latest from ISD API
python 04_create_indexer.py  # Set schedule: weekly
```

## Benefits of Integrated Vectorization

1. **MCS Compatibility** - Works with Microsoft Copilot Studio
2. **Simpler Code** - No need to call embedding API in your scripts
3. **Consistent** - Same vectorization across pro-code and low-code
4. **Scalable** - Azure handles vectorization infrastructure
5. **Cost Efficient** - Only vectorizes once, reuses for both solutions

## Testing the New Index

### From Azure Portal
1. Navigate to Azure AI Search → Indexes → `partner-solutions-index-mcs`
2. Click "Search explorer"
3. Run a vector search query

### From Your FastAPI
```bash
# Update config
export AZURE_SEARCH_INDEX_NAME=partner-solutions-index-mcs

# Restart backend
cd backend
uvicorn app.main:app --reload

# Test
curl http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me healthcare AI solutions"}'
```

### From Microsoft Copilot Studio
Your colleague can now:
1. Add "Search" capability
2. Select Azure AI Search
3. Choose `partner-solutions-index-mcs` ✅
4. MCS will recognize it as supported!

## Troubleshooting

### "Unsupported indexes" still showing?
- Refresh the MCS interface
- Verify the index was created with integrated vectorization
- Check that the vectorizer is configured in the index schema

### Vectors not generated?
- Wait 5-10 minutes after uploading documents
- Check Azure OpenAI deployment is accessible
- Verify managed identity has "Cognitive Services OpenAI User" role

### Query performance?
- Integrated vectorization has same query performance as manual
- Initial indexing is slightly slower (vectorization happens async)
- Consider keeping both indexes if needed

## Collaboration Strategy

**Your Pro-Code (FastAPI)**
- Can use either index
- Recommend: Switch to `partner-solutions-index-mcs` for consistency

**Your Colleague's Low-Code (MCS)**
- Must use `partner-solutions-index-mcs`
- Will automatically work once index is created

**Data Ingestion**
- One script → One index → Both solutions ✅
- No coordination needed after initial setup

## Cost Implications

- **Integrated Vectorization**: Free (included with Azure AI Search)
- **Storage**: Minimal increase (same documents, same vectors)
- **Compute**: Same embedding costs (just moved from your script to Azure)

Net effect: **No additional cost**, just better compatibility!

## Next Steps

1. ✅ Run `create_mcs_compatible_index.py`
2. ✅ Run `copy_to_mcs_index.py`
3. ✅ Tell your colleague the new index name
4. ✅ Update your backend config (optional)
5. ✅ Celebrate collaboration! 🎉

## References

- [Azure AI Search Integrated Vectorization](https://learn.microsoft.com/azure/search/vector-search-integrated-vectorization)
- [Microsoft Copilot Studio with Azure AI Search](https://learn.microsoft.com/microsoft-copilot-studio/nlu-generative-answers-azure-ai-search)
- [Azure OpenAI Vectorizer](https://learn.microsoft.com/azure/search/vector-search-how-to-configure-vectorizer)
