#!/bin/bash

##############################################################################
# Deploy Gradio Frontend to Azure Container Apps
# Deploys a new Gradio-based frontend alongside existing Streamlit frontend
##############################################################################

set -e  # Exit on error

# Configuration
RESOURCE_GROUP="indsolse-dev-rg"
LOCATION="swedencentral"
ACR_NAME="indsolsedevacr"
ENVIRONMENT_NAME="indsolse-dev-env"
GRADIO_APP_NAME="indsolse-dev-frontend-gradio"
GRADIO_IMAGE="industry-solutions-frontend-gradio:latest"
BACKEND_APP_NAME="indsolse-dev-backend-v2-vnet"  # Using VNet backend to avoid Cosmos DB firewall issues

echo "=========================================="
echo "Gradio Frontend Deployment"
echo "=========================================="
echo ""
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "ACR: $ACR_NAME"
echo "Environment: $ENVIRONMENT_NAME"
echo "Gradio App: $GRADIO_APP_NAME"
echo "Backend App: $BACKEND_APP_NAME"
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

# Get backend URL
echo "Getting backend URL..."
BACKEND_URL=$(az containerapp show \
    --name $BACKEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn \
    -o tsv 2>/dev/null || echo "")

if [ -z "$BACKEND_URL" ]; then
    echo "❌ Backend app not found: $BACKEND_APP_NAME"
    echo "Please deploy the backend first or update BACKEND_APP_NAME"
    exit 1
fi

BACKEND_URL="https://$BACKEND_URL"
echo "✅ Backend URL: $BACKEND_URL"
echo ""

# Step 1: Build and push Docker image
echo "=========================================="
echo "Step 1: Build and Push Docker Image"
echo "=========================================="

cd "$(dirname "$0")/../frontend-gradio"

echo "Building Docker image..."
az acr build \
    --registry $ACR_NAME \
    --image $GRADIO_IMAGE \
    --file Dockerfile \
    .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built and pushed successfully"
else
    echo "❌ Failed to build Docker image"
    exit 1
fi

echo ""

# Step 2: Deploy Gradio frontend container app
echo "=========================================="
echo "Step 2: Deploy Gradio Frontend"
echo "=========================================="

# Check if app already exists
APP_EXISTS=$(az containerapp show \
    --name $GRADIO_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query name -o tsv 2>/dev/null || echo "")

if [ -n "$APP_EXISTS" ]; then
    echo "⚠️  Container app already exists. Updating..."
    
    az containerapp update \
        --name $GRADIO_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --image "$ACR_NAME.azurecr.io/$GRADIO_IMAGE" \
        --set-env-vars \
            BACKEND_API_URL="$BACKEND_URL"
    
    if [ $? -eq 0 ]; then
        echo "✅ Gradio frontend updated successfully"
    else
        echo "❌ Failed to update Gradio frontend"
        exit 1
    fi
else
    echo "Creating new Gradio frontend container app..."
    
    az containerapp create \
        --name $GRADIO_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --environment $ENVIRONMENT_NAME \
        --image "$ACR_NAME.azurecr.io/$GRADIO_IMAGE" \
        --registry-server "$ACR_NAME.azurecr.io" \
        --registry-identity system \
        --target-port 7860 \
        --ingress external \
        --min-replicas 1 \
        --max-replicas 3 \
        --cpu 0.5 \
        --memory 1Gi \
        --env-vars \
            BACKEND_API_URL="$BACKEND_URL" \
        --system-assigned
    
    if [ $? -eq 0 ]; then
        echo "✅ Gradio frontend created successfully"
    else
        echo "❌ Failed to create Gradio frontend"
        exit 1
    fi
fi

# Get Gradio frontend URL
GRADIO_URL=$(az containerapp show \
    --name $GRADIO_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn \
    -o tsv)

GRADIO_URL="https://$GRADIO_URL"
echo "Gradio Frontend URL: $GRADIO_URL"

# Summary
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "🎉 Gradio Frontend: $GRADIO_URL"
echo "🔗 Backend API: $BACKEND_URL"
echo ""
echo "Other Frontends:"
echo "  📊 Streamlit v1: https://indsolse-dev-frontend.redplant-675b33da.swedencentral.azurecontainerapps.io"
echo "  📊 Streamlit v2: Check 'indsolse-dev-frontend-v2' if deployed"
echo ""
echo "Next Steps:"
echo "  1. Open $GRADIO_URL in your browser"
echo "  2. Test chat functionality"
echo "  3. Compare with Streamlit UI"
echo "  4. Choose your preferred interface"
echo ""
echo "Health Check:"
echo "  curl $BACKEND_URL/api/health"
echo ""
