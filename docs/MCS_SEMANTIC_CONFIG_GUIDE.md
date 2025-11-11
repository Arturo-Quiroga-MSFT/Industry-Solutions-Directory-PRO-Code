# Adding Semantic Configuration for Microsoft Copilot Studio

## The Issue

Your PSA colleague working with **Microsoft Copilot Studio (MCS)** is encountering issues because the current Azure AI Search index lacks a **semantic configuration**. While the index has integrated vectorization (which MCS requires), it's missing semantic search configuration that MCS Generative Answers feature expects.

## Why MCS Requires Semantic Configuration

Microsoft Copilot Studio's Generative Answers feature uses:
1. **Integrated Vectorization** - For automatic embedding generation ✅ (You have this)
2. **Semantic Configuration** - For L2 semantic reranking and caption extraction ❌ (Currently missing)

Without semantic configuration, MCS may:
- Show the index as "unsupported" or "limited functionality"
- Fail to extract proper captions and answers
- Provide suboptimal relevance ranking

## Solution: Add Semantic Configuration

### Option 1: Update Existing Index (Recommended)

Run the enhanced index creation script that adds semantic configuration:

```bash
cd data-ingestion/integrated-vectorization
python 02_create_index_with_semantic.py
```

This will **update** your existing `partner-solutions-integrated` index to add:
- **Semantic configuration** named "default"
- **Title field**: `solution_name`
- **Content fields**: `description`, `chunk_text`, `content`
- **Keywords fields**: `partner_name`, `industry`, `theme`

### Option 2: Create New Index with Semantic Config

If you prefer not to modify the existing index, you can create a new one:

```bash
# Edit config.py to use a new index name
# Change INDEX_NAME = "partner-solutions-integrated-semantic"

python 02_create_index_with_semantic.py
python 03_create_skillset.py
python 04_create_indexer.py
```

## What is Semantic Configuration?

Semantic configuration tells Azure AI Search which fields to use for:

1. **Title Field** - The main identifier (e.g., `solution_name`)
2. **Content Fields** - Fields containing detailed text for semantic matching
3. **Keywords Fields** - Fields containing important terms for ranking

Azure AI Search uses this configuration to:
- Apply **L2 semantic reranking** (Bing-powered relevance)
- Extract **captions** (relevant excerpts from content)
- Generate **answers** (direct answers to questions)

## Benefits of Adding Semantic Configuration

### For MCS (Your PSA Colleague)
- ✅ Full MCS Generative Answers support
- ✅ Better answer quality with semantic reranking
- ✅ Automatic caption extraction
- ✅ Index shows as "fully supported" in MCS

### For Your Pro-Code Solution
- ✅ Improved search relevance with L2 reranking
- ✅ Better captions for user responses
- ✅ Hybrid search: Vector + Keyword + Semantic
- ✅ No breaking changes (backward compatible)

### For Both
- ✅ Single index serves both pro-code and low-code
- ✅ Consistent search results across solutions
- ✅ Better user experience overall

## How to Use in Microsoft Copilot Studio

After adding semantic configuration, tell your PSA colleague:

### Step 1: Connect to Azure AI Search
1. In MCS, open your copilot
2. Add a **Generative answers** node
3. Select **Azure AI Search** as the data source

### Step 2: Configure Connection
- **Search Service**: `indsolse-dev-srch-okumlm.search.windows.net`
- **Index Name**: `partner-solutions-integrated`
- **Authentication**: Managed Identity or API Key

### Step 3: Verify Semantic Configuration
- MCS should now show the index as **fully supported** ✅
- You should see semantic ranking options available
- Test with a query to verify captions are extracted

## How to Use in Your FastAPI Backend

The backend has been updated to support semantic search. To enable it:

### Option 1: Use Semantic Search Directly

```python
# In your chat endpoint, use semantic_hybrid_search instead of hybrid_search
results = await search_service.semantic_hybrid_search(
    query=user_query,
    filters=filters,
    top_k=5
)
```

### Option 2: Auto-Detection (Graceful Fallback)

The `semantic_hybrid_search` method automatically falls back to regular hybrid search if semantic configuration is not available. This ensures backward compatibility.

```python
# This will use semantic if available, hybrid if not
results = await search_service.semantic_hybrid_search(
    query=user_query,
    filters=filters,
    top_k=5
)
```

### Testing Semantic Search

```bash
# Start your backend
cd backend
uvicorn app.main:app --reload

# Test semantic search
curl http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What AI solutions help with patient care in hospitals?"
  }'
```

Look for these indicators in responses:
- Higher relevance scores (reranker scores)
- Better-quality excerpts (semantic captions)
- More contextually relevant results

## Cost Implications

### Semantic Search Pricing
- **Standard tier**: Semantic ranking is included, but limited to specific SKUs
- **Required SKU**: Basic tier or higher with semantic search enabled
- **Cost**: Approximately $250/month for Standard S1 with semantic search

### Current Setup Check

Verify your search service tier supports semantic search:

```bash
# Check via Azure CLI
az search service show \
  --name indsolse-dev-srch-okumlm \
  --resource-group <your-resource-group> \
  --query "sku.name"
```

Required: `basic` or higher. If you're on `free` tier, you'll need to upgrade.

## Troubleshooting

### Issue: "Semantic configuration not found"

**Solution**: Make sure you ran `02_create_index_with_semantic.py` and the index was updated.

```bash
# Verify semantic config exists
az search index show \
  --name partner-solutions-integrated \
  --service-name indsolse-dev-srch-okumlm \
  --resource-group <your-resource-group> \
  --query "semanticSearch"
```

### Issue: MCS still shows "unsupported"

**Solution**: 
1. Refresh the MCS interface (hard refresh: Cmd+Shift+R)
2. Disconnect and reconnect to Azure AI Search
3. Verify the index has both integrated vectorization AND semantic configuration
4. Check that managed identity has proper permissions

### Issue: Backend getting 400 errors

**Solution**: If your search service doesn't support semantic search:

```python
# The code already handles this gracefully
# Check logs for: "Semantic search failed, falling back to hybrid"
# This means semantic isn't available but hybrid still works
```

### Issue: Higher costs than expected

**Solution**: Semantic search adds cost. If budget is constrained:
- Use semantic only in production
- Use regular hybrid in dev/test
- Or continue without semantic (MCS may have limited functionality)

## Comparison: With vs Without Semantic Configuration

| Feature | Without Semantic | With Semantic |
|---------|------------------|---------------|
| **Vector Search** | ✅ Yes | ✅ Yes |
| **Keyword Search** | ✅ Yes | ✅ Yes |
| **Hybrid Search** | ✅ Yes | ✅ Yes |
| **L2 Reranking** | ❌ No | ✅ Yes |
| **Caption Extraction** | ❌ No | ✅ Yes |
| **Answer Extraction** | ❌ No | ✅ Yes |
| **MCS Full Support** | ⚠️ Limited | ✅ Full |
| **Pro-Code Works** | ✅ Yes | ✅ Yes |
| **Monthly Cost** | Lower | +$250 |

## Recommendation

**For your scenario, I recommend adding semantic configuration because:**

1. ✅ Your PSA colleague needs full MCS support
2. ✅ It improves both pro-code and low-code solutions
3. ✅ Better search relevance = better user experience
4. ✅ No breaking changes to existing code
5. ✅ Single index serves both teams efficiently

**Estimated effort**: 10 minutes to update the index

## Next Steps

1. **Run the script**:
   ```bash
   cd data-ingestion/integrated-vectorization
   python 02_create_index_with_semantic.py
   ```

2. **Verify in Azure Portal**:
   - Go to Azure AI Search → Indexes → `partner-solutions-integrated`
   - Check "Semantic configurations" section
   - Should see "default" configuration

3. **Test in MCS**:
   - Have your PSA colleague reconnect to the index
   - Verify it shows as fully supported
   - Test a query with Generative Answers

4. **Test in FastAPI** (optional):
   - Update chat endpoint to use `semantic_hybrid_search`
   - Test queries and compare relevance
   - Monitor for any errors

5. **Monitor costs**:
   - Track Azure AI Search costs in Azure Portal
   - Compare before/after semantic enablement
   - Adjust usage based on budget

## References

- [Azure AI Search Semantic Ranking](https://learn.microsoft.com/azure/search/semantic-search-overview)
- [Microsoft Copilot Studio with Azure AI Search](https://learn.microsoft.com/microsoft-copilot-studio/nlu-generative-answers-azure-ai-search)
- [Semantic Configuration](https://learn.microsoft.com/azure/search/semantic-how-to-query-request)
- [Pricing](https://azure.microsoft.com/pricing/details/search/)

---

**Need help?** Reach out to Arturo or refer to the existing docs:
- `docs/MCS_INTEGRATION.md` - General MCS integration guide
- `docs/MCS_SIMPLE_SOLUTION.md` - Quick workarounds
- `ARCHITECTURE.md` - Overall system architecture
