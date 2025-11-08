#!/bin/bash

##############################################################################
# Deploy v2.9 with Streaming Support - Full Deployment (Backend + Frontend)
##############################################################################

set -e  # Exit on error

# Configuration
RESOURCE_GROUP="indsolse-dev-rg"
ACR_NAME="indsolsedevacr"
BACKEND_APP_NAME="indsolse-dev-backend-v2-vnet"
FRONTEND_APP_NAME="indsolse-dev-frontend-v2-vnet"
BACKEND_IMAGE="industry-solutions-backend:v2.9"
FRONTEND_IMAGE="industry-solutions-frontend:v2.9"

echo "=========================================="
echo "Deploying v2.9 with Streaming Support"
echo "Backend + Frontend Full Deployment"
echo "=========================================="
echo ""
echo "Resource Group: $RESOURCE_GROUP"
echo "ACR: $ACR_NAME"
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

# Build backend image v2.9
echo "=========================================="
echo "Building Backend Docker Image v2.9"
echo "=========================================="
cd ../backend
az acr build \
    --registry $ACR_NAME \
    --image $BACKEND_IMAGE \
    --file Dockerfile \
    .

if [ $? -eq 0 ]; then
    echo "✅ Backend image v2.9 built successfully"
else
    echo "❌ Failed to build backend image"
    exit 1
fi

# Build frontend image v2.9
echo ""
echo "=========================================="
echo "Building Frontend Docker Image v2.9"
echo "=========================================="
cd ../frontend
az acr build \
    --registry $ACR_NAME \
    --image $FRONTEND_IMAGE \
    --file Dockerfile \
    .

if [ $? -eq 0 ]; then
    echo "✅ Frontend image v2.9 built successfully"
else
    echo "❌ Failed to build frontend image"
    exit 1
fi

# Update backend container app to v2.9
echo ""
echo "=========================================="
echo "Updating Backend Container App to v2.9"
echo "=========================================="

az containerapp update \
    --name $BACKEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --image "$ACR_NAME.azurecr.io/$BACKEND_IMAGE"

if [ $? -eq 0 ]; then
    echo "✅ Backend container app updated to v2.9 successfully"
else
    echo "❌ Failed to update backend container app"
    exit 1
fi

# Update frontend container app to v2.9
echo ""
echo "=========================================="
echo "Updating Frontend Container App to v2.9"
echo "=========================================="

az containerapp update \
    --name $FRONTEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --image "$ACR_NAME.azurecr.io/$FRONTEND_IMAGE"

if [ $? -eq 0 ]; then
    echo "✅ Frontend container app updated to v2.9 successfully"
else
    echo "❌ Failed to update frontend container app"
    exit 1
fi

# Get URLs
BACKEND_URL=$(az containerapp show \
    --name $BACKEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn \
    -o tsv)

FRONTEND_URL=$(az containerapp show \
    --name $FRONTEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn \
    -o tsv)

BACKEND_URL="https://$BACKEND_URL"
FRONTEND_URL="https://$FRONTEND_URL"

# Summary
echo ""
echo "=========================================="
echo "Deployment Complete - v2.9"
echo "=========================================="
echo ""
echo "✅ Backend v2.9: $BACKEND_URL"
echo "✅ Frontend v2.9: $FRONTEND_URL"
echo ""
echo "New Features in v2.9:"
echo "  🚀 Real-time streaming responses (SSE)"
echo "  🚀 Token-by-token response generation"
echo "  🚀 Improved user experience with live updates"
echo "  🚀 Visual streaming cursor in frontend"
echo "  🚀 New endpoint: /api/chat/stream"
echo ""
echo "Testing:"
echo "  1. Open frontend: $FRONTEND_URL"
echo "  2. Ask a question and watch it stream in real-time!"
echo ""
echo "API Testing:"
echo "  Backend health: curl $BACKEND_URL/api/health"
echo "  Streaming: curl -N $BACKEND_URL/api/chat/stream \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"message\": \"What solutions are available for healthcare AI?\", \"session_id\": \"test-v2.9-stream\"}'"
echo ""
