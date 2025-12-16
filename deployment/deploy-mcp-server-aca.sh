#!/bin/bash

##############################################################################
# Deploy ISD MCP Server to Azure Container Apps
# Creates a new ACA environment and deploys the MCP server
# Compatible with Azure AI Foundry Agent Service
##############################################################################

set -e  # Exit on error

# Configuration
RESOURCE_GROUP="indsolse-dev-rg"
LOCATION="swedencentral"
ACR_NAME="indsolsedevacr"
MCP_ENVIRONMENT_NAME="indsolse-mcp-env"
MCP_APP_NAME="indsolse-mcp-server"
MCP_IMAGE="isd-mcp-server:latest"

echo "=========================================="
echo "ISD MCP Server - Azure Container Apps"
echo "=========================================="
echo ""
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "ACR: $ACR_NAME"
echo "MCP Environment: $MCP_ENVIRONMENT_NAME"
echo "MCP App: $MCP_APP_NAME"
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
ACCOUNT_NAME=$(az account show --query user.name -o tsv)
echo "Subscription: $SUBSCRIPTION_ID"
echo "Account: $ACCOUNT_NAME"
echo ""

# Check if resource group exists
echo "Checking resource group..."
if ! az group show --name $RESOURCE_GROUP &> /dev/null; then
    echo "❌ Resource group $RESOURCE_GROUP does not exist"
    echo "Creating resource group..."
    az group create --name $RESOURCE_GROUP --location $LOCATION
    echo "✅ Resource group created"
else
    echo "✅ Resource group exists"
fi
echo ""

# Build MCP server image
echo "=========================================="
echo "Building MCP Server Docker Image"
echo "=========================================="
cd mcp-isd-server

echo "Building image: $MCP_IMAGE"
az acr build \
    --registry $ACR_NAME \
    --image $MCP_IMAGE \
    --file Dockerfile \
    .

if [ $? -eq 0 ]; then
    echo "✅ MCP server image built successfully"
else
    echo "❌ Failed to build MCP server image"
    exit 1
fi

cd ..

# Create Container Apps environment for MCP
echo ""
echo "=========================================="
echo "Creating Container Apps Environment"
echo "=========================================="

# Check if environment already exists
if az containerapp env show --name $MCP_ENVIRONMENT_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo "✅ Environment $MCP_ENVIRONMENT_NAME already exists"
else
    echo "Creating new environment: $MCP_ENVIRONMENT_NAME"
    az containerapp env create \
        --name $MCP_ENVIRONMENT_NAME \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION

    if [ $? -eq 0 ]; then
        echo "✅ Container Apps environment created successfully"
    else
        echo "❌ Failed to create Container Apps environment"
        exit 1
    fi
fi

# Deploy MCP server container app
echo ""
echo "=========================================="
echo "Deploying MCP Server Container App"
echo "=========================================="

az containerapp create \
    --name $MCP_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --environment $MCP_ENVIRONMENT_NAME \
    --image "$ACR_NAME.azurecr.io/$MCP_IMAGE" \
    --registry-server "$ACR_NAME.azurecr.io" \
    --registry-identity system \
    --target-port 8080 \
    --ingress external \
    --min-replicas 1 \
    --max-replicas 5 \
    --cpu 0.5 \
    --memory 1Gi \
    --system-assigned

if [ $? -eq 0 ]; then
    echo "✅ MCP server container app created successfully"
else
    echo "❌ Failed to create MCP server container app"
    exit 1
fi

# Get MCP server URL
MCP_SERVER_URL=$(az containerapp show \
    --name $MCP_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn \
    -o tsv)

MCP_SERVER_URL="https://$MCP_SERVER_URL"

# Get managed identity principal ID for RBAC (if needed in future)
MCP_PRINCIPAL_ID=$(az containerapp show \
    --name $MCP_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query identity.principalId \
    -o tsv)

echo ""
echo "=========================================="
echo "Deployment Complete - MCP Server"
echo "=========================================="
echo ""
echo "🚀 MCP Server URL: $MCP_SERVER_URL"
echo "🔑 Principal ID: $MCP_PRINCIPAL_ID"
echo ""
echo "📋 Available Endpoints:"
echo "  Health:        $MCP_SERVER_URL/health"
echo "  Info:          $MCP_SERVER_URL/"
echo "  Tools List:    $MCP_SERVER_URL/tools"
echo "  MCP Protocol:  $MCP_SERVER_URL/mcp"
echo ""
echo "🧪 Test Commands:"
echo "  # Health check"
echo "  curl $MCP_SERVER_URL/health"
echo ""
echo "  # List industries"
echo "  curl -X POST $MCP_SERVER_URL/tools/list_industries"
echo ""
echo "  # Get solutions by industry"
echo "  curl -X POST $MCP_SERVER_URL/tools/get_solutions_by_industry \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"industry\": \"Managing Risk and Compliance\"}'"
echo ""
echo "🔗 Azure AI Foundry Integration:"
echo "  1. Go to https://ai.azure.com"
echo "  2. Navigate to your project"
echo "  3. Go to Build → Tools → Add Custom Tool"
echo "  4. Select 'Model Context Protocol'"
echo "  5. Configure:"
echo "     - Name: ISD Solutions Directory"
echo "     - Remote MCP Server endpoint: $MCP_SERVER_URL/mcp"
echo "     - Server Label: isd-server"
echo "     - Authentication: (configure as needed)"
echo ""
echo "📖 Next Steps:"
echo "  1. Test the MCP server endpoints"
echo "  2. Connect to Azure AI Foundry Agent Service"
echo "  3. Test with AI agent queries"
echo "  4. Monitor performance and logs"
echo ""
echo "🔍 Monitoring:"
echo "  # View logs"
echo "  az containerapp logs show --name $MCP_APP_NAME --resource-group $RESOURCE_GROUP --follow"
echo ""
echo "  # View metrics"
echo "  az monitor metrics list --resource \"/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.App/containerApps/$MCP_APP_NAME\""
echo ""

# Save deployment info to file
DEPLOYMENT_INFO_FILE="deployment/mcp-deployment-info.json"
cat > $DEPLOYMENT_INFO_FILE << EOF
{
  "deployment_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "resource_group": "$RESOURCE_GROUP",
  "location": "$LOCATION",
  "environment": "$MCP_ENVIRONMENT_NAME",
  "app_name": "$MCP_APP_NAME",
  "image": "$ACR_NAME.azurecr.io/$MCP_IMAGE",
  "mcp_server_url": "$MCP_SERVER_URL",
  "principal_id": "$MCP_PRINCIPAL_ID",
  "subscription_id": "$SUBSCRIPTION_ID",
  "endpoints": {
    "health": "$MCP_SERVER_URL/health",
    "info": "$MCP_SERVER_URL/",
    "tools": "$MCP_SERVER_URL/tools",
    "mcp_protocol": "$MCP_SERVER_URL/mcp"
  }
}
EOF

echo "💾 Deployment info saved to: $DEPLOYMENT_INFO_FILE"
echo ""
