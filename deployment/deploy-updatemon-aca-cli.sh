#!/bin/bash
set -e

# Configuration
RESOURCE_GROUP="indsolse-dev-rg"
LOCATION="swedencentral"
ACR_NAME="indsolsedevacr"
IMAGE_NAME="update-monitor"
IMAGE_TAG="latest"
CONTAINER_APP_NAME="indsolse-dev-updatemon-aca"
CONTAINER_APP_ENV="indsolse-dev-env"
SEARCH_SERVICE="indsolse-dev-srch-okumlm"
NOTIFICATION_EMAIL="arturo.quiroga@microsoft.com"

echo "=== Building and Deploying Update Monitor Container App ==="

# Step 1: Build in ACR
echo ""
echo "Step 1: Building Docker image in ACR..."
cd ../azure-functions/update-monitor

az acr build \
  --registry ${ACR_NAME} \
  --image ${IMAGE_NAME}:${IMAGE_TAG} \
  --file Dockerfile \
  .

# Step 2: Get SendGrid API key
echo ""
read -sp "Enter SendGrid API Key: " SENDGRID_KEY
echo ""

# Step 3: Get Search API key
echo ""
echo "Step 2: Getting Search Service API key..."
SEARCH_API_KEY=$(az search admin-key show \
  --resource-group ${RESOURCE_GROUP} \
  --service-name ${SEARCH_SERVICE} \
  --query primaryKey -o tsv)

# Step 4: Create Container App
echo ""
echo "Step 3: Creating Container App..."
az containerapp create \
  --name ${CONTAINER_APP_NAME} \
  --resource-group ${RESOURCE_GROUP} \
  --environment ${CONTAINER_APP_ENV} \
  --image ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${IMAGE_TAG} \
  --registry-server ${ACR_NAME}.azurecr.io \
  --registry-identity system \
  --target-port 8080 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 1 \
  --cpu 0.5 \
  --memory 1Gi \
  --secrets \
    sendgrid-api-key="${SENDGRID_KEY}" \
    search-api-key="${SEARCH_API_KEY}" \
  --env-vars \
    AZURE_SEARCH_SERVICE=${SEARCH_SERVICE} \
    AZURE_SEARCH_INDEX=partner-solutions-integrated \
    AZURE_SEARCH_KEY=secretref:search-api-key \
    NOTIFICATION_EMAIL_TO="${NOTIFICATION_EMAIL}" \
    NOTIFICATION_EMAIL_FROM=noreply@indsolse.com \
    SENDGRID_API_KEY=secretref:sendgrid-api-key \
    WEBSITE_TIME_ZONE=UTC

# Step 5: Assign ACR Pull role
echo ""
echo "Step 4: Assigning ACR Pull permissions..."
PRINCIPAL_ID=$(az containerapp show \
  --name ${CONTAINER_APP_NAME} \
  --resource-group ${RESOURCE_GROUP} \
  --query identity.principalId -o tsv)

az role assignment create \
  --assignee ${PRINCIPAL_ID} \
  --role AcrPull \
  --scope /subscriptions/$(az account show --query id -o tsv)/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.ContainerRegistry/registries/${ACR_NAME}

# Step 6: Assign Search Index Data Reader role
echo ""
echo "Step 5: Assigning Search Index Data Reader permissions..."
az role assignment create \
  --assignee ${PRINCIPAL_ID} \
  --role "Search Index Data Reader" \
  --scope /subscriptions/$(az account show --query id -o tsv)/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.Search/searchServices/${SEARCH_SERVICE}

echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "Container App URL:"
az containerapp show \
  --name ${CONTAINER_APP_NAME} \
  --resource-group ${RESOURCE_GROUP} \
  --query properties.configuration.ingress.fqdn -o tsv

echo ""
echo "Test the endpoint:"
FQDN=$(az containerapp show --name ${CONTAINER_APP_NAME} --resource-group ${RESOURCE_GROUP} --query properties.configuration.ingress.fqdn -o tsv)
echo "curl -X POST https://${FQDN}/api/update-check"
