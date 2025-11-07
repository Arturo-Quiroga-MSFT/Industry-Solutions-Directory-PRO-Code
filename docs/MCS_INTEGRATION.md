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

For future data updates, you have two options:

### Option A: Keep Using Manual Vectorization (Current)
Continue using `ingest_data.py` but point it to the new index. The integrated vectorizer will be ignored since you're providing vectors directly.

### Option B: Simplify to Integrated Vectorization
Modify your ingestion script to NOT call the embedding API - just upload documents with text fields, and let the integrated vectorizer handle it:

```python
# Simplified ingestion - no embedding calls needed!
doc = {
    "id": solution_id,
    "solution_name": solution_name,
    "content": content,  # Just text - vectorization happens automatically
    # No content_vector field needed
}
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
