#!/bin/bash

##############################################################################
# Update Frontend Container App with New UI
# This script rebuilds and deploys the updated frontend to ACA with VNet
##############################################################################

set -e  # Exit on error

# Configuration
RESOURCE_GROUP="indsolse-dev-rg"
ACR_NAME="indsolsedevacr"
FRONTEND_APP_NAME="indsolse-dev-frontend-v2-vnet"
FRONTEND_IMAGE_TAG="v2.3-enhanced-ui"

echo "=========================================="
echo "Updating Frontend with Enhanced UI"
echo "=========================================="
echo ""
echo "Resource Group: $RESOURCE_GROUP"
echo "ACR: $ACR_NAME"
echo "Frontend App: $FRONTEND_APP_NAME"
echo "Image Tag: $FRONTEND_IMAGE_TAG"
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

# Check if container app exists
echo "Checking if frontend app exists..."
if ! az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo "❌ Frontend app '$FRONTEND_APP_NAME' not found"
    echo "Available options:"
    echo "  1. Deploy with deploy-aca-v2.sh first"
    echo "  2. Or change FRONTEND_APP_NAME to 'indsolse-dev-frontend' for v1"
    exit 1
fi

echo "✅ Frontend app found"
echo ""

# Build frontend image with new UI
echo "=========================================="
echo "Building Frontend Docker Image"
echo "=========================================="
cd frontend
az acr build \
    --registry $ACR_NAME \
    --image "industry-solutions-frontend:$FRONTEND_IMAGE_TAG" \
    --file Dockerfile \
    .

if [ $? -eq 0 ]; then
    echo "✅ Frontend image built successfully"
else
    echo "❌ Failed to build frontend image"
    exit 1
fi

cd ..

# Update the container app with new image
echo ""
echo "=========================================="
echo "Updating Frontend Container App"
echo "=========================================="

az containerapp update \
    --name $FRONTEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --image "$ACR_NAME.azurecr.io/industry-solutions-frontend:$FRONTEND_IMAGE_TAG"

if [ $? -eq 0 ]; then
    echo "✅ Frontend container app updated successfully"
else
    echo "❌ Failed to update frontend container app"
    exit 1
fi

# Get frontend URL
FRONTEND_URL=$(az containerapp show \
    --name $FRONTEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn \
    -o tsv)

FRONTEND_URL="https://$FRONTEND_URL"

# Get revision status
LATEST_REVISION=$(az containerapp revision list \
    --name $FRONTEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "[0].name" \
    -o tsv)

echo ""
echo "=========================================="
echo "Update Complete!"
echo "=========================================="
echo ""
echo "Frontend URL: $FRONTEND_URL"
echo "Latest Revision: $LATEST_REVISION"
echo ""
echo "New UI Features:"
echo "  ✨ Microsoft branding and logo"
echo "  🎨 Gradient backgrounds and modern styling"
echo "  📸 Welcome screen with imagery"
echo "  🎯 Visual icons for solutions"
echo "  💫 Enhanced industry category icons"
echo "  🌈 Professional color scheme (Azure blue/purple)"
echo ""
echo "Next Steps:"
echo "  1. Open the app: $FRONTEND_URL"
echo "  2. Clear browser cache if needed (Ctrl+Shift+R)"
echo "  3. Verify the new UI elements"
echo ""
echo "Monitor deployment:"
echo "  az containerapp logs show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --follow"
echo ""
echo "Rollback if needed:"
echo "  az containerapp revision list --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP"
echo "  az containerapp revision activate --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --revision <previous-revision-name>"
echo ""

