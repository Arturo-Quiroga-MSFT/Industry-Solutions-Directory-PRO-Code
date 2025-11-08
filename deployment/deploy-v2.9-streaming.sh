#!/bin/bash

##############################################################################
# Deploy v2.9 with Streaming Support
# This script updates the existing v2.8 backend to v2.9 with streaming
##############################################################################

set -e  # Exit on error

# Configuration
RESOURCE_GROUP="indsolse-dev-rg"
ACR_NAME="indsolsedevacr"
BACKEND_APP_NAME="indsolse-dev-backend-v2-vnet"
BACKEND_IMAGE="industry-solutions-backend:v2.9"

echo "=========================================="
echo "Deploying v2.9 with Streaming Support"
echo "=========================================="
echo ""
echo "Resource Group: $RESOURCE_GROUP"
echo "ACR: $ACR_NAME"
echo "Backend App: $BACKEND_APP_NAME"
echo "Image: $BACKEND_IMAGE"
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

# Get backend URL
BACKEND_URL=$(az containerapp show \
    --name $BACKEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn \
    -o tsv)

BACKEND_URL="https://$BACKEND_URL"

# Summary
echo ""
echo "=========================================="
echo "Deployment Complete - v2.9"
echo "=========================================="
echo ""
echo "Backend v2.9 URL: $BACKEND_URL"
echo ""
echo "New Features in v2.9:"
echo "  ✅ Real-time streaming responses (SSE)"
echo "  ✅ Token-by-token response generation"
echo "  ✅ Improved user experience"
echo "  ✅ New endpoint: /api/chat/stream"
echo ""
echo "Testing:"
echo "  Non-streaming: curl -X POST $BACKEND_URL/api/chat \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"message\": \"What solutions are available for healthcare AI?\", \"conversation_id\": \"test-v2.9\"}'"
echo ""
echo "  Streaming: curl -N $BACKEND_URL/api/chat/stream \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"message\": \"What solutions are available for healthcare AI?\", \"conversation_id\": \"test-v2.9-stream\"}'"
echo ""
echo "Frontend URL (automatically using new backend):"
echo "  https://indsolse-dev-frontend-vnet.icyplant-dd879251.swedencentral.azurecontainerapps.io"
echo ""
