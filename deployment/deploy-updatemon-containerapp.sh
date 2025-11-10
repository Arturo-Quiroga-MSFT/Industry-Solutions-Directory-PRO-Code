#!/bin/bash
set -e

# Configuration
RESOURCE_GROUP="indsolse-dev-rg"
LOCATION="swedencentral"
ACR_NAME="indsolsedevacr"
IMAGE_NAME="update-monitor"
IMAGE_TAG="latest"
CONTAINER_APP_ENV="indsolse-dev-env"
SEARCH_SERVICE="indsolse-dev-srch-okumlm"
NOTIFICATION_EMAIL="arturo.quiroga@microsoft.com"

echo "=== Building and Deploying Update Monitor Container App ==="

# Step 1: Build image in ACR (no local Docker needed)
echo ""
echo "Step 1: Building Docker image in Azure Container Registry..."
cd ../azure-functions/update-monitor

az acr build \
  --registry ${ACR_NAME} \
  --image ${IMAGE_NAME}:${IMAGE_TAG} \
  --file Dockerfile \
  .

# Step 2: Deploy infrastructure
echo ""
echo "Step 2: Deploying Container App infrastructure..."
cd ../../infra

# Prompt for SendGrid API key (secure)
echo ""
read -sp "Enter SendGrid API Key: " SENDGRID_KEY
echo ""

az deployment group create \
  --resource-group ${RESOURCE_GROUP} \
  --template-file container-app-monitor.bicep \
  --parameters \
    location=${LOCATION} \
    environment=dev \
    baseName=indsolse \
    searchServiceName=${SEARCH_SERVICE} \
    notificationEmail="${NOTIFICATION_EMAIL}" \
    sendGridApiKey="${SENDGRID_KEY}" \
    containerAppEnvName=${CONTAINER_APP_ENV} \
    containerRegistryName=${ACR_NAME} \
    containerImage="${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${IMAGE_TAG}"

echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "Container App URL:"
az containerapp show \
  --name indsolse-dev-updatemon-aca \
  --resource-group ${RESOURCE_GROUP} \
  --query properties.configuration.ingress.fqdn \
  -o tsv

echo ""
echo "Test the endpoint:"
echo "curl -X POST https://\$(az containerapp show --name indsolse-dev-updatemon-aca --resource-group ${RESOURCE_GROUP} --query properties.configuration.ingress.fqdn -o tsv)/api/update-check"
