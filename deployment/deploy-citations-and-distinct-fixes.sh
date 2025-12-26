#!/bin/bash

##############################################################################
# Deploy Citations + DISTINCT Fixes to Azure Container Apps
# 
# Changes deployed:
# - Frontend: SQL formatter + Citations display
# - Backend: DISTINCT enforcement + Citations generation
##############################################################################

set -e  # Exit on error

# Configuration
RESOURCE_GROUP="indsolse-dev-rg"
ACR_NAME="indsolsedevacr"
FRONTEND_APP_NAME="isd-chat-seller-frontend"
BACKEND_APP_NAME="isd-chat-seller-backend"
IMAGE_TAG="v2.5-citations-distinct-fix"

echo "=========================================="
echo "Deploying Citations + DISTINCT Fixes"
echo "=========================================="
echo ""
echo "Resource Group: $RESOURCE_GROUP"
echo "ACR: $ACR_NAME"
echo "Frontend App: $FRONTEND_APP_NAME"
echo "Backend App: $BACKEND_APP_NAME"
echo "Image Tag: $IMAGE_TAG"
echo ""
echo "Changes being deployed:"
echo "  ✨ Frontend: SQL formatter for readable queries"
echo "  📚 Frontend: Copilot-style citations display"
echo "  🎯 Backend: DISTINCT enforcement (no more 328 duplicates!)"
echo "  📖 Backend: Citations generation in insights"
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

# Build and push backend image
echo "=========================================="
echo "Step 1: Building Backend Docker Image"
echo "=========================================="
cd ../frontend-react/backend
az acr build \
    --registry $ACR_NAME \
    --image "industry-solutions-backend:$IMAGE_TAG" \
    --file Dockerfile \
    .

if [ $? -eq 0 ]; then
    echo "✅ Backend image built successfully"
else
    echo "❌ Failed to build backend image"
    exit 1
fi

# Build and push frontend image
echo ""
echo "=========================================="
echo "Step 2: Building Frontend Docker Image"
echo "=========================================="
cd ../../frontend-react

# Get backend URL for build argument
BACKEND_URL="https://$BACKEND_APP_NAME.redplant-675b33da.swedencentral.azurecontainerapps.io"
echo "Building frontend with VITE_API_URL=$BACKEND_URL"

az acr build \
    --registry $ACR_NAME \
    --image "industry-solutions-frontend:$IMAGE_TAG" \
    --file Dockerfile \
    --build-arg VITE_API_URL=$BACKEND_URL \
    .

if [ $? -eq 0 ]; then
    echo "✅ Frontend image built successfully"
else
    echo "❌ Failed to build frontend image"
    exit 1
fi

cd ../deployment

# Update backend container app
echo ""
echo "=========================================="
echo "Step 3: Updating Backend Container App"
echo "=========================================="

az containerapp update \
    --name $BACKEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --image "$ACR_NAME.azurecr.io/industry-solutions-backend:$IMAGE_TAG"

if [ $? -eq 0 ]; then
    echo "✅ Backend container app updated successfully"
else
    echo "❌ Failed to update backend container app"
    exit 1
fi

# Update frontend container app
echo ""
echo "=========================================="
echo "Step 4: Updating Frontend Container App"
echo "=========================================="

az containerapp update \
    --name $FRONTEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --image "$ACR_NAME.azurecr.io/industry-solutions-frontend:$IMAGE_TAG"

if [ $? -eq 0 ]; then
    echo "✅ Frontend container app updated successfully"
else
    echo "❌ Failed to update frontend container app"
    exit 1
fi

# Get URLs and status
FRONTEND_URL=$(az containerapp show \
    --name $FRONTEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn \
    -o tsv)

BACKEND_URL=$(az containerapp show \
    --name $BACKEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn \
    -o tsv)

FRONTEND_URL="https://$FRONTEND_URL"
BACKEND_URL="https://$BACKEND_URL"

FRONTEND_REVISION=$(az containerapp revision list \
    --name $FRONTEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "[0].name" \
    -o tsv)

BACKEND_REVISION=$(az containerapp revision list \
    --name $BACKEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "[0].name" \
    -o tsv)

echo ""
echo "=========================================="
echo "🎉 Deployment Complete!"
echo "=========================================="
echo ""
echo "Frontend URL: $FRONTEND_URL"
echo "Backend URL: $BACKEND_URL"
echo ""
echo "Latest Revisions:"
echo "  Frontend: $FRONTEND_REVISION"
echo "  Backend: $BACKEND_REVISION"
echo ""
echo "✨ New Features Deployed:"
echo ""
echo "1. SQL Formatting"
echo "   - Queries now display with proper line breaks and indentation"
echo "   - Much easier to read and debug"
echo ""
echo "2. Copilot-Style Citations"
echo "   - AI insights now include [1], [2], [3] citation badges"
echo "   - Click citations to jump to source data in table"
echo "   - Shows which solutions support each key finding"
echo ""
echo "3. DISTINCT Enforcement (MAJOR FIX!)"
echo "   - Fixed: 'Adastra agentic AI' query returned 328 duplicates ❌"
echo "   - Now: Returns ~88 legitimate unique solutions ✅"
echo "   - All SQL queries now properly deduplicate results"
echo ""
echo "4. Enhanced SQL Generation"
echo "   - Breakdown queries return individual solutions (not just counts)"
echo "   - Sellers can see WHAT solutions exist, not just HOW MANY"
echo "   - Better handling of 'detailed breakdown' requests"
echo ""
echo "📋 Test Questions (from Will's feedback):"
echo "   1. What financial services solutions help with risk management?"
echo "   2. What agent-based applications exist in the Solutions Directory?"
echo "   3. Provide a detailed breakdown of which industries have Adastra's agentic AI offerings"
echo ""
echo "🧪 Testing Steps:"
echo "   1. Open: $FRONTEND_URL"
echo "   2. Clear browser cache (Cmd+Shift+R or Ctrl+Shift+R)"
echo "   3. Ask Will's test questions above"
echo "   4. Verify:"
echo "      - Citations appear in insights section"
echo "      - SQL tab shows formatted queries"
echo "      - Query 3 returns ~88 results (not 328!)"
echo "      - Tables show solution names + descriptions"
echo ""
echo "📊 Monitor Logs:"
echo "  Frontend: az containerapp logs show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --follow"
echo "  Backend: az containerapp logs show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --follow"
echo ""
echo "🔄 Rollback if needed:"
echo "  az containerapp revision list --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP"
echo "  az containerapp revision activate --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --revision <previous-revision>"
echo ""
echo "  az containerapp revision list --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP"
echo "  az containerapp revision activate --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --revision <previous-revision>"
echo ""
