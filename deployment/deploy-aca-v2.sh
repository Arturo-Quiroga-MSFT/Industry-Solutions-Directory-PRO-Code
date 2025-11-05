#!/bin/bash

##############################################################################
# Deploy Azure Container Apps - Version 2 (Blue-Green Deployment)
# This script deploys v2 apps alongside the existing v1 apps
##############################################################################

set -e  # Exit on error

# Configuration
RESOURCE_GROUP="indsolse-dev-rg"
LOCATION="swedencentral"
ACR_NAME="indsolsedevacr"
ENVIRONMENT_NAME="indsolse-dev-env"
BACKEND_APP_NAME="indsolse-dev-backend-v2"
FRONTEND_APP_NAME="indsolse-dev-frontend-v2"
BACKEND_IMAGE="industry-solutions-backend:v2"
FRONTEND_IMAGE="industry-solutions-frontend:v2"

# Azure resource IDs (same as v1)
OPENAI_ACCOUNT="indsolse-dev-ai-okumlm"
SEARCH_SERVICE="indsolse-dev-srch-okumlm"
COSMOS_ACCOUNT="indsolse-dev-db-okumlm"

echo "=========================================="
echo "Azure Container Apps Deployment - v2"
echo "=========================================="
echo ""
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "ACR: $ACR_NAME"
echo "Environment: $ENVIRONMENT_NAME"
echo "Backend App: $BACKEND_APP_NAME"
echo "Frontend App: $FRONTEND_APP_NAME"
echo ""

# Check if logged in to Azure
echo "Checking Azure CLI login..."
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure CLI"
    echo "Please run: az login"
    exit 1
fi

echo "✅ Logged in to Azure"
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "Subscription: $SUBSCRIPTION_ID"
echo ""

# Build backend image
echo "=========================================="
echo "Building Backend Docker Image (v2)"
echo "=========================================="
cd backend
az acr build \
    --registry $ACR_NAME \
    --image $BACKEND_IMAGE \
    --file Dockerfile \
    .

if [ $? -eq 0 ]; then
    echo "✅ Backend image built successfully"
else
    echo "❌ Failed to build backend image"
    exit 1
fi

cd ..

# Build frontend image
echo ""
echo "=========================================="
echo "Building Frontend Docker Image (v2)"
echo "=========================================="
cd frontend
az acr build \
    --registry $ACR_NAME \
    --image $FRONTEND_IMAGE \
    --file Dockerfile \
    .

if [ $? -eq 0 ]; then
    echo "✅ Frontend image built successfully"
else
    echo "❌ Failed to build frontend image"
    exit 1
fi

cd ..

# Deploy backend container app (v2)
echo ""
echo "=========================================="
echo "Deploying Backend Container App (v2)"
echo "=========================================="

az containerapp create \
    --name $BACKEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT_NAME \
    --image "$ACR_NAME.azurecr.io/$BACKEND_IMAGE" \
    --registry-server "$ACR_NAME.azurecr.io" \
    --registry-identity system \
    --target-port 8000 \
    --ingress external \
    --min-replicas 1 \
    --max-replicas 3 \
    --cpu 0.5 \
    --memory 1Gi \
    --env-vars \
        AZURE_OPENAI_ENDPOINT="https://$OPENAI_ACCOUNT.openai.azure.com/" \
        AZURE_OPENAI_API_VERSION="2024-02-01" \
        AZURE_OPENAI_CHAT_DEPLOYMENT="gpt-4.1-mini" \
        AZURE_SEARCH_ENDPOINT="https://$SEARCH_SERVICE.search.windows.net" \
        AZURE_SEARCH_INDEX_NAME="partner-solutions-index" \
        AZURE_COSMOS_ENDPOINT="https://$COSMOS_ACCOUNT.documents.azure.com:443/" \
        AZURE_COSMOS_DATABASE="industry-solutions-db" \
        AZURE_COSMOS_CONTAINER="chat-sessions" \
    --system-assigned

if [ $? -eq 0 ]; then
    echo "✅ Backend container app (v2) created successfully"
else
    echo "❌ Failed to create backend container app (v2)"
    exit 1
fi

# Get backend URL
BACKEND_URL=$(az containerapp show \
    --name $BACKEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn \
    -o tsv)

BACKEND_URL="https://$BACKEND_URL"
echo "Backend URL (v2): $BACKEND_URL"

# Deploy frontend container app (v2)
echo ""
echo "=========================================="
echo "Deploying Frontend Container App (v2)"
echo "=========================================="

az containerapp create \
    --name $FRONTEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT_NAME \
    --image "$ACR_NAME.azurecr.io/$FRONTEND_IMAGE" \
    --registry-server "$ACR_NAME.azurecr.io" \
    --registry-identity system \
    --target-port 8501 \
    --ingress external \
    --min-replicas 1 \
    --max-replicas 3 \
    --cpu 0.5 \
    --memory 1Gi \
    --env-vars \
        BACKEND_API_URL="$BACKEND_URL" \
    --system-assigned

if [ $? -eq 0 ]; then
    echo "✅ Frontend container app (v2) created successfully"
else
    echo "❌ Failed to create frontend container app (v2)"
    exit 1
fi

# Get frontend URL
FRONTEND_URL=$(az containerapp show \
    --name $FRONTEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn \
    -o tsv)

FRONTEND_URL="https://$FRONTEND_URL"
echo "Frontend URL (v2): $FRONTEND_URL"

# Assign RBAC permissions to backend managed identity (v2)
echo ""
echo "=========================================="
echo "Assigning RBAC Permissions to Backend (v2)"
echo "=========================================="

# Get backend managed identity principal ID
BACKEND_PRINCIPAL_ID=$(az containerapp show \
    --name $BACKEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query identity.principalId \
    -o tsv)

echo "Backend Principal ID: $BACKEND_PRINCIPAL_ID"

# Assign Azure OpenAI User role
echo "Assigning Cognitive Services OpenAI User role..."
az role assignment create \
    --assignee $BACKEND_PRINCIPAL_ID \
    --role "Cognitive Services OpenAI User" \
    --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/$OPENAI_ACCOUNT"

# Assign Search Index Data Reader role
echo "Assigning Search Index Data Reader role..."
az role assignment create \
    --assignee $BACKEND_PRINCIPAL_ID \
    --role "Search Index Data Reader" \
    --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Search/searchServices/$SEARCH_SERVICE"

# Assign Cosmos DB Built-in Data Contributor role
echo "Assigning Cosmos DB Built-in Data Contributor role..."
COSMOS_RESOURCE_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.DocumentDB/databaseAccounts/$COSMOS_ACCOUNT"

az cosmosdb sql role assignment create \
    --account-name $COSMOS_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --role-definition-name "Cosmos DB Built-in Data Contributor" \
    --principal-id $BACKEND_PRINCIPAL_ID \
    --scope $COSMOS_RESOURCE_ID

echo "✅ RBAC permissions assigned successfully"

# Summary
echo ""
echo "=========================================="
echo "Deployment Complete - Version 2"
echo "=========================================="
echo ""
echo "Backend v2 URL: $BACKEND_URL"
echo "Frontend v2 URL: $FRONTEND_URL"
echo ""
echo "V1 Apps (Still Running):"
echo "  Backend v1: https://indsolse-dev-backend.redplant-675b33da.swedencentral.azurecontainerapps.io"
echo "  Frontend v1: https://indsolse-dev-frontend.redplant-675b33da.swedencentral.azurecontainerapps.io"
echo ""
echo "Next Steps:"
echo "1. Test v2 apps: $FRONTEND_URL"
echo "2. Verify new features: Generate Summary and Download Conversation"
echo "3. Confirm v1 apps still working"
echo "4. Once validated, you can update DNS/routing or decommission v1"
echo ""
echo "Health Check:"
echo "  curl $BACKEND_URL/api/health"
echo ""
