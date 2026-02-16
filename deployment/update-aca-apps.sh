#!/bin/bash

##############################################################################
# Update All ACA Apps - Build, Push, and Deploy
#
# Builds Docker images for backend + both frontends, pushes to ACR,
# and updates all 4 Azure Container Apps.
#
# Usage:
#   ./deployment/update-aca-apps.sh          # default tag: v3.x (auto-incremented)
#   ./deployment/update-aca-apps.sh v3.2     # explicit tag
##############################################################################

set -e

# Configuration
RESOURCE_GROUP="indsolse-dev-rg"
ACR_NAME="indsolsedevacr"
ACR_SERVER="${ACR_NAME}.azurecr.io"

# Container App names
SELLER_BACKEND="isd-chat-seller-backend"
SELLER_FRONTEND="isd-chat-seller-frontend"
CUSTOMER_BACKEND="isd-chat-customer-backend"
CUSTOMER_FRONTEND="isd-chat-customer-frontend"

# Image names
BACKEND_IMAGE="isd-backend-seller"
SELLER_FRONTEND_IMAGE="isd-frontend-seller"
CUSTOMER_FRONTEND_IMAGE="isd-frontend-customer"

# Backend URLs (for VITE_API_URL build arg)
SELLER_BACKEND_URL="https://isd-chat-seller-backend.kindfield-353d98ed.swedencentral.azurecontainerapps.io"
CUSTOMER_BACKEND_URL="https://isd-chat-customer-backend.kindfield-353d98ed.swedencentral.azurecontainerapps.io"

# Tag (from argument or auto-detect)
if [ -n "$1" ]; then
    TAG="$1"
else
    # Auto-detect: find latest tag in ACR and increment
    LATEST=$(az acr repository show-tags --name "$ACR_NAME" --repository "$BACKEND_IMAGE" --orderby time_desc --top 1 -o tsv 2>/dev/null || echo "v3.0")
    MAJOR=$(echo "$LATEST" | sed 's/v//' | cut -d. -f1)
    MINOR=$(echo "$LATEST" | sed 's/v//' | cut -d. -f2)
    TAG="v${MAJOR}.$((MINOR + 1))"
fi

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "  ACA Update - All 4 Apps"
echo "=========================================="
echo ""
echo "Resource Group: $RESOURCE_GROUP"
echo "ACR:            $ACR_SERVER"
echo "Tag:            $TAG"
echo ""
echo "Apps:"
echo "  1. $SELLER_BACKEND"
echo "  2. $CUSTOMER_BACKEND"
echo "  3. $SELLER_FRONTEND"
echo "  4. $CUSTOMER_FRONTEND"
echo ""

# Pre-flight: Check Azure login
echo "Checking Azure CLI login..."
if ! az account show &> /dev/null; then
    echo "❌ Not logged in. Run: az login"
    exit 1
fi
echo "✅ Logged in to Azure"
echo ""

# ============================================================
# Step 1: Build Backend Image
# ============================================================
echo "=========================================="
echo "Step 1/5: Building Backend Image"
echo "=========================================="
cd "$PROJECT_ROOT/frontend-react/backend"
az acr build \
    --registry "$ACR_NAME" \
    --image "${BACKEND_IMAGE}:${TAG}" \
    --file Dockerfile \
    .
echo "✅ Backend image built: ${BACKEND_IMAGE}:${TAG}"
echo ""

# ============================================================
# Step 2: Build Seller Frontend Image
# ============================================================
echo "=========================================="
echo "Step 2/5: Building Seller Frontend Image"
echo "=========================================="
cd "$PROJECT_ROOT/frontend-react"
az acr build \
    --registry "$ACR_NAME" \
    --image "${SELLER_FRONTEND_IMAGE}:${TAG}" \
    --build-arg "VITE_API_URL=${SELLER_BACKEND_URL}" \
    .
echo "✅ Seller frontend image built: ${SELLER_FRONTEND_IMAGE}:${TAG}"
echo ""

# ============================================================
# Step 3: Build Customer Frontend Image
# ============================================================
echo "=========================================="
echo "Step 3/5: Building Customer Frontend Image"
echo "=========================================="
az acr build \
    --registry "$ACR_NAME" \
    --image "${CUSTOMER_FRONTEND_IMAGE}:${TAG}" \
    --build-arg "VITE_API_URL=${CUSTOMER_BACKEND_URL}" \
    .
echo "✅ Customer frontend image built: ${CUSTOMER_FRONTEND_IMAGE}:${TAG}"
echo ""

# ============================================================
# Step 4: Update All Container Apps
# ============================================================
echo "=========================================="
echo "Step 4/5: Updating Container Apps"
echo "=========================================="

echo ""
echo "Updating $SELLER_BACKEND..."
az containerapp update \
    --name "$SELLER_BACKEND" \
    --resource-group "$RESOURCE_GROUP" \
    --image "${ACR_SERVER}/${BACKEND_IMAGE}:${TAG}" \
    -o table
echo "✅ $SELLER_BACKEND updated"

echo ""
echo "Updating $CUSTOMER_BACKEND..."
az containerapp update \
    --name "$CUSTOMER_BACKEND" \
    --resource-group "$RESOURCE_GROUP" \
    --image "${ACR_SERVER}/${BACKEND_IMAGE}:${TAG}" \
    -o table
echo "✅ $CUSTOMER_BACKEND updated"

echo ""
echo "Updating $SELLER_FRONTEND..."
az containerapp update \
    --name "$SELLER_FRONTEND" \
    --resource-group "$RESOURCE_GROUP" \
    --image "${ACR_SERVER}/${SELLER_FRONTEND_IMAGE}:${TAG}" \
    -o table
echo "✅ $SELLER_FRONTEND updated"

echo ""
echo "Updating $CUSTOMER_FRONTEND..."
az containerapp update \
    --name "$CUSTOMER_FRONTEND" \
    --resource-group "$RESOURCE_GROUP" \
    --image "${ACR_SERVER}/${CUSTOMER_FRONTEND_IMAGE}:${TAG}" \
    -o table
echo "✅ $CUSTOMER_FRONTEND updated"

echo ""

# ============================================================
# Step 5: Verify Deployment
# ============================================================
echo "=========================================="
echo "Step 5/5: Verifying Deployment"
echo "=========================================="
az containerapp list \
    --resource-group "$RESOURCE_GROUP" \
    --query "[].{App:name, Image:properties.template.containers[0].image}" \
    -o table

echo ""
echo "=========================================="
echo "  ✅ All 4 ACA Apps Updated to ${TAG}"
echo "=========================================="
echo ""
echo "🔗 Seller Frontend:   https://isd-chat-seller-frontend.kindfield-353d98ed.swedencentral.azurecontainerapps.io"
echo "🔗 Customer Frontend: https://isd-chat-customer-frontend.kindfield-353d98ed.swedencentral.azurecontainerapps.io"
echo ""
