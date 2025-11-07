#!/bin/bash
set -e

# Configuration
RESOURCE_GROUP="indsolse-dev-rg"
LOCATION="swedencentral"
OLD_ENV_NAME="indsolse-dev-env"
NEW_ENV_NAME="indsolse-dev-env-vnet"
VNET_NAME="indsolse-dev-vnet"
ACA_SUBNET_NAME="aca-subnet"
LOG_ANALYTICS_NAME="indsolse-dev-logs"
ACR_NAME="indsolsedevacr"

# App configurations
BACKEND_NAME="indsolse-dev-backend-v2"
FRONTEND_NAME="indsolse-dev-frontend-v2"

echo "🔧 Recreating Container Apps Environment with VNet Integration..."
echo ""
echo "⚠️  WARNING: This will create a NEW environment and redeploy your apps."
echo "⚠️  Your old environment will remain for rollback if needed."
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# Step 1: Get subnet ID
echo ""
echo "🔍 Step 1: Getting subnet ID..."
SUBNET_ID=$(az network vnet subnet show \
  --resource-group $RESOURCE_GROUP \
  --vnet-name $VNET_NAME \
  --name $ACA_SUBNET_NAME \
  --query "id" -o tsv)

echo "✅ Subnet ID: $SUBNET_ID"

# Step 2: Get Log Analytics workspace ID
echo ""
echo "🔍 Step 2: Getting Log Analytics workspace..."
LOG_ANALYTICS_ID=$(az monitor log-analytics workspace show \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $LOG_ANALYTICS_NAME \
  --query "customerId" -o tsv)

LOG_ANALYTICS_KEY=$(az monitor log-analytics workspace get-shared-keys \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $LOG_ANALYTICS_NAME \
  --query "primarySharedKey" -o tsv)

echo "✅ Log Analytics configured"

# Step 3: Create new Container Apps environment with VNet
echo ""
echo "🏗️  Step 3: Creating VNet-integrated Container Apps environment..."
az containerapp env create \
  --name $NEW_ENV_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --infrastructure-subnet-resource-id $SUBNET_ID \
  --logs-workspace-id $LOG_ANALYTICS_ID \
  --logs-workspace-key $LOG_ANALYTICS_KEY \
  --internal-only false

echo "✅ New environment created: $NEW_ENV_NAME"

# Step 4: Get backend principal ID from old app
echo ""
echo "🔍 Step 4: Getting backend managed identity..."
BACKEND_PRINCIPAL_ID=$(az containerapp show \
  --name $BACKEND_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "identity.principalId" -o tsv)

echo "✅ Backend Principal ID: $BACKEND_PRINCIPAL_ID"

# Step 5: Redeploy backend to new environment
echo ""
echo "🚀 Step 5: Deploying backend to new environment..."
az containerapp create \
  --name "${BACKEND_NAME}-vnet" \
  --resource-group $RESOURCE_GROUP \
  --environment $NEW_ENV_NAME \
  --image "${ACR_NAME}.azurecr.io/industry-solutions-backend:v2.2" \
  --registry-server "${ACR_NAME}.azurecr.io" \
  --registry-identity system \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1Gi \
  --env-vars \
    AZURE_COSMOS_DB_ENDPOINT=secretref:cosmos-endpoint \
    AZURE_COSMOS_DB_NAME=secretref:cosmos-db \
    AZURE_SEARCH_ENDPOINT=secretref:search-endpoint \
    AZURE_SEARCH_INDEX=secretref:search-index \
    AZURE_OPENAI_ENDPOINT=secretref:openai-endpoint \
    AZURE_OPENAI_CHAT_MODEL=secretref:openai-model \
    AZURE_OPENAI_EMBEDDING_MODEL=secretref:embedding-model \
  --secrets \
    cosmos-endpoint="https://indsolse-dev-db-okumlm.documents.azure.com:443/" \
    cosmos-db="industry-solutions" \
    search-endpoint="https://indsolse-dev-srch-okumlm.search.windows.net" \
    search-index="partner-solutions-index" \
    openai-endpoint="https://indsolse-dev-aoai.openai.azure.com/" \
    openai-model="gpt-4" \
    embedding-model="text-embedding-3-large" \
  --system-assigned

echo "✅ Backend deployed"

# Step 6: Get new backend URL and principal ID
echo ""
echo "🔍 Step 6: Getting new backend URL..."
NEW_BACKEND_URL=$(az containerapp show \
  --name "${BACKEND_NAME}-vnet" \
  --resource-group $RESOURCE_GROUP \
  --query "properties.configuration.ingress.fqdn" -o tsv)

NEW_BACKEND_PRINCIPAL_ID=$(az containerapp show \
  --name "${BACKEND_NAME}-vnet" \
  --resource-group $RESOURCE_GROUP \
  --query "identity.principalId" -o tsv)

echo "✅ New Backend URL: https://$NEW_BACKEND_URL"
echo "✅ New Principal ID: $NEW_BACKEND_PRINCIPAL_ID"

# Step 7: Assign RBAC roles to new backend
echo ""
echo "🔐 Step 7: Assigning RBAC roles to new backend..."

# Cosmos DB Data Contributor
az cosmosdb sql role assignment create \
  --account-name indsolse-dev-db-okumlm \
  --resource-group $RESOURCE_GROUP \
  --scope "/subscriptions/7a28b21e-0d3e-4435-a686-d92889d4ee96/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.DocumentDB/databaseAccounts/indsolse-dev-db-okumlm" \
  --principal-id $NEW_BACKEND_PRINCIPAL_ID \
  --role-definition-id "00000000-0000-0000-0000-000000000002"

# Search Index Data Reader
az role assignment create \
  --assignee $NEW_BACKEND_PRINCIPAL_ID \
  --role "Search Index Data Reader" \
  --scope "/subscriptions/7a28b21e-0d3e-4435-a686-d92889d4ee96/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.Search/searchServices/indsolse-dev-srch-okumlm"

# Cognitive Services OpenAI User
az role assignment create \
  --assignee $NEW_BACKEND_PRINCIPAL_ID \
  --role "Cognitive Services OpenAI User" \
  --scope "/subscriptions/7a28b21e-0d3e-4435-a686-d92889d4ee96/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.CognitiveServices/accounts/indsolse-dev-aoai"

# ACR Pull
az role assignment create \
  --assignee $NEW_BACKEND_PRINCIPAL_ID \
  --role "AcrPull" \
  --scope "/subscriptions/7a28b21e-0d3e-4435-a686-d92889d4ee96/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.ContainerRegistry/registries/${ACR_NAME}"

echo "✅ RBAC roles assigned"

# Step 8: Deploy frontend to new environment
echo ""
echo "🚀 Step 8: Deploying frontend to new environment..."
az containerapp create \
  --name "${FRONTEND_NAME}-vnet" \
  --resource-group $RESOURCE_GROUP \
  --environment $NEW_ENV_NAME \
  --image "${ACR_NAME}.azurecr.io/industry-solutions-frontend:v2.2" \
  --registry-server "${ACR_NAME}.azurecr.io" \
  --registry-identity system \
  --target-port 8501 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1Gi \
  --env-vars \
    BACKEND_URL="https://${NEW_BACKEND_URL}" \
  --system-assigned

echo "✅ Frontend deployed"

# Step 9: Get new frontend URL
echo ""
echo "🔍 Step 9: Getting new frontend URL..."
NEW_FRONTEND_URL=$(az containerapp show \
  --name "${FRONTEND_NAME}-vnet" \
  --resource-group $RESOURCE_GROUP \
  --query "properties.configuration.ingress.fqdn" -o tsv)

echo "✅ New Frontend URL: https://$NEW_FRONTEND_URL"

# Step 10: Assign ACR Pull to frontend
echo ""
echo "🔐 Step 10: Assigning ACR Pull to frontend..."
NEW_FRONTEND_PRINCIPAL_ID=$(az containerapp show \
  --name "${FRONTEND_NAME}-vnet" \
  --resource-group $RESOURCE_GROUP \
  --query "identity.principalId" -o tsv)

az role assignment create \
  --assignee $NEW_FRONTEND_PRINCIPAL_ID \
  --role "AcrPull" \
  --scope "/subscriptions/7a28b21e-0d3e-4435-a686-d92889d4ee96/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.ContainerRegistry/registries/${ACR_NAME}"

echo "✅ ACR Pull assigned to frontend"

echo ""
echo "✨ Container Apps environment recreated with VNet integration!"
echo ""
echo "📊 Summary:"
echo "  New Environment: $NEW_ENV_NAME"
echo "  Backend: https://$NEW_BACKEND_URL"
echo "  Frontend: https://$NEW_FRONTEND_URL"
echo ""
echo "🧪 Test the new apps:"
echo "  curl https://$NEW_BACKEND_URL/api/health"
echo "  open https://$NEW_FRONTEND_URL"
echo ""
echo "✅ Your apps can now access Cosmos DB via Private Endpoint!"
echo "   No more firewall IP management needed."
echo ""
echo "⚠️  Old apps still running at:"
echo "  Backend: https://indsolse-dev-backend-v2.redplant-675b33da.swedencentral.azurecontainerapps.io"
echo "  Frontend: https://indsolse-dev-frontend-v2.redplant-675b33da.swedencentral.azurecontainerapps.io"
echo ""
echo "📝 After testing, you can delete the old environment: $OLD_ENV_NAME"
