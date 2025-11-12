#!/bin/bash
# Quick Rollback Script for Gradio Frontend
# Usage: ./ROLLBACK.sh [version]
# Example: ./ROLLBACK.sh v1.0-baseline
# If no version specified, defaults to v1.0-baseline

set -e

VERSION=${1:-v1.0-baseline}
CONTAINER_APP="indsolse-dev-frontend-gradio"
RESOURCE_GROUP="indsolse-dev-rg"
ACR_NAME="indsolsedevacr"
IMAGE_REPO="industry-solutions-frontend-gradio"

echo "🔄 Rolling back Gradio frontend to version: $VERSION"
echo "================================================"

# Get backend FQDN
echo "📡 Fetching backend FQDN..."
BACKEND_FQDN=$(az containerapp show \
  --name indsolse-dev-backend-v2-vnet \
  --resource-group indsolse-dev-rg \
  --query properties.configuration.ingress.fqdn -o tsv)

echo "   Backend URL: https://$BACKEND_FQDN"

# Update container app with specified version
echo ""
echo "🚀 Updating Container App to $VERSION..."
az containerapp update \
  --name $CONTAINER_APP \
  --resource-group $RESOURCE_GROUP \
  --image $ACR_NAME.azurecr.io/$IMAGE_REPO:$VERSION \
  --set-env-vars "BACKEND_API_URL=https://$BACKEND_FQDN"

# Force restart
echo ""
echo "🔄 Forcing container restart..."
CURRENT_REVISION=$(az containerapp revision list \
  --name $CONTAINER_APP \
  --resource-group $RESOURCE_GROUP \
  --query '[0].name' -o tsv)

az containerapp revision restart \
  --name $CONTAINER_APP \
  --resource-group $RESOURCE_GROUP \
  --revision $CURRENT_REVISION

echo ""
echo "✅ Rollback complete!"
echo ""
echo "📋 Current status:"
az containerapp show \
  --name $CONTAINER_APP \
  --resource-group $RESOURCE_GROUP \
  --query '{name:name,fqdn:properties.configuration.ingress.fqdn,image:properties.template.containers[0].image}' \
  -o table

echo ""
echo "🌐 Access your app at:"
APP_URL=$(az containerapp show \
  --name $CONTAINER_APP \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn -o tsv)
echo "   https://$APP_URL"
echo ""
echo "💡 Test thoroughly before proceeding!"
