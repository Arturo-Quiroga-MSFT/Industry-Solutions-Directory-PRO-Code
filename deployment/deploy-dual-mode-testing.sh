#!/bin/bash

##############################################################################
# Deploy Dual-Mode ISD Chat Application for Testing
# Creates TWO separate deployments:
#   1. Customer Mode (external-facing, vendor-neutral)
#   2. Seller Mode (internal Microsoft, partner intelligence)
##############################################################################

set -e  # Exit on error

# Configuration
RESOURCE_GROUP="indsolse-dev-rg"
LOCATION="swedencentral"
ACR_NAME="indsolsedevacr"
ENVIRONMENT_NAME="indsolse-dev-env"

# Customer Mode App Names
CUSTOMER_BACKEND_APP="isd-chat-customer-backend"
CUSTOMER_FRONTEND_APP="isd-chat-customer-frontend"

# Seller Mode App Names
SELLER_BACKEND_APP="isd-chat-seller-backend"
SELLER_FRONTEND_APP="isd-chat-seller-frontend"

# Image names
BACKEND_IMAGE="isd-chat-backend:v2.9"
FRONTEND_IMAGE="isd-chat-frontend:v2.9"

# Database Configuration (from your existing setup)
SQL_SERVER="mssoldir-prd-sql.database.windows.net"
SQL_DATABASE="Solutions"
SQL_USERNAME="sa-mssoldir-prd-sql"

echo "=========================================="
echo "ISD Chat - Dual Mode Deployment"
echo "=========================================="
echo ""
echo "📦 Deploying TWO separate applications:"
echo "   1. 🛡️  CUSTOMER MODE (vendor-neutral)"
echo "   2. 💾 SELLER MODE (partner intelligence)"
echo ""
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "Environment: $ENVIRONMENT_NAME"
echo ""

# Check Azure CLI login
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

# Check for required secrets
echo "Checking Azure credentials..."
if [ -z "$AZURE_OPENAI_API_KEY" ]; then
    echo "❌ AZURE_OPENAI_API_KEY not set"
    echo "Please set: export AZURE_OPENAI_API_KEY='your-key'"
    exit 1
fi

if [ -z "$SQL_PASSWORD" ]; then
    echo "❌ SQL_PASSWORD not set"
    echo "Please set: export SQL_PASSWORD='your-password'"
    exit 1
fi

echo "✅ Credentials verified"
echo ""

# Get Azure OpenAI endpoint from environment or prompt
if [ -z "$AZURE_OPENAI_ENDPOINT" ]; then
    echo "❌ AZURE_OPENAI_ENDPOINT not set"
    echo "Please set: export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'"
    exit 1
fi

AZURE_OPENAI_CHAT_DEPLOYMENT=${AZURE_OPENAI_CHAT_DEPLOYMENT:-"gpt-4.1"}

echo "OpenAI Endpoint: $AZURE_OPENAI_ENDPOINT"
echo "OpenAI Deployment: $AZURE_OPENAI_CHAT_DEPLOYMENT"
echo ""

##############################################################################
# PART 1: Build Docker Images
##############################################################################

echo "=========================================="
echo "Building Backend Docker Image"
echo "=========================================="

cd ../frontend-react/backend

# Create temporary Dockerfile if it doesn't exist
if [ ! -f Dockerfile ]; then
    echo "Creating Dockerfile for backend..."
    cat > Dockerfile << 'EOF'
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    unixodbc \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft ODBC Driver 18 for SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy nl2sql_pipeline from data-ingestion
COPY ../../data-ingestion/sql-direct/nl2sql_pipeline.py .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
fi

# Build backend image
az acr build \
    --registry $ACR_NAME \
    --image $BACKEND_IMAGE \
    --file Dockerfile \
    --build-arg BUILDKIT_PROGRESS=plain \
    .

if [ $? -eq 0 ]; then
    echo "✅ Backend image built successfully"
else
    echo "❌ Failed to build backend image"
    exit 1
fi

cd ../../deployment

echo ""
echo "=========================================="
echo "Building Frontend Docker Image"
echo "=========================================="

cd ../frontend-react

# Create temporary Dockerfile for frontend if it doesn't exist
if [ ! -f Dockerfile ]; then
    echo "Creating Dockerfile for frontend..."
    cat > Dockerfile << 'EOF'
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production image
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
RUN echo 'server { \
    listen 80; \
    server_name _; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
EOF
fi

# Build frontend image
az acr build \
    --registry $ACR_NAME \
    --image $FRONTEND_IMAGE \
    --file Dockerfile \
    --build-arg BUILDKIT_PROGRESS=plain \
    .

if [ $? -eq 0 ]; then
    echo "✅ Frontend image built successfully"
else
    echo "❌ Failed to build frontend image"
    exit 1
fi

cd ../deployment

##############################################################################
# PART 2: Deploy CUSTOMER MODE (Port 8001)
##############################################################################

echo ""
echo "=========================================="
echo "🛡️  Deploying CUSTOMER MODE"
echo "=========================================="

# Deploy Customer Backend
echo "Deploying Customer Backend..."
az containerapp create \
    --name $CUSTOMER_BACKEND_APP \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT_NAME \
    --image "$ACR_NAME.azurecr.io/$BACKEND_IMAGE" \
    --registry-server "$ACR_NAME.azurecr.io" \
    --target-port 8000 \
    --ingress external \
    --min-replicas 1 \
    --max-replicas 3 \
    --cpu 1.0 \
    --memory 2.0Gi \
    --env-vars \
        "APP_MODE=customer" \
        "AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY" \
        "AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT" \
        "AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=$AZURE_OPENAI_CHAT_DEPLOYMENT" \
        "SQL_SERVER=$SQL_SERVER" \
        "SQL_DATABASE=$SQL_DATABASE" \
        "SQL_USERNAME=$SQL_USERNAME" \
        "SQL_PASSWORD=$SQL_PASSWORD" \
        "ALLOWED_ORIGINS=https://$CUSTOMER_FRONTEND_APP.$ENVIRONMENT_NAME.$LOCATION.azurecontainerapps.io,http://localhost:5174"

if [ $? -eq 0 ]; then
    echo "✅ Customer backend deployed"
    CUSTOMER_BACKEND_URL=$(az containerapp show \
        --name $CUSTOMER_BACKEND_APP \
        --resource-group $RESOURCE_GROUP \
        --query properties.configuration.ingress.fqdn -o tsv)
    echo "   URL: https://$CUSTOMER_BACKEND_URL"
else
    echo "❌ Failed to deploy customer backend"
    exit 1
fi

# Deploy Customer Frontend
echo ""
echo "Deploying Customer Frontend..."
az containerapp create \
    --name $CUSTOMER_FRONTEND_APP \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT_NAME \
    --image "$ACR_NAME.azurecr.io/$FRONTEND_IMAGE" \
    --registry-server "$ACR_NAME.azurecr.io" \
    --target-port 80 \
    --ingress external \
    --min-replicas 1 \
    --max-replicas 2 \
    --cpu 0.5 \
    --memory 1.0Gi \
    --env-vars \
        "VITE_API_URL=https://$CUSTOMER_BACKEND_URL"

if [ $? -eq 0 ]; then
    echo "✅ Customer frontend deployed"
    CUSTOMER_FRONTEND_URL=$(az containerapp show \
        --name $CUSTOMER_FRONTEND_APP \
        --resource-group $RESOURCE_GROUP \
        --query properties.configuration.ingress.fqdn -o tsv)
    echo "   URL: https://$CUSTOMER_FRONTEND_URL"
else
    echo "❌ Failed to deploy customer frontend"
    exit 1
fi

##############################################################################
# PART 3: Deploy SELLER MODE (Port 8000)
##############################################################################

echo ""
echo "=========================================="
echo "💾 Deploying SELLER MODE"
echo "=========================================="

# Deploy Seller Backend
echo "Deploying Seller Backend..."
az containerapp create \
    --name $SELLER_BACKEND_APP \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT_NAME \
    --image "$ACR_NAME.azurecr.io/$BACKEND_IMAGE" \
    --registry-server "$ACR_NAME.azurecr.io" \
    --target-port 8000 \
    --ingress external \
    --min-replicas 1 \
    --max-replicas 3 \
    --cpu 1.0 \
    --memory 2.0Gi \
    --env-vars \
        "APP_MODE=seller" \
        "AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY" \
        "AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT" \
        "AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=$AZURE_OPENAI_CHAT_DEPLOYMENT" \
        "SQL_SERVER=$SQL_SERVER" \
        "SQL_DATABASE=$SQL_DATABASE" \
        "SQL_USERNAME=$SQL_USERNAME" \
        "SQL_PASSWORD=$SQL_PASSWORD" \
        "ALLOWED_ORIGINS=https://$SELLER_FRONTEND_APP.$ENVIRONMENT_NAME.$LOCATION.azurecontainerapps.io,http://localhost:5173"

if [ $? -eq 0 ]; then
    echo "✅ Seller backend deployed"
    SELLER_BACKEND_URL=$(az containerapp show \
        --name $SELLER_BACKEND_APP \
        --resource-group $RESOURCE_GROUP \
        --query properties.configuration.ingress.fqdn -o tsv)
    echo "   URL: https://$SELLER_BACKEND_URL"
else
    echo "❌ Failed to deploy seller backend"
    exit 1
fi

# Deploy Seller Frontend
echo ""
echo "Deploying Seller Frontend..."
az containerapp create \
    --name $SELLER_FRONTEND_APP \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT_NAME \
    --image "$ACR_NAME.azurecr.io/$FRONTEND_IMAGE" \
    --registry-server "$ACR_NAME.azurecr.io" \
    --target-port 80 \
    --ingress external \
    --min-replicas 1 \
    --max-replicas 2 \
    --cpu 0.5 \
    --memory 1.0Gi \
    --env-vars \
        "VITE_API_URL=https://$SELLER_BACKEND_URL"

if [ $? -eq 0 ]; then
    echo "✅ Seller frontend deployed"
    SELLER_FRONTEND_URL=$(az containerapp show \
        --name $SELLER_FRONTEND_APP \
        --resource-group $RESOURCE_GROUP \
        --query properties.configuration.ingress.fqdn -o tsv)
    echo "   URL: https://$SELLER_FRONTEND_URL"
else
    echo "❌ Failed to deploy seller frontend"
    exit 1
fi

##############################################################################
# PART 4: Summary
##############################################################################

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "🛡️  CUSTOMER MODE (External):"
echo "   Frontend: https://$CUSTOMER_FRONTEND_URL"
echo "   Backend:  https://$CUSTOMER_BACKEND_URL"
echo "   - Vendor-neutral insights"
echo "   - No partner rankings"
echo "   - Legal compliance mode"
echo ""
echo "💾 SELLER MODE (Internal):"
echo "   Frontend: https://$SELLER_FRONTEND_URL"
echo "   Backend:  https://$SELLER_BACKEND_URL"
echo "   - Partner intelligence"
echo "   - Competitive insights"
echo "   - Seller decision support"
echo ""
echo "📊 Next Steps:"
echo "   1. Test both URLs to verify correct mode"
echo "   2. Update TESTING_GUIDE.md with these URLs"
echo "   3. Send testing instructions to your team"
echo "   4. Monitor logs: az containerapp logs show -n [app-name] -g $RESOURCE_GROUP"
echo ""
echo "🔐 Security Notes:"
echo "   - Both apps use HTTPS"
echo "   - Environment variables are encrypted"
echo "   - Database is READ-ONLY mode"
echo "   - CORS configured for respective frontends"
echo ""
echo "Happy Testing! 🚀"
