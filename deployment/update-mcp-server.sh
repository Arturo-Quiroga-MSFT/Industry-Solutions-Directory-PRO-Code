#!/bin/bash

##############################################################################
# Update ISD MCP Server - Rebuild and redeploy
# Quick update script for iterative development
##############################################################################

set -e  # Exit on error

# Configuration
RESOURCE_GROUP="indsolse-dev-rg"
ACR_NAME="indsolsedevacr"
MCP_APP_NAME="indsolse-mcp-server"
MCP_IMAGE="isd-mcp-server:latest"

echo "=========================================="
echo "Updating ISD MCP Server"
echo "=========================================="
echo ""

# Build new image
echo "Building updated MCP server image..."
cd mcp-isd-server

az acr build \
    --registry $ACR_NAME \
    --image $MCP_IMAGE \
    --file Dockerfile \
    .

if [ $? -eq 0 ]; then
    echo "✅ Image built successfully"
else
    echo "❌ Failed to build image"
    exit 1
fi

cd ..

# Update container app
echo ""
echo "Updating container app..."

az containerapp update \
    --name $MCP_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --image "$ACR_NAME.azurecr.io/$MCP_IMAGE"

if [ $? -eq 0 ]; then
    echo "✅ Container app updated successfully"
else
    echo "❌ Failed to update container app"
    exit 1
fi

# Get URL
MCP_SERVER_URL=$(az containerapp show \
    --name $MCP_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn \
    -o tsv)

MCP_SERVER_URL="https://$MCP_SERVER_URL"

echo ""
echo "=========================================="
echo "Update Complete"
echo "=========================================="
echo ""
echo "MCP Server URL: $MCP_SERVER_URL"
echo ""
echo "Test health endpoint:"
echo "  curl $MCP_SERVER_URL/health"
echo ""
