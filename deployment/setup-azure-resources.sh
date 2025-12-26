#!/bin/bash

# Azure Resource Setup for ISD Chat Dual-Mode Deployment
# This script creates all necessary Azure resources

set -e

echo "=========================================="
echo "Azure Resource Setup for ISD Chat"
echo "=========================================="

# Configuration
RESOURCE_GROUP="indsolse-dev-rg"
LOCATION="swedencentral"
ACR_NAME="indsolsedevacr"
ENVIRONMENT_NAME="indsolse-dev-env"
LOG_ANALYTICS_WORKSPACE="indsolse-dev-logs"

echo ""
echo "✓ Creating Resource Group..."
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION \
  --output table

echo ""
echo "✓ Creating Container Registry..."
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true \
  --location $LOCATION \
  --output table

echo ""
echo "✓ Creating Log Analytics Workspace..."
az monitor log-analytics workspace create \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $LOG_ANALYTICS_WORKSPACE \
  --location $LOCATION \
  --output table

# Get the workspace ID and key
WORKSPACE_ID=$(az monitor log-analytics workspace show \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $LOG_ANALYTICS_WORKSPACE \
  --query customerId \
  --output tsv)

WORKSPACE_KEY=$(az monitor log-analytics workspace get-shared-keys \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $LOG_ANALYTICS_WORKSPACE \
  --query primarySharedKey \
  --output tsv)

echo ""
echo "✓ Creating Container Apps Environment..."
az containerapp env create \
  --name $ENVIRONMENT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --logs-workspace-id $WORKSPACE_ID \
  --logs-workspace-key $WORKSPACE_KEY \
  --output table

echo ""
echo "=========================================="
echo "✅ Azure Resources Created Successfully!"
echo "=========================================="
echo ""
echo "Resource Group: $RESOURCE_GROUP"
echo "Container Registry: $ACR_NAME"
echo "Container Apps Environment: $ENVIRONMENT_NAME"
echo "Location: $LOCATION"
echo ""
echo "Next step: Run ./deploy-dual-mode.sh to deploy both customer and seller modes"
echo "=========================================="
