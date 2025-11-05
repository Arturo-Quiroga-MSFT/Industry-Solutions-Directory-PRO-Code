# Deployment Guide: Azure Container Apps

This guide walks you through deploying the Industry Solutions Directory to Azure Container Apps using Azure Container Registry.

## Prerequisites

1. **Azure CLI** installed and authenticated
   ```bash
   az login
   az account set --subscription "your-subscription-name"
   ```

2. **Existing Azure Resources** (from infrastructure deployment):
   - Resource Group: `indsolse-dev-rg`
   - Azure OpenAI: `indsolse-dev-ai-okumlm`
   - Azure AI Search: `indsolse-dev-srch-okumlm`
   - Azure Cosmos DB: `indsolse-dev-db-okumlm`

3. **Docker** (optional, for local testing)

## Architecture

```
┌─────────────────┐      ┌─────────────────┐
│   Streamlit     │─────▶│   FastAPI       │
│   Frontend      │      │   Backend       │
│  (Port 8501)    │      │  (Port 8000)    │
└─────────────────┘      └─────────────────┘
         │                        │
         │                        ├──▶ Azure OpenAI
         │                        ├──▶ Azure AI Search
         │                        └──▶ Azure Cosmos DB
         │
    Container Apps Environment
```

## Deployment Steps

### Option 1: Automated Deployment (Recommended)

Run the deployment script:

```bash
cd deployment
./deploy-aca.sh
```

This script will:
1. ✅ Create Azure Container Registry (if not exists)
2. ✅ Build backend Docker image and push to ACR
3. ✅ Build frontend Docker image and push to ACR
4. ✅ Create Container Apps Environment
5. ✅ Deploy backend Container App with managed identity
6. ✅ Deploy frontend Container App
7. ✅ Assign RBAC permissions for Azure services

### Option 2: Manual Deployment

#### Step 1: Create Azure Container Registry

```bash
az acr create \
  --resource-group indsolse-dev-rg \
  --name indsolsedevacr \
  --sku Basic \
  --location swedencentral \
  --admin-enabled true
```

#### Step 2: Build and Push Backend Image

```bash
cd backend
az acr build \
  --registry indsolsedevacr \
  --image industry-solutions-backend:latest \
  --file Dockerfile \
  .
```

#### Step 3: Build and Push Frontend Image

```bash
cd ../frontend
az acr build \
  --registry indsolsedevacr \
  --image industry-solutions-frontend:latest \
  --file Dockerfile \
  .
```

#### Step 4: Create Container Apps Environment

```bash
az containerapp env create \
  --name indsolse-dev-env \
  --resource-group indsolse-dev-rg \
  --location swedencentral
```

#### Step 5: Deploy Backend

```bash
az containerapp create \
  --name indsolse-dev-backend \
  --resource-group indsolse-dev-rg \
  --environment indsolse-dev-env \
  --image indsolsedevacr.azurecr.io/industry-solutions-backend:latest \
  --target-port 8000 \
  --ingress external \
  --registry-server indsolsedevacr.azurecr.io \
  --registry-identity system \
  --cpu 0.5 \
  --memory 1.0Gi \
  --min-replicas 1 \
  --max-replicas 3 \
  --env-vars \
    AZURE_OPENAI_ENDPOINT=https://indsolse-dev-ai-okumlm.openai.azure.com/ \
    AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4.1-mini \
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large \
    AZURE_OPENAI_API_VERSION=2024-02-01 \
    AZURE_SEARCH_ENDPOINT=https://indsolse-dev-srch-okumlm.search.windows.net \
    AZURE_SEARCH_INDEX_NAME=partner-solutions-index \
    AZURE_COSMOS_ENDPOINT=https://indsolse-dev-db-okumlm.documents.azure.com:443/ \
    AZURE_COSMOS_DATABASE_NAME=industry-solutions-db \
    AZURE_COSMOS_CONTAINER_NAME=chat-sessions \
  --system-assigned
```

#### Step 6: Get Backend URL

```bash
BACKEND_URL=$(az containerapp show \
  --name indsolse-dev-backend \
  --resource-group indsolse-dev-rg \
  --query properties.configuration.ingress.fqdn -o tsv)

echo "Backend URL: https://$BACKEND_URL"
```

#### Step 7: Deploy Frontend

```bash
az containerapp create \
  --name indsolse-dev-frontend \
  --resource-group indsolse-dev-rg \
  --environment indsolse-dev-env \
  --image indsolsedevacr.azurecr.io/industry-solutions-frontend:latest \
  --target-port 8501 \
  --ingress external \
  --registry-server indsolsedevacr.azurecr.io \
  --registry-identity system \
  --cpu 0.5 \
  --memory 1.0Gi \
  --min-replicas 1 \
  --max-replicas 3 \
  --env-vars BACKEND_API_URL=https://$BACKEND_URL \
  --system-assigned
```

#### Step 8: Assign RBAC Permissions

Get the backend's managed identity principal ID:

```bash
BACKEND_PRINCIPAL_ID=$(az containerapp show \
  --name indsolse-dev-backend \
  --resource-group indsolse-dev-rg \
  --query identity.principalId -o tsv)
```

Assign permissions:

```bash
# OpenAI
az role assignment create \
  --assignee $BACKEND_PRINCIPAL_ID \
  --role "Cognitive Services OpenAI User" \
  --scope $(az cognitiveservices account show --name indsolse-dev-ai-okumlm --resource-group indsolse-dev-rg --query id -o tsv)

# AI Search
az role assignment create \
  --assignee $BACKEND_PRINCIPAL_ID \
  --role "Search Index Data Reader" \
  --scope $(az search service show --name indsolse-dev-srch-okumlm --resource-group indsolse-dev-rg --query id -o tsv)

# Cosmos DB
az cosmosdb sql role assignment create \
  --account-name indsolse-dev-db-okumlm \
  --resource-group indsolse-dev-rg \
  --scope "/" \
  --principal-id $BACKEND_PRINCIPAL_ID \
  --role-definition-id 00000000-0000-0000-0000-000000000002
```

## Post-Deployment

### Get Application URLs

```bash
# Backend
az containerapp show \
  --name indsolse-dev-backend \
  --resource-group indsolse-dev-rg \
  --query properties.configuration.ingress.fqdn -o tsv

# Frontend
az containerapp show \
  --name indsolse-dev-frontend \
  --resource-group indsolse-dev-rg \
  --query properties.configuration.ingress.fqdn -o tsv
```

### Test the Deployment

1. **Backend Health Check**:
   ```bash
   curl https://<backend-url>/api/health
   ```

2. **Frontend UI**: Open browser to `https://<frontend-url>`

### Monitor Logs

```bash
# Backend logs
az containerapp logs show \
  --name indsolse-dev-backend \
  --resource-group indsolse-dev-rg \
  --follow

# Frontend logs
az containerapp logs show \
  --name indsolse-dev-frontend \
  --resource-group indsolse-dev-rg \
  --follow
```

## Updating the Application

To update either app after code changes:

```bash
# Rebuild and push backend
cd backend
az acr build --registry indsolsedevacr --image industry-solutions-backend:latest --file Dockerfile .

# Update backend container app
az containerapp update \
  --name indsolse-dev-backend \
  --resource-group indsolse-dev-rg \
  --image indsolsedevacr.azurecr.io/industry-solutions-backend:latest

# Same for frontend...
```

## Scaling

Container Apps auto-scale based on HTTP traffic. Adjust scaling rules:

```bash
az containerapp update \
  --name indsolse-dev-backend \
  --resource-group indsolse-dev-rg \
  --min-replicas 1 \
  --max-replicas 10
```

## Cost Optimization

- **Development**: Use `--min-replicas 0` to scale to zero when idle
- **Production**: Keep `--min-replicas 1` for better availability
- **Review pricing**: Container Apps charges for vCPU and memory per second

## Troubleshooting

### Backend can't access Azure services

Check RBAC assignments:
```bash
az role assignment list --assignee $BACKEND_PRINCIPAL_ID --all
```

### Frontend can't reach backend

Verify backend URL environment variable:
```bash
az containerapp show \
  --name indsolse-dev-frontend \
  --resource-group indsolse-dev-rg \
  --query properties.template.containers[0].env
```

### Container fails to start

Check logs and events:
```bash
az containerapp logs show --name indsolse-dev-backend --resource-group indsolse-dev-rg --tail 100
az containerapp show --name indsolse-dev-backend --resource-group indsolse-dev-rg --query properties.latestRevisionName -o tsv
```

## Clean Up

To remove all Container Apps resources:

```bash
az containerapp delete --name indsolse-dev-backend --resource-group indsolse-dev-rg --yes
az containerapp delete --name indsolse-dev-frontend --resource-group indsolse-dev-rg --yes
az containerapp env delete --name indsolse-dev-env --resource-group indsolse-dev-rg --yes
az acr delete --name indsolsedevacr --resource-group indsolse-dev-rg --yes
```
