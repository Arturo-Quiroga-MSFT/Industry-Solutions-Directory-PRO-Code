#!/bin/bash
set -e

# Configuration
RESOURCE_GROUP="indsolse-dev-rg"
LOCATION="swedencentral"
COSMOS_DB_NAME="indsolse-dev-db-okumlm"
VNET_NAME="indsolse-dev-vnet"
SUBNET_NAME="endpoints-subnet"
ACA_SUBNET_NAME="aca-subnet"
PRIVATE_ENDPOINT_NAME="cosmos-private-endpoint"
PRIVATE_DNS_ZONE="privatelink.documents.azure.com"
SUBSCRIPTION_ID="7a28b21e-0d3e-4435-a686-d92889d4ee96"

echo "🔧 Setting up Private Endpoint for Cosmos DB..."

# Step 1: Create VNet with two subnets
echo ""
echo "📡 Step 1: Creating Virtual Network..."
az network vnet create \
  --resource-group $RESOURCE_GROUP \
  --name $VNET_NAME \
  --location $LOCATION \
  --address-prefixes 10.0.0.0/16 \
  --subnet-name $SUBNET_NAME \
  --subnet-prefixes 10.0.1.0/24

echo "✅ VNet created: $VNET_NAME"

# Step 2: Create subnet for Container Apps (will need to recreate ACA environment)
echo ""
echo "📡 Step 2: Creating Container Apps subnet..."
az network vnet subnet create \
  --resource-group $RESOURCE_GROUP \
  --vnet-name $VNET_NAME \
  --name $ACA_SUBNET_NAME \
  --address-prefixes 10.0.2.0/23

echo "✅ Container Apps subnet created"

# Step 3: Disable subnet private endpoint policies
echo ""
echo "🔒 Step 3: Configuring subnet for private endpoints..."
az network vnet subnet update \
  --resource-group $RESOURCE_GROUP \
  --vnet-name $VNET_NAME \
  --name $SUBNET_NAME \
  --disable-private-endpoint-network-policies true

echo "✅ Subnet configured"

# Step 4: Get Cosmos DB resource ID
echo ""
echo "🔍 Step 4: Getting Cosmos DB resource ID..."
COSMOS_RESOURCE_ID=$(az cosmosdb show \
  --resource-group $RESOURCE_GROUP \
  --name $COSMOS_DB_NAME \
  --query "id" -o tsv)

echo "✅ Found Cosmos DB: $COSMOS_RESOURCE_ID"

# Step 5: Create Private Endpoint
echo ""
echo "🔐 Step 5: Creating Private Endpoint..."
az network private-endpoint create \
  --resource-group $RESOURCE_GROUP \
  --name $PRIVATE_ENDPOINT_NAME \
  --location $LOCATION \
  --vnet-name $VNET_NAME \
  --subnet $SUBNET_NAME \
  --private-connection-resource-id $COSMOS_RESOURCE_ID \
  --group-id Sql \
  --connection-name cosmos-private-connection

echo "✅ Private Endpoint created"

# Step 6: Create Private DNS Zone
echo ""
echo "🌐 Step 6: Creating Private DNS Zone..."
az network private-dns zone create \
  --resource-group $RESOURCE_GROUP \
  --name $PRIVATE_DNS_ZONE

echo "✅ Private DNS Zone created"

# Step 7: Link DNS Zone to VNet
echo ""
echo "🔗 Step 7: Linking DNS Zone to VNet..."
az network private-dns link vnet create \
  --resource-group $RESOURCE_GROUP \
  --zone-name $PRIVATE_DNS_ZONE \
  --name cosmos-dns-link \
  --virtual-network $VNET_NAME \
  --registration-enabled false

echo "✅ DNS Zone linked"

# Step 8: Create DNS Zone Group (auto-registers private endpoint IP)
echo ""
echo "📝 Step 8: Creating DNS Zone Group..."
az network private-endpoint dns-zone-group create \
  --resource-group $RESOURCE_GROUP \
  --endpoint-name $PRIVATE_ENDPOINT_NAME \
  --name cosmos-dns-zone-group \
  --private-dns-zone $PRIVATE_DNS_ZONE \
  --zone-name sql

echo "✅ DNS Zone Group created"

# Step 9: Disable Cosmos DB public network access
echo ""
echo "🔒 Step 9: Disabling Cosmos DB public network access..."
az cosmosdb update \
  --resource-group $RESOURCE_GROUP \
  --name $COSMOS_DB_NAME \
  --public-network-access Disabled

echo "✅ Public network access disabled"

echo ""
echo "✨ Private Endpoint setup complete!"
echo ""
echo "⚠️  NEXT STEPS:"
echo "1. You need to recreate your Container Apps environment with VNet integration"
echo "2. Use the subnet: $ACA_SUBNET_NAME (10.0.2.0/23)"
echo "3. Then redeploy your Container Apps to the new environment"
echo ""
echo "Run: ./deployment/recreate-aca-with-vnet.sh"
