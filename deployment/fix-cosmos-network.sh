#!/bin/bash

# Script to fix Cosmos DB network settings
# Run this daily if Azure Policy is resetting public network access

set -e

# Configuration
RESOURCE_GROUP="indsolse-dev-rg"
COSMOS_ACCOUNT="indsolse-dev-db-okumlm"

# IP addresses that need access
# 24.226.125.69 - Your laptop
# 9.223.246.165 - V1 apps (indsolse-dev-backend)
# 74.241.205.78 - V2 apps initial (indsolse-dev-backend-v2)
# 20.240.37.231 - V2 apps after restart
# 74.241.211.241 - V2 apps after v2.1 revision deployment
IP_RANGE_FILTER="24.226.125.69,9.223.246.165,74.241.205.78,20.240.37.231,74.241.211.241"

echo "=================================================="
echo "Fixing Cosmos DB Network Configuration"
echo "=================================================="
echo ""
echo "Resource Group: $RESOURCE_GROUP"
echo "Cosmos Account: $COSMOS_ACCOUNT"
echo ""

# Check current status
echo "Checking current network configuration..."
CURRENT_CONFIG=$(az cosmosdb show \
    --name $COSMOS_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --query "{PublicAccess:publicNetworkAccess, IpRules:ipRules[].ipAddressOrRange}" \
    -o json)

echo "Current Configuration:"
echo "$CURRENT_CONFIG"
echo ""

# Enable public network access and update firewall rules
echo "Enabling public network access and updating firewall rules..."
az cosmosdb update \
    --name $COSMOS_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --public-network-access Enabled \
    --ip-range-filter "$IP_RANGE_FILTER"

echo ""
echo "✅ Update complete!"
echo ""

# Verify the changes
echo "Verifying new configuration..."
UPDATED_CONFIG=$(az cosmosdb show \
    --name $COSMOS_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --query "{PublicAccess:publicNetworkAccess, IpRules:ipRules[].ipAddressOrRange}" \
    -o json)

echo "Updated Configuration:"
echo "$UPDATED_CONFIG"
echo ""

# Check if v2 backend is healthy
echo "Checking v2 backend health..."
BACKEND_V2_URL="https://indsolse-dev-backend-v2.redplant-675b33da.swedencentral.azurecontainerapps.io/api/health"

# Wait a few seconds for container to restart if needed
sleep 5

HEALTH_STATUS=$(curl -s -w "\n%{http_code}" "$BACKEND_V2_URL" 2>/dev/null | tail -n 1)

if [ "$HEALTH_STATUS" = "200" ]; then
    echo "✅ V2 Backend is healthy!"
    curl -s "$BACKEND_V2_URL" | jq .
else
    echo "⚠️  V2 Backend returned HTTP $HEALTH_STATUS"
    echo "   The container may need a few more seconds to restart."
    echo "   Check logs: az containerapp logs show --name indsolse-dev-backend-v2 --resource-group $RESOURCE_GROUP --tail 50"
fi

echo ""
echo "=================================================="
echo "Script completed at $(date)"
echo "=================================================="
