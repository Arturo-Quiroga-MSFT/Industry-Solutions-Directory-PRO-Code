#!/bin/bash

##############################################################################
# Pre-Deployment Checklist for Dual-Mode ISD Chat
# Run this before deploying to catch common issues
##############################################################################

echo "=========================================="
echo "ISD Chat - Pre-Deployment Checklist"
echo "=========================================="
echo ""

ERRORS=0

# Check 1: Azure CLI
echo "✓ Checking Azure CLI..."
if command -v az &> /dev/null; then
    echo "  ✅ Azure CLI installed"
    
    # Check if logged in
    if az account show &> /dev/null; then
        SUBSCRIPTION=$(az account show --query name -o tsv)
        echo "  ✅ Logged in to: $SUBSCRIPTION"
    else
        echo "  ❌ Not logged in to Azure"
        echo "     Run: az login"
        ((ERRORS++))
    fi
else
    echo "  ❌ Azure CLI not installed"
    echo "     Install: https://docs.microsoft.com/cli/azure/install-azure-cli"
    ((ERRORS++))
fi
echo ""

# Check 2: Environment Variables
echo "✓ Checking Environment Variables..."

if [ -n "$AZURE_OPENAI_API_KEY" ]; then
    echo "  ✅ AZURE_OPENAI_API_KEY is set"
else
    echo "  ❌ AZURE_OPENAI_API_KEY not set"
    echo "     Run: export AZURE_OPENAI_API_KEY='your-key'"
    ((ERRORS++))
fi

if [ -n "$AZURE_OPENAI_ENDPOINT" ]; then
    echo "  ✅ AZURE_OPENAI_ENDPOINT is set: $AZURE_OPENAI_ENDPOINT"
else
    echo "  ❌ AZURE_OPENAI_ENDPOINT not set"
    echo "     Run: export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'"
    ((ERRORS++))
fi

if [ -n "$SQL_PASSWORD" ]; then
    echo "  ✅ SQL_PASSWORD is set"
else
    echo "  ❌ SQL_PASSWORD not set"
    echo "     Run: export SQL_PASSWORD='your-password'"
    ((ERRORS++))
fi

if [ -n "$AZURE_OPENAI_CHAT_DEPLOYMENT_NAME" ]; then
    echo "  ✅ AZURE_OPENAI_CHAT_DEPLOYMENT_NAME: $AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"
else
    echo "  ⚠️  AZURE_OPENAI_CHAT_DEPLOYMENT_NAME not set (will use default: gpt-4o-mini)"
fi
echo ""

# Check 3: Resource Group
echo "✓ Checking Azure Resources..."
RESOURCE_GROUP="indsolse-dev-rg"

if az group show --name $RESOURCE_GROUP &> /dev/null; then
    echo "  ✅ Resource Group exists: $RESOURCE_GROUP"
else
    echo "  ❌ Resource Group not found: $RESOURCE_GROUP"
    echo "     Create it or update RESOURCE_GROUP in deploy script"
    ((ERRORS++))
fi

# Check 4: Container Registry
ACR_NAME="indsolsedevacr"

if az acr show --name $ACR_NAME &> /dev/null; then
    echo "  ✅ Container Registry exists: $ACR_NAME"
    
    # Check if we can access it
    if az acr login --name $ACR_NAME &> /dev/null; then
        echo "  ✅ ACR login successful"
    else
        echo "  ⚠️  ACR login failed (might need permissions)"
    fi
else
    echo "  ❌ Container Registry not found: $ACR_NAME"
    echo "     Create it or update ACR_NAME in deploy script"
    ((ERRORS++))
fi

# Check 5: Container Apps Environment
ENVIRONMENT_NAME="indsolse-dev-env"

if az containerapp env show --name $ENVIRONMENT_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo "  ✅ Container Apps Environment exists: $ENVIRONMENT_NAME"
else
    echo "  ❌ Container Apps Environment not found: $ENVIRONMENT_NAME"
    echo "     Create it with: az containerapp env create --name $ENVIRONMENT_NAME --resource-group $RESOURCE_GROUP --location swedencentral"
    ((ERRORS++))
fi
echo ""

# Check 6: Local Files
echo "✓ Checking Local Project Files..."

if [ -f "../frontend-react/backend/main.py" ]; then
    echo "  ✅ Backend code found"
else
    echo "  ❌ Backend main.py not found"
    ((ERRORS++))
fi

if [ -f "../frontend-react/backend/multi_agent_pipeline.py" ]; then
    echo "  ✅ Multi-agent pipeline found"
else
    echo "  ❌ Multi-agent pipeline not found"
    ((ERRORS++))
fi

if [ -f "../frontend-react/src/App.tsx" ]; then
    echo "  ✅ Frontend code found"
else
    echo "  ❌ Frontend App.tsx not found"
    ((ERRORS++))
fi

if [ -f "../data-ingestion/sql-direct/nl2sql_pipeline.py" ]; then
    echo "  ✅ NL2SQL pipeline found"
else
    echo "  ❌ NL2SQL pipeline not found"
    ((ERRORS++))
fi
echo ""

# Check 7: Database Connectivity (optional test)
echo "✓ Checking Database Configuration..."
SQL_SERVER="mssoldir-prd-sql.database.windows.net"
SQL_DATABASE="Solutions"

echo "  ℹ️  SQL Server: $SQL_SERVER"
echo "  ℹ️  Database: $SQL_DATABASE"
echo "  ℹ️  (Connection will be tested during deployment)"
echo ""

# Summary
echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    echo "✅ All checks passed!"
    echo "=========================================="
    echo ""
    echo "Ready to deploy! Run:"
    echo "  ./deploy-dual-mode-testing.sh"
    echo ""
    exit 0
else
    echo "❌ Found $ERRORS error(s)"
    echo "=========================================="
    echo ""
    echo "Please fix the errors above before deploying."
    echo ""
    exit 1
fi
