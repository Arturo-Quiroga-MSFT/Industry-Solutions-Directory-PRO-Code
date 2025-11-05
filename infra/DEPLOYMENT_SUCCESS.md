# Infrastructure Deployment Summary

## Deployment Information
- **Deployment Name**: industry-solutions-sweden-deployment
- **Region**: Sweden Central
- **Resource Group**: indsolse-dev-rg
- **Status**: ✅ Succeeded
- **Timestamp**: 2025-11-04T20:43:10Z

## Deployed Resources

### Azure OpenAI Service
- **Name**: indsolse-dev-ai-okumlm
- **Endpoint**: https://indsolse-dev-ai-okumlm.openai.azure.com/
- **Deployments**:
  - `gpt-4.1-mini` (GPT-4.1, version 2025-04-14, GlobalStandard SKU, 100 capacity)
  - `text-embedding-3-large` (Embedding model, version 1, Standard SKU, 100 capacity)
- **Authentication**: Azure CLI / Managed Identity (local auth disabled)

### Azure AI Search
- **Name**: indsolse-dev-srch-okumlm
- **Endpoint**: https://indsolse-dev-srch-okumlm.search.windows.net
- **SKU**: Basic
- **Replicas**: 1
- **Partitions**: 1
- **Authentication**: Azure CLI / Managed Identity (local auth disabled)

### Azure Cosmos DB
- **Account Name**: indsolse-dev-db-okumlm
- **Endpoint**: https://indsolse-dev-db-okumlm.documents.azure.com:443/
- **Database**: industry-solutions-db
- **Container**: chat-sessions (partition key: /sessionId)
- **Configuration**: Serverless, Continuous backup (7 days)
- **Authentication**: Azure CLI / Managed Identity (local auth disabled)

### Azure Key Vault
- **Name**: indsolse-dev-kv-okumlm
- **URI**: https://indsolse-dev-kv-okumlm.vault.azure.net/
- **SKU**: Standard
- **Features**: Enabled for deployment and template deployment

### Application Insights
- **Name**: indsolse-dev-insights
- **Instrumentation Key**: e6abf535-44ec-4388-b4b5-24a5fd9512f3
- **Connection String**: Available in .env file
- **Log Analytics Workspace**: indsolse-dev-logs

## Next Steps

### 1. Grant RBAC Permissions
Since local authentication is disabled, you need to assign Azure RBAC roles to your user/service principal:

```bash
# Get your user object ID
USER_OBJECT_ID=$(az ad signed-in-user show --query id -o tsv)

# Azure OpenAI - Cognitive Services OpenAI User
az role assignment create \
  --assignee $USER_OBJECT_ID \
  --role "Cognitive Services OpenAI User" \
  --scope "/subscriptions/7a28b21e-0d3e-4435-a686-d92889d4ee96/resourceGroups/indsolse-dev-rg/providers/Microsoft.CognitiveServices/accounts/indsolse-dev-ai-okumlm"

# Azure AI Search - Search Index Data Contributor
az role assignment create \
  --assignee $USER_OBJECT_ID \
  --role "Search Index Data Contributor" \
  --scope "/subscriptions/7a28b21e-0d3e-4435-a686-d92889d4ee96/resourceGroups/indsolse-dev-rg/providers/Microsoft.Search/searchServices/indsolse-dev-srch-okumlm"

# Azure AI Search - Search Service Contributor
az role assignment create \
  --assignee $USER_OBJECT_ID \
  --role "Search Service Contributor" \
  --scope "/subscriptions/7a28b21e-0d3e-4435-a686-d92889d4ee96/resourceGroups/indsolse-dev-rg/providers/Microsoft.Search/searchServices/indsolse-dev-srch-okumlm"

# Cosmos DB - Cosmos DB Built-in Data Contributor
az cosmosdb sql role assignment create \
  --account-name indsolse-dev-db-okumlm \
  --resource-group indsolse-dev-rg \
  --role-definition-name "Cosmos DB Built-in Data Contributor" \
  --principal-id $USER_OBJECT_ID \
  --scope "/"
```

### 2. Create Search Index
Run the data ingestion script to create the search index and load sample data:

```bash
cd /Users/arturoquiroga/Industry-Solutions-Directory-PRO-Code
python data-ingestion/ingest_data.py
```

### 3. Test the Backend API
Start the FastAPI backend:

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### 4. Test the Chat Endpoint

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What healthcare solutions do you have?",
    "session_id": "test-session-001"
  }'
```

## Resource URLs
- **Resource Group Portal**: https://portal.azure.com/#resource/subscriptions/7a28b21e-0d3e-4435-a686-d92889d4ee96/resourceGroups/indsolse-dev-rg
- **Azure OpenAI Studio**: https://oai.azure.com/portal/indsolse-dev-ai-okumlm
- **AI Search Portal**: https://portal.azure.com/#resource/subscriptions/7a28b21e-0d3e-4435-a686-d92889d4ee96/resourceGroups/indsolse-dev-rg/providers/Microsoft.Search/searchServices/indsolse-dev-srch-okumlm
- **Cosmos DB Portal**: https://portal.azure.com/#resource/subscriptions/7a28b21e-0d3e-4435-a686-d92889d4ee96/resourceGroups/indsolse-dev-rg/providers/Microsoft.DocumentDB/databaseAccounts/indsolse-dev-db-okumlm

## Authentication Notes
All services are configured with **disableLocalAuth: true** for enhanced security. This means:
- ✅ Use Azure CLI: `az login` for local development
- ✅ Use Managed Identity for production deployments
- ❌ API keys are not available
- ✅ Better security with Azure AD authentication
- ✅ Fine-grained RBAC permissions
