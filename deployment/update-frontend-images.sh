#!/bin/bash

##############################################################################
# Rebuild Frontend Images with Correct Backend URLs
##############################################################################

set -e

# Configuration
RESOURCE_GROUP="indsolse-dev-rg"
ACR_NAME="indsolsedevacr"

# Backend URLs from deployed container apps
CUSTOMER_BACKEND_URL="https://isd-chat-customer-backend.redplant-675b33da.swedencentral.azurecontainerapps.io"
SELLER_BACKEND_URL="https://isd-chat-seller-backend.redplant-675b33da.swedencentral.azurecontainerapps.io"

echo "=========================================="
echo "Rebuilding Frontend Images"
echo "=========================================="

cd ../frontend-react

echo ""
echo "Building Customer Frontend..."
az acr build \
    --registry $ACR_NAME \
    --image isd-chat-frontend:customer \
    --build-arg VITE_API_URL=$CUSTOMER_BACKEND_URL \
    .

echo ""
echo "✅ Customer frontend built"

echo ""
echo "Building Seller Frontend..."
az acr build \
    --registry $ACR_NAME \
    --image isd-chat-frontend:seller \
    --build-arg VITE_API_URL=$SELLER_BACKEND_URL \
    .

echo ""
echo "✅ Seller frontend built"

cd ../deployment

echo ""
echo "=========================================="
echo "Updating Container Apps"
echo "=========================================="

echo ""
echo "Updating Customer Frontend..."
az containerapp update \
    --name isd-chat-customer-frontend \
    --resource-group $RESOURCE_GROUP \
    --image ${ACR_NAME}.azurecr.io/isd-chat-frontend:customer

echo "✅ Customer frontend updated"

echo ""
echo "Updating Seller Frontend..."
az containerapp update \
    --name isd-chat-seller-frontend \
    --resource-group $RESOURCE_GROUP \
    --image ${ACR_NAME}.azurecr.io/isd-chat-frontend:seller

echo "✅ Seller frontend updated"

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "🛡️  CUSTOMER MODE:"
echo "   Frontend: https://isd-chat-customer-frontend.redplant-675b33da.swedencentral.azurecontainerapps.io"
echo ""
echo "💾 SELLER MODE:"
echo "   Frontend: https://isd-chat-seller-frontend.redplant-675b33da.swedencentral.azurecontainerapps.io"
echo ""
