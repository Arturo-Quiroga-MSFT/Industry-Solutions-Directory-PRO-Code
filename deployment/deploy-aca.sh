#!/bin/bash

# Azure Container Apps Deployment Script
# This script builds Docker images, pushes them to ACR, and deploys to Azure Container Apps

set -e  # Exit on error

# ============================================================================
# Configuration Variables
# ============================================================================

# Resource names (customize these)
RESOURCE_GROUP="indsolse-dev-rg"
LOCATION="swedencentral"
ACR_NAME="indsolsedevacr"  # Must be globally unique, lowercase, no hyphens
BACKEND_IMAGE_NAME="industry-solutions-backend"
FRONTEND_IMAGE_NAME="industry-solutions-frontend"
BACKEND_APP_NAME="indsolse-dev-backend"
FRONTEND_APP_NAME="indsolse-dev-frontend"
CONTAINER_APP_ENV="indsolse-dev-env"

# Azure resource IDs (will be retrieved)
OPENAI_ENDPOINT="https://indsolse-dev-ai-okumlm.openai.azure.com/"
SEARCH_ENDPOINT="https://indsolse-dev-srch-okumlm.search.windows.net"
COSMOS_ENDPOINT="https://indsolse-dev-db-okumlm.documents.azure.com:443/"

# ============================================================================
# Helper Functions
# ============================================================================

echo_header() {
    echo ""
    echo "============================================================================"
    echo "$1"
    echo "============================================================================"
}

echo_step() {
    echo ""
    echo "➜ $1"
}

# ============================================================================
# Pre-flight Checks
# ============================================================================

echo_header "Azure Container Apps Deployment"
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "ACR Name: $ACR_NAME"
echo ""

# Check if logged in to Azure
echo_step "Checking Azure CLI login status..."
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure. Please run 'az login' first."
    exit 1
fi
echo "✅ Logged in to Azure"

# Get subscription info
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
echo "Subscription: $SUBSCRIPTION_NAME ($SUBSCRIPTION_ID)"

# ============================================================================
# Step 1: Create/Verify Azure Container Registry
# ============================================================================

echo_header "Step 1: Azure Container Registry Setup"

# Check if ACR exists
if az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo_step "ACR '$ACR_NAME' already exists"
else
    echo_step "Creating Azure Container Registry..."
    az acr create \
        --resource-group $RESOURCE_GROUP \
        --name $ACR_NAME \
        --sku Basic \
        --location $LOCATION \
        --admin-enabled true
    echo "✅ ACR created"
fi

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)
echo "ACR Login Server: $ACR_LOGIN_SERVER"

# ============================================================================
# Step 2: Build and Push Backend Image
# ============================================================================

echo_header "Step 2: Build and Push Backend Image"

echo_step "Building backend Docker image..."
cd ../backend
az acr build \
    --registry $ACR_NAME \
    --image $BACKEND_IMAGE_NAME:latest \
    --image $BACKEND_IMAGE_NAME:$(date +%Y%m%d-%H%M%S) \
    --file Dockerfile \
    .

echo "✅ Backend image built and pushed"

# ============================================================================
# Step 3: Build and Push Frontend Image
# ============================================================================

echo_header "Step 3: Build and Push Frontend Image"

echo_step "Building frontend Docker image..."
cd ../frontend
az acr build \
    --registry $ACR_NAME \
    --image $FRONTEND_IMAGE_NAME:latest \
    --image $FRONTEND_IMAGE_NAME:$(date +%Y%m%d-%H%M%S) \
    --file Dockerfile \
    .

echo "✅ Frontend image built and pushed"

cd ../deployment

# ============================================================================
# Step 4: Create Container Apps Environment
# ============================================================================

echo_header "Step 4: Container Apps Environment Setup"

# Check if environment exists
if az containerapp env show --name $CONTAINER_APP_ENV --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo_step "Container Apps Environment '$CONTAINER_APP_ENV' already exists"
else
    echo_step "Creating Container Apps Environment..."
    az containerapp env create \
        --name $CONTAINER_APP_ENV \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION
    echo "✅ Environment created"
fi

# ============================================================================
# Step 5: Deploy Backend Container App
# ============================================================================

echo_header "Step 5: Deploy Backend Container App"

# Check if backend app exists
if az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo_step "Updating existing backend app..."
    az containerapp update \
        --name $BACKEND_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --image $ACR_LOGIN_SERVER/$BACKEND_IMAGE_NAME:latest
else
    echo_step "Creating backend Container App..."
    az containerapp create \
        --name $BACKEND_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --environment $CONTAINER_APP_ENV \
        --image $ACR_LOGIN_SERVER/$BACKEND_IMAGE_NAME:latest \
        --target-port 8000 \
        --ingress external \
        --registry-server $ACR_LOGIN_SERVER \
        --registry-identity system \
        --cpu 0.5 \
        --memory 1.0Gi \
        --min-replicas 1 \
        --max-replicas 3 \
        --env-vars \
            AZURE_OPENAI_ENDPOINT=$OPENAI_ENDPOINT \
            AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4.1-mini \
            AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large \
            AZURE_OPENAI_API_VERSION=2024-02-01 \
            AZURE_SEARCH_ENDPOINT=$SEARCH_ENDPOINT \
            AZURE_SEARCH_INDEX_NAME=partner-solutions-index \
            AZURE_COSMOS_ENDPOINT=$COSMOS_ENDPOINT \
            AZURE_COSMOS_DATABASE_NAME=industry-solutions-db \
            AZURE_COSMOS_CONTAINER_NAME=chat-sessions \
        --system-assigned
fi

# Enable managed identity for backend
echo_step "Configuring managed identity for backend..."
BACKEND_PRINCIPAL_ID=$(az containerapp show \
    --name $BACKEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query identity.principalId -o tsv)

echo "Backend Principal ID: $BACKEND_PRINCIPAL_ID"

# Get backend URL
BACKEND_URL=$(az containerapp show \
    --name $BACKEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn -o tsv)

echo "✅ Backend deployed at: https://$BACKEND_URL"

# ============================================================================
# Step 6: Deploy Frontend Container App
# ============================================================================

echo_header "Step 6: Deploy Frontend Container App"

# Check if frontend app exists
if az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo_step "Updating existing frontend app..."
    az containerapp update \
        --name $FRONTEND_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --image $ACR_LOGIN_SERVER/$FRONTEND_IMAGE_NAME:latest \
        --set-env-vars BACKEND_API_URL=https://$BACKEND_URL
else
    echo_step "Creating frontend Container App..."
    az containerapp create \
        --name $FRONTEND_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --environment $CONTAINER_APP_ENV \
        --image $ACR_LOGIN_SERVER/$FRONTEND_IMAGE_NAME:latest \
        --target-port 8501 \
        --ingress external \
        --registry-server $ACR_LOGIN_SERVER \
        --registry-identity system \
        --cpu 0.5 \
        --memory 1.0Gi \
        --min-replicas 1 \
        --max-replicas 3 \
        --env-vars \
            BACKEND_API_URL=https://$BACKEND_URL \
        --system-assigned
fi

# Get frontend URL
FRONTEND_URL=$(az containerapp show \
    --name $FRONTEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn -o tsv)

echo "✅ Frontend deployed at: https://$FRONTEND_URL"

# ============================================================================
# Step 7: Assign RBAC Permissions
# ============================================================================

echo_header "Step 7: Assign RBAC Permissions for Managed Identity"

# Get resource IDs
OPENAI_RESOURCE_ID=$(az cognitiveservices account show \
    --name indsolse-dev-ai-okumlm \
    --resource-group $RESOURCE_GROUP \
    --query id -o tsv)

SEARCH_RESOURCE_ID=$(az search service show \
    --name indsolse-dev-srch-okumlm \
    --resource-group $RESOURCE_GROUP \
    --query id -o tsv)

COSMOS_RESOURCE_ID=$(az cosmosdb show \
    --name indsolse-dev-db-okumlm \
    --resource-group $RESOURCE_GROUP \
    --query id -o tsv)

echo_step "Assigning OpenAI permissions..."
az role assignment create \
    --assignee $BACKEND_PRINCIPAL_ID \
    --role "Cognitive Services OpenAI User" \
    --scope $OPENAI_RESOURCE_ID \
    || echo "Role assignment already exists"

echo_step "Assigning Search permissions..."
az role assignment create \
    --assignee $BACKEND_PRINCIPAL_ID \
    --role "Search Index Data Reader" \
    --scope $SEARCH_RESOURCE_ID \
    || echo "Role assignment already exists"

az role assignment create \
    --assignee $BACKEND_PRINCIPAL_ID \
    --role "Search Service Contributor" \
    --scope $SEARCH_RESOURCE_ID \
    || echo "Role assignment already exists"

echo_step "Assigning Cosmos DB permissions..."
az cosmosdb sql role assignment create \
    --account-name indsolse-dev-db-okumlm \
    --resource-group $RESOURCE_GROUP \
    --scope "/" \
    --principal-id $BACKEND_PRINCIPAL_ID \
    --role-definition-id 00000000-0000-0000-0000-000000000002 \
    || echo "Role assignment already exists"

echo "✅ RBAC permissions assigned"

# ============================================================================
# Deployment Complete
# ============================================================================

echo_header "Deployment Complete! 🎉"
echo ""
echo "Backend API: https://$BACKEND_URL"
echo "Frontend UI: https://$FRONTEND_URL"
echo ""
echo "Next steps:"
echo "1. Test the backend health endpoint: https://$BACKEND_URL/api/health"
echo "2. Access the Streamlit UI: https://$FRONTEND_URL"
echo "3. Monitor logs with: az containerapp logs show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --follow"
echo ""
