# Azure Infrastructure Recreation Guide
## Industry Solutions Directory - React Chat Applications

**Last Updated:** January 4, 2026  
**Author:** Arturo Quiroga  
**Purpose:** Complete guide to recreate Azure infrastructure for dual-mode React chat apps (Seller & Customer)

---

## 📋 Overview

This guide provides step-by-step instructions to recreate the Azure infrastructure for the Industry Solutions Directory chat applications after monthly resource cleanup due to cost constraints.

### Applications to Deploy
1. **Seller Mode Frontend + Backend** - Internal use with partner rankings and analytics
2. **Customer Mode Frontend + Backend** - External use with unbiased recommendations

### Total Deployment Time
- **Estimated:** 45-60 minutes (following this updated guide)
- **Actual (January 2026):** 2.5 hours (first attempt with troubleshooting)

### ⚠️ CRITICAL LESSONS LEARNED (January 2026)
1. **Always use ACR build** - Never use local Docker (ARM64 vs AMD64 architecture mismatch)
2. **Set ALLOWED_ORIGINS correctly** - Frontend URL must be FIRST in the comma-separated list
3. **Apply ACR credentials immediately** - After creating each container app, run `az containerapp registry set`
4. **Remove .env files** - Before building frontend, delete all .env* files to prevent localhost:8000 hardcoding
5. **Use single quotes for passwords** - Bash interprets `!` in double quotes; use single quotes for special chars
6. **New Azure OpenAI endpoint** - Use `r2d2-foundry-001.services.ai.azure.com` (updated AI Foundry URL)

### Monthly Cost Estimate
- **Infrastructure:** ~$137/month
- **Azure OpenAI (GPT-4.1):** ~$90-150/month
- **Total:** ~$227-287/month

---

## 🔑 Prerequisites Checklist

### Required Before Starting

- [ ] **Azure Subscription** with active credits
- [ ] **Azure CLI** installed (`az --version` to verify)
- [ ] **Docker** installed (for local testing)
- [ ] **Git repository** access to this codebase

### Credentials to Gather

#### 1. Azure OpenAI (AI Foundry) - ⚠️ UPDATED JANUARY 2026
```bash
AZURE_OPENAI_API_KEY="<your-azure-openai-api-key-here>"
AZURE_OPENAI_ENDPOINT="https://r2d2-foundry-001.services.ai.azure.com/"
AZURE_OPENAI_DEPLOYMENT="gpt-4.1"
AZURE_OPENAI_API_VERSION="2024-08-01-preview"
```
**Where to find:** Azure Portal → AI Foundry → Keys and Endpoint  
**Note:** Endpoint changed from `aq-ai-foundry-sweden-central` to `r2d2-foundry-001` in January 2026

#### 2. SQL Server (ISD Production Database - Read-Only) - ⚠️ PASSWORD ESCAPING CRITICAL
```bash
SQL_SERVER="mssoldir-prd-sql.database.windows.net"
SQL_DATABASE="mssoldir-prd"
SQL_USERNAME="isdapi_dev"
SQL_PASSWORD='<your-password-with-special-chars>'  # ⚠️ MUST use single quotes - bash interprets ! in double quotes
```
**Where to find:** Secure password vault or contact database admin  
**CRITICAL:** Always use single quotes around password when setting environment variables. Double quotes cause bash to interpret `!` as history expansion, truncating the password.

#### 3. Azure Subscription
```bash
SUBSCRIPTION_ID="<your-subscription-id>"
```
**Where to find:** `az account show --query id -o tsv`

---

## 🚀 Phase 1: Core Infrastructure Setup

**Time:** 10-15 minutes  
**Cost:** ~$20/month

### 1.1 Azure CLI Login

```bash
# Login to Azure
az login

# Set subscription
az account set --subscription <your-subscription-id>

# Verify
az account show --query "{Name:name, SubscriptionId:id, TenantId:tenantId}" -o table
```

### 1.2 Create Core Resources

```bash
#!/bin/bash
# Save as: deployment/setup-january-2026.sh

# Configuration
RESOURCE_GROUP="indsolse-dev-rg"
LOCATION="swedencentral"
ACR_NAME="indsolsedevacr"
ENVIRONMENT_NAME="indsolse-dev-env"
LOG_ANALYTICS_WORKSPACE="indsolse-dev-logs"

echo "=========================================="
echo "Creating Core Infrastructure"
echo "=========================================="

# 1. Create Resource Group
echo "✓ Creating Resource Group: $RESOURCE_GROUP"
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION \
  --output table

# 2. Create Container Registry
echo "✓ Creating Container Registry: $ACR_NAME"
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true \
  --location $LOCATION \
  --output table

# 3. Create Log Analytics Workspace
echo "✓ Creating Log Analytics Workspace: $LOG_ANALYTICS_WORKSPACE"
az monitor log-analytics workspace create \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $LOG_ANALYTICS_WORKSPACE \
  --location $LOCATION \
  --output table

# Get workspace credentials
WORKSPACE_ID=$(az monitor log-analytics workspace show \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $LOG_ANALYTICS_WORKSPACE \
  --query customerId -o tsv)

WORKSPACE_KEY=$(az monitor log-analytics workspace get-shared-keys \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $LOG_ANALYTICS_WORKSPACE \
  --query primarySharedKey -o tsv)

# 4. Create Container Apps Environment
echo "✓ Creating Container Apps Environment: $ENVIRONMENT_NAME"
az containerapp env create \
  --name $ENVIRONMENT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --logs-workspace-id $WORKSPACE_ID \
  --logs-workspace-key $WORKSPACE_KEY \
  --output table

echo ""
echo "=========================================="
echo "✅ Core Infrastructure Created!"
echo "=========================================="
echo "Resource Group: $RESOURCE_GROUP"
echo "Container Registry: $ACR_NAME"
echo "Environment: $ENVIRONMENT_NAME"
echo "Location: $LOCATION"
```

### 1.3 Run Setup Script

```bash
cd /Users/arturoquiroga/Industry-Solutions-Directory-PRO-Code/deployment
chmod +x setup-january-2026.sh
bash setup-january-2026.sh
```

**Expected Output:**
```
✅ Core Infrastructure Created!
Resource Group: indsolse-dev-rg
Container Registry: indsolsedevacr
Environment: indsolse-dev-env
Location: swedencentral
```

---

## 🔧 Phase 2: Backend Deployment

**Time:** 20-30 minutes  
**Cost:** ~$18/month (2 backends)

### 2.1 Seller Backend

#### Build Docker Image

```bash
cd /Users/arturoquiroga/Industry-Solutions-Directory-PRO-Code/frontend-react/backend

# Build and push to ACR
az acr build \
  --registry indsolsedevacr \
  --image isd-backend-seller:v2.6-jan2026 \
  --file Dockerfile \
  .
```

#### Deploy Container App - ⚠️ UPDATED STEPS (January 2026)

**CRITICAL: Do these steps in order to avoid image pull failures**

```bash
# Step 1: Create seller backend container app
az containerapp create \
  --name isd-chat-seller-backend \
  --resource-group indsolse-dev-rg \
  --environment indsolse-dev-env \
  --image indsolsedevacr.azurecr.io/isd-backend-seller:v2.6 \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 1 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --registry-server indsolsedevacr.azurecr.io \
  --env-vars \
    APP_MODE=seller \
    SQL_SERVER='mssoldir-prd-sql.database.windows.net' \
    SQL_DATABASE='mssoldir-prd' \
    SQL_USERNAME='isdapi_dev' \
    SQL_PASSWORD='<your-sql-password-here>' \
    AZURE_OPENAI_ENDPOINT='https://r2d2-foundry-001.services.ai.azure.com/' \
    AZURE_OPENAI_API_KEY='<your-azure-openai-api-key-here>' \
    AZURE_OPENAI_DEPLOYMENT='gpt-4.1' \
    AZURE_OPENAI_API_VERSION='2024-08-01-preview' \
    ALLOWED_ORIGINS='https://isd-chat-seller-frontend.kindfield-353d98ed.swedencentral.azurecontainerapps.io,http://localhost:5173,http://localhost:5174'

# Step 2: Configure ACR authentication (CRITICAL - prevents ImagePullBackOff)
az containerapp registry set \
  --name isd-chat-seller-backend \
  --resource-group indsolse-dev-rg \
  --server indsolsedevacr.azurecr.io \
  --username indsolsedevacr \
  --password "$(az acr credential show --name indsolsedevacr --query 'passwords[0].value' -o tsv)"
```

**⚠️ Key Changes from Previous Version:**
- Use single quotes `'` for all passwords with special characters (`!`, `&`, etc.)
- Updated Azure OpenAI endpoint to `r2d2-foundry-001`
- **MUST** run `az containerapp registry set` immediately after creation
- Frontend URL must be FIRST in `ALLOWED_ORIGINS` list

#### Get Backend URL

```bash
SELLER_BACKEND_URL=$(az containerapp show \
  --name isd-chat-seller-backend \
  --resource-group indsolse-dev-rg \
  --query properties.configuration.ingress.fqdn -o tsv)

echo "Seller Backend URL: https://$SELLER_BACKEND_URL"
```

#### Test Health Endpoint

```bash
curl https://$SELLER_BACKEND_URL/
# Expected: {"status":"healthy","service":"ISD NL2SQL API","version":"1.0.0"}
```

### 2.2 Customer Backend - ⚠️ UPDATED (January 2026)

```bash
# Step 1: Create customer backend (same image, APP_MODE=customer)
az containerapp create \
  --name isd-chat-customer-backend \
  --resource-group indsolse-dev-rg \
  --environment indsolse-dev-env \
  --image indsolsedevacr.azurecr.io/isd-backend-seller:v2.6 \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 1 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --registry-server indsolsedevacr.azurecr.io \
  --env-vars \
    APP_MODE=customer \
    SQL_SERVER='mssoldir-prd-sql.database.windows.net' \
    SQL_DATABASE='mssoldir-prd' \
    SQL_USERNAME='isdapi_dev' \
    SQL_PASSWORD='<your-sql-password-here>' \
    AZURE_OPENAI_ENDPOINT='https://r2d2-foundry-001.services.ai.azure.com/' \
    AZURE_OPENAI_API_KEY='<your-azure-openai-api-key-here>' \
    AZURE_OPENAI_DEPLOYMENT='gpt-4.1' \
    AZURE_OPENAI_API_VERSION='2024-08-01-preview' \
    ALLOWED_ORIGINS='https://isd-chat-customer-frontend.kindfield-353d98ed.swedencentral.azurecontainerapps.io,http://localhost:5173,http://localhost:5174'

# Step 2: Configure ACR authentication (CRITICAL)
az containerapp registry set \
  --name isd-chat-customer-backend \
  --resource-group indsolse-dev-rg \
  --server indsolsedevacr.azurecr.io \
  --username indsolsedevacr \
  --password "$(az acr credential show --name indsolsedevacr --query 'passwords[0].value' -o tsv)"

# Get customer backend URL
CUSTOMER_BACKEND_URL=$(az containerapp show \
  --name isd-chat-customer-backend \
  --resource-group indsolse-dev-rg \
  --query properties.configuration.ingress.fqdn -o tsv)

echo "Customer Backend URL: https://$CUSTOMER_BACKEND_URL"

# Test health endpoint - should return "mode": "customer"
curl https://$CUSTOMER_BACKEND_URL/api/health | jq
```

---

## 🎨 Phase 3: Frontend Deployment - ⚠️ CRITICAL UPDATES (January 2026)

**Time:** 20-30 minutes  
**Cost:** ~$9/month (2 frontends)

### ⚠️ CRITICAL: Always Use ACR Build (Never Local Docker)

**Problem Encountered (January 2026):**
- Local Docker on Mac ARM64 builds ARM64 images
- Azure Container Apps requires AMD64/linux images
- ARM64 images fail with `exec format error`

**Solution:** ALWAYS use `az acr build` which builds AMD64 by default.

### 3.1 Seller Frontend - UPDATED STEPS

#### Step 1: Remove Local .env Files (CRITICAL)

```bash
cd /Users/arturoquiroga/Industry-Solutions-Directory-PRO-Code/frontend-react

# Remove ALL .env files to prevent localhost:8000 hardcoding
rm -f .env .env.local .env.production .env.development

# Verify removal
ls -la .env* 2>/dev/null || echo "✓ All .env files removed"
```

#### Step 2: Build Frontend with ACR (NOT Docker!)

```bash
# Get seller backend URL
SELLER_BACKEND_URL=$(az containerapp show \
  --name isd-chat-seller-backend \
  --resource-group indsolse-dev-rg \
  --query properties.configuration.ingress.fqdn -o tsv)

echo "Building with backend URL: https://$SELLER_BACKEND_URL"

# Build using ACR (builds AMD64 automatically)
az acr build \
  --registry indsolsedevacr \
  --image isd-frontend-seller:v2.6-jan2026 \
  --build-arg VITE_API_URL=https://$SELLER_BACKEND_URL \
  --file Dockerfile \
  .
```

**✅ Expected:** Build completes in ~45 seconds, pushes to ACR

#### Step 3: Deploy Seller Frontend Container App

```bash
az containerapp create \
  --name isd-chat-seller-frontend \
  --resource-group indsolse-dev-rg \
  --environment indsolse-dev-env \
  --image indsolsedevacr.azurecr.io/isd-frontend-seller:v2.6-jan2026 \
  --target-port 80 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 1 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --registry-server indsolsedevacr.azurecr.io

# Step 4: Configure ACR authentication (CRITICAL)
az containerapp registry set \
  --name isd-chat-seller-frontend \
  --resource-group indsolse-dev-rg \
  --server indsolsedevacr.azurecr.io \
  --username indsolsedevacr \
  --password "$(az acr credential show --name indsolsedevacr --query 'passwords[0].value' -o tsv)"

# Get seller frontend URL
SELLER_FRONTEND_URL=$(az containerapp show \
  --name isd-chat-seller-frontend \
  --resource-group indsolse-dev-rg \
  --query properties.configuration.ingress.fqdn -o tsv)

echo "🎉 Seller Frontend URL: https://$SELLER_FRONTEND_URL"
```

#### Step 5: Update Backend CORS to Allow Frontend

```bash
# Update seller backend CORS with the frontend URL
az containerapp update \
  --name isd-chat-seller-backend \
  --resource-group indsolse-dev-rg \
  --set-env-vars \
    ALLOWED_ORIGINS="https://$SELLER_FRONTEND_URL,http://localhost:5173,http://localhost:5174"
```

### 3.2 Customer Frontend - UPDATED STEPS

```bash
# Step 1: Get customer backend URL
CUSTOMER_BACKEND_URL=$(az containerapp show \
  --name isd-chat-customer-backend \
  --resource-group indsolse-dev-rg \
  --query properties.configuration.ingress.fqdn -o tsv)

# Step 2: Remove .env files (if not done already)
cd /Users/arturoquiroga/Industry-Solutions-Directory-PRO-Code/frontend-react
rm -f .env .env.local .env.production .env.development

# Step 3: Build customer frontend with ACR
az acr build \
  --registry indsolsedevacr \
  --image isd-frontend-customer:v2.6-jan2026 \
  --build-arg VITE_API_URL=https://$CUSTOMER_BACKEND_URL \
  --file Dockerfile \
  .

# Step 4: Deploy customer frontend
az containerapp create \
  --name isd-chat-customer-frontend \
  --resource-group indsolse-dev-rg \
  --environment indsolse-dev-env \
  --image indsolsedevacr.azurecr.io/isd-frontend-customer:v2.6-jan2026 \
  --target-port 80 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 1 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --registry-server indsolsedevacr.azurecr.io

# Step 5: Configure ACR authentication (CRITICAL)
az containerapp registry set \
  --name isd-chat-customer-frontend \
  --resource-group indsolse-dev-rg \
  --server indsolsedevacr.azurecr.io \
  --username indsolsedevacr \
  --password "$(az acr credential show --name indsolsedevacr --query 'passwords[0].value' -o tsv)"

# Get customer frontend URL
CUSTOMER_FRONTEND_URL=$(az containerapp show \
  --name isd-chat-customer-frontend \
  --resource-group indsolse-dev-rg \
  --query properties.configuration.ingress.fqdn -o tsv)

echo "🎉 Customer Frontend URL: https://$CUSTOMER_FRONTEND_URL"

# Step 6: Update customer backend CORS with frontend URL
az containerapp update \
  --name isd-chat-customer-backend \
  --resource-group indsolse-dev-rg \
  --set-env-vars \
    ALLOWED_ORIGINS="https://$CUSTOMER_FRONTEND_URL,http://localhost:5173,http://localhost:5174"
```

---

## ✅ Phase 4: Verification & Testing

**Time:** 10 minutes

### 4.1 Verify All Services Are Running

```bash
# Check all container apps status
az containerapp list \
  --resource-group indsolse-dev-rg \
  --query "[].{Name:name,Status:properties.runningStatus,URL:properties.configuration.ingress.fqdn}" \
  -o table
```

**Expected Output:** All 4 apps showing "Running"

### 4.2 Test Seller Mode

```bash
# Get seller frontend URL
SELLER_URL=$(az containerapp show --name isd-chat-seller-frontend --resource-group indsolse-dev-rg --query properties.configuration.ingress.fqdn -o tsv)

echo "Seller Frontend: https://$SELLER_URL"

# Test backend health
curl -s https://isd-chat-seller-backend.kindfield-353d98ed.swedencentral.azurecontainerapps.io/api/health | jq
# Expected: {"status":"healthy", "mode":"seller", ...}
```

### 4.3 Test Customer Mode

```bash
# Get customer frontend URL
CUSTOMER_URL=$(az containerapp show --name isd-chat-customer-frontend --resource-group indsolse-dev-rg --query properties.configuration.ingress.fqdn -o tsv)

echo "Customer Frontend: https://$CUSTOMER_URL"

# Test backend health
curl -s https://isd-chat-customer-backend.kindfield-353d98ed.swedencentral.azurecontainerapps.io/api/health | jq
# Expected: {"status":"healthy", "mode":"customer", ...}
```

### 4.4 Browser Testing

Open both URLs in browser:
1. **Seller:** Should show "SELLER MODE" badge (blue), sample questions on left
2. **Customer:** Should show "CUSTOMER MODE" badge (green), sample questions on left

Test a query in each:
- **Seller:** "What financial services solutions help with risk management?"
- **Customer:** Same query - results should NOT show partner rankings

**✅ Success Indicators:**
- Both frontends load without "Network Error"
- Seller shows blue "SELLER MODE" badge
- Customer shows green "CUSTOMER MODE" badge
- Citations appear as [1], [2], [3] badges
- SQL tab shows formatted query
- DataTable displays results
---

## 🐛 Common Issues & Solutions (January 2026 Learnings)

### Issue 1: ImagePullBackOff / Image Pull Failed with Unauthorized Error

**Symptom:** Container app revision shows "ActivationFailed", logs show "unauthorized" or "image pull failed"

**Root Cause:** ACR credentials not configured on container app

**Solution:**
```bash
az containerapp registry set \
  --name <your-app-name> \
  --resource-group indsolse-dev-rg \
  --server indsolsedevacr.azurecr.io \
  --username indsolsedevacr \
  --password "$(az acr credential show --name indsolsedevacr --query 'passwords[0].value' -o tsv)"
```

### Issue 2: Frontend Shows "Network Error" / CORS Failure

**Symptom:** Browser console shows CORS error, frontend displays "Network Error"

**Root Cause:** Backend `ALLOWED_ORIGINS` doesn't include frontend URL or frontend is not first

**Solution:**
```bash
# Frontend URL MUST be first in the list
az containerapp update \
  --name <backend-name> \
  --resource-group indsolse-dev-rg \
  --set-env-vars \
    ALLOWED_ORIGINS='https://<frontend-url>,http://localhost:5173,http://localhost:5174'
```

**Verification:**
```bash
curl -s -D - -o /dev/null -X OPTIONS 'https://<backend-url>/api/query' \
  -H 'Origin: https://<frontend-url>' \
  -H 'Access-Control-Request-Method: POST' | grep access-control-allow-origin
# Should return: access-control-allow-origin: https://<frontend-url>
```

### Issue 3: Frontend Hardcoded to localhost:8000

**Symptom:** Frontend loads but all API calls go to localhost:8000

**Root Cause:** `.env` file present during Docker build, overriding build arguments

**Solution:**
```bash
cd frontend-react
rm -f .env .env.local .env.production .env.development
# Then rebuild using ACR
```

### Issue 4: SQL Password Truncated / Connection Fails

**Symptom:** Backend logs show SQL connection error, password appears truncated

**Root Cause:** Bash interprets `!` in double-quoted strings as history expansion

**Solution:** Always use single quotes for passwords with special characters:
```bash
SQL_PASSWORD='My!Pass@123'  # ✅ Correct
SQL_PASSWORD="My!Pass@123"  # ❌ Wrong - bash interprets ! and truncates
```

### Issue 5: exec format error / Container Won't Start

**Symptom:** Container logs show `exec format error`, revision fails to activate

**Root Cause:** ARM64 image (from Mac Docker) deployed to AMD64 Container Apps

**Solution:** ALWAYS use ACR build, NEVER local Docker:
```bash
# ✅ Correct - builds AMD64
az acr build --registry indsolsedevacr --image myapp:tag .

# ❌ Wrong - builds ARM64 on Mac
docker build -t indsolsedevacr.azurecr.io/myapp:tag .
docker push indsolsedevacr.azurecr.io/myapp:tag
```

### Issue 6: Frontend Shows "SELLER MODE" Instead of "CUSTOMER MODE"

**Symptom:** Customer frontend displays seller mode badge

**Root Cause:** Frontend caching old `/api/health` response or backend returning wrong mode

**Solutions:**
1. Verify backend returns correct mode:
```bash
curl -s https://isd-chat-customer-backend.*/api/health | jq '.mode'
# Should return: "customer"
```

2. Hard refresh browser (Cmd+Shift+R) or open incognito window

3. If still wrong, rebuild frontend with correct backend URL:
```bash
rm -f .env*
az acr build --registry indsolsedevacr --image isd-frontend-customer:v2.6-fix \
  --build-arg VITE_API_URL=https://isd-chat-customer-backend.*.azurecontainerapps.io .
```

### Issue 7: Revision Stuck in "Activating" State

**Symptom:** New revision never reaches "Running", stays "Activating" for >5 minutes

**Common Causes & Solutions:**

1. **Image Pull Authentication Failure:**
   - Run `az containerapp registry set` with ACR credentials

2. **Invalid Environment Variable:**
   - Check env vars don't have typos: `AZURE_OPENAI_ENDPOINT` not `AZURE_OPENAI_URL`
   - Use single quotes for values with special characters

3. **Application Startup Failure:**
   - Check system logs: `az containerapp logs show --type system --tail 100`
   - Look for Python import errors, missing dependencies

4. **Resource Constraints:**
   - Increase CPU/memory if app is resource-intensive
   - Check logs for OOM (Out of Memory) errors

**Recovery:** Force new revision or rollback:
```bash
# Rollback to last healthy revision
az containerapp revision set-mode \
  --name <app-name> \
  --resource-group indsolse-dev-rg \
  --mode single

az containerapp revision activate \
  --name <app-name> \
  --resource-group indsolse-dev-rg \
  --revision <previous-working-revision-name>
```
- **Customer:** https://isd-chat-customer-frontend.{region}.azurecontainerapps.io

**Note:** Replace `{region}` with actual region suffix (e.g., `redplant-675b33da.swedencentral`)

---

## 🐛 Common Issues & Troubleshooting

### Issue 1: "Network Error" in Frontend

**Symptoms:** Frontend shows "Network Error" when sending queries

**Cause:** Frontend has `localhost:8000` hardcoded instead of backend URL

**Solution:**
```bash
# 1. Remove .env file before building
cd frontend-react
rm .env

# 2. Rebuild with backend URL
BACKEND_URL=$(az containerapp show --name isd-chat-seller-backend --resource-group indsolse-dev-rg --query properties.configuration.ingress.fqdn -o tsv)

az acr build \
  --registry indsolsedevacr \
  --image isd-frontend-seller:v2.6-fixed-$(date +%s) \
  --file Dockerfile \
  --build-arg VITE_API_URL=https://$BACKEND_URL \
  .

# 3. Update container app with new image tag
NEW_TAG="v2.6-fixed-$(date +%s)"
az containerapp update \
  --name isd-chat-seller-frontend \
  --resource-group indsolse-dev-rg \
  --image "indsolsedevacr.azurecr.io/isd-frontend-seller:$NEW_TAG"
```

### Issue 2: CORS Errors

**Symptoms:** Browser console shows "CORS policy blocked"

**Solution:**
```bash
# Get frontend URL
FRONTEND_URL=$(az containerapp show --name isd-chat-seller-frontend --resource-group indsolse-dev-rg --query properties.configuration.ingress.fqdn -o tsv)

# Update backend CORS
az containerapp update \
  --name isd-chat-seller-backend \
  --resource-group indsolse-dev-rg \
  --set-env-vars ALLOWED_ORIGINS="https://$FRONTEND_URL,http://localhost:5173"
```

### Issue 3: Backend Returns 500 Error

**Symptoms:** API calls return HTTP 500

**Check Logs:**
```bash
# View backend logs
az containerapp logs show \
  --name isd-chat-seller-backend \
  --resource-group indsolse-dev-rg \
  --follow

# Common issues:
# - Missing environment variables (SQL_PASSWORD, AZURE_OPENAI_API_KEY)
# - Invalid SQL credentials
# - Azure OpenAI quota exceeded
```

### Issue 4: Duplicate Results (328 instead of 88)

**Symptoms:** Query 3 returns 328 duplicate solutions

**Cause:** DISTINCT enforcement not working in nl2sql_pipeline.py

**Solution:** This should already be fixed in the codebase. If not:
```bash
cd frontend-react/backend
# Verify DISTINCT fixes are present in nl2sql_pipeline.py
grep "CRITICAL SELLER MODE REMINDER" nl2sql_pipeline.py
# Should return matches - if not, contact Arturo for updated file
```

### Issue 5: Frontend Shows Old Revision

**Symptoms:** Deployment completes but frontend still shows old behavior

**Cause:** Azure didn't create new revision because image tag was reused

**Solution:**
```bash
# Always use unique image tags with timestamp
NEW_TAG="v2.6-$(date +%s)"

# Rebuild with unique tag
az acr build \
  --registry indsolsedevacr \
  --image isd-frontend-seller:$NEW_TAG \
  --file Dockerfile \
  --build-arg VITE_API_URL=https://$BACKEND_URL \
  .

# Update container app
az containerapp update \
  --name isd-chat-seller-frontend \
  --resource-group indsolse-dev-rg \
  --image "indsolsedevacr.azurecr.io/isd-frontend-seller:$NEW_TAG"
```

---

## 💰 Cost Management

### Daily Monitoring

```bash
# Check current month's cost
az consumption usage list \
  --start-date $(date -v-1d +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  --query "[?contains(instanceName,'indsolse')].{Resource:instanceName,Cost:pretaxCost}" \
  -o table
```

### Scale to Zero (Save Costs When Not Using)

```bash
# Stop all apps (scale to zero)
az containerapp update --name isd-chat-seller-backend --resource-group indsolse-dev-rg --min-replicas 0 --max-replicas 0
az containerapp update --name isd-chat-customer-backend --resource-group indsolse-dev-rg --min-replicas 0 --max-replicas 0
az containerapp update --name isd-chat-seller-frontend --resource-group indsolse-dev-rg --min-replicas 0 --max-replicas 0
az containerapp update --name isd-chat-customer-frontend --resource-group indsolse-dev-rg --min-replicas 0 --max-replicas 0

# Restart when needed
az containerapp update --name isd-chat-seller-backend --resource-group indsolse-dev-rg --min-replicas 1 --max-replicas 2
az containerapp update --name isd-chat-customer-backend --resource-group indsolse-dev-rg --min-replicas 1 --max-replicas 2
az containerapp update --name isd-chat-seller-frontend --resource-group indsolse-dev-rg --min-replicas 1 --max-replicas 2
az containerapp update --name isd-chat-customer-frontend --resource-group indsolse-dev-rg --min-replicas 1 --max-replicas 2
```

**Savings:** ~$200/month if stopped 20 days/month

### Delete Everything (End of Month)

```bash
#!/bin/bash
# Save as: deployment/cleanup-january-2026.sh

echo "⚠️  WARNING: This will delete all Azure resources in indsolse-dev-rg"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Delete resource group (deletes all resources inside)
az group delete \
  --name indsolse-dev-rg \
  --yes \
  --no-wait

echo "✅ Resource deletion initiated (async)"
echo "Resources will be fully deleted in ~5-10 minutes"
```

---

## 📊 Deployment Summary

### Created Resources

| Resource Type | Name | Purpose | Monthly Cost |
|---------------|------|---------|--------------|
| Resource Group | indsolse-dev-rg | Container for all resources | Free |
| Container Registry | indsolsedevacr | Docker image storage | $5 |
| Log Analytics | indsolse-dev-logs | Centralized logging | $15 |
| Container Apps Env | indsolse-dev-env | Host for container apps | Included |
| Backend (Seller) | isd-chat-seller-backend | Seller API | $9 |
| Backend (Customer) | isd-chat-customer-backend | Customer API | $9 |
| Frontend (Seller) | isd-chat-seller-frontend | Seller UI | $4.50 |
| Frontend (Customer) | isd-chat-customer-frontend | Customer UI | $4.50 |
| **Subtotal** | | | **$47** |
| Azure OpenAI | (external) | GPT-4.1 calls | $90-150 |
| **Total** | | | **$137-197** |

### Features Deployed

✅ **Dual-Mode Architecture**
- Seller mode: Partner rankings, detailed analytics
- Customer mode: Unbiased recommendations

✅ **Enhanced Features**
- SQL query formatting with line breaks
- Copilot-style citations [1], [2], [3]
- DISTINCT enforcement (no duplicates)
- Enhanced seller mode (individual rows, not aggregates)

✅ **Production-Ready**
- CORS configured
- Logging enabled
- Scaling configured
- Health endpoints working

---

## 📝 Quick Reference Commands

### Get All URLs

```bash
# Seller Frontend
az containerapp show --name isd-chat-seller-frontend --resource-group indsolse-dev-rg --query properties.configuration.ingress.fqdn -o tsv

# Seller Backend
az containerapp show --name isd-chat-seller-backend --resource-group indsolse-dev-rg --query properties.configuration.ingress.fqdn -o tsv

# Customer Frontend
az containerapp show --name isd-chat-customer-frontend --resource-group indsolse-dev-rg --query properties.configuration.ingress.fqdn -o tsv

# Customer Backend
az containerapp show --name isd-chat-customer-backend --resource-group indsolse-dev-rg --query properties.configuration.ingress.fqdn -o tsv
```

### View Logs

```bash
# Seller backend logs
az containerapp logs show --name isd-chat-seller-backend --resource-group indsolse-dev-rg --follow

# Seller frontend logs
az containerapp logs show --name isd-chat-seller-frontend --resource-group indsolse-dev-rg --follow
```

### Check Revisions

```bash
# List all revisions for seller frontend
az containerapp revision list \
  --name isd-chat-seller-frontend \
  --resource-group indsolse-dev-rg \
  --query "[].{Name:name,Active:properties.active,Created:properties.createdTime,Image:properties.template.containers[0].image}" \
  -o table
```

### Update Environment Variables

```bash
# Update seller backend
az containerapp update \
  --name isd-chat-seller-backend \
  --resource-group indsolse-dev-rg \
  --set-env-vars \
    AZURE_OPENAI_API_KEY="new-key" \
    SQL_PASSWORD="new-password"
```

---

## 🔄 Next Month Preparation

### Before Deletion (Save This Info)

```bash
# Export all URLs to file
echo "# Deployed URLs - $(date)" > deployment/urls-$(date +%Y-%m).txt
echo "Seller Frontend: https://$(az containerapp show --name isd-chat-seller-frontend --resource-group indsolse-dev-rg --query properties.configuration.ingress.fqdn -o tsv)" >> deployment/urls-$(date +%Y-%m).txt
echo "Seller Backend: https://$(az containerapp show --name isd-chat-seller-backend --resource-group indsolse-dev-rg --query properties.configuration.ingress.fqdn -o tsv)" >> deployment/urls-$(date +%Y-%m).txt
echo "Customer Frontend: https://$(az containerapp show --name isd-chat-customer-frontend --resource-group indsolse-dev-rg --query properties.configuration.ingress.fqdn -o tsv)" >> deployment/urls-$(date +%Y-%m).txt
echo "Customer Backend: https://$(az containerapp show --name isd-chat-customer-backend --resource-group indsolse-dev-rg --query properties.configuration.ingress.fqdn -o tsv)" >> deployment/urls-$(date +%Y-%m).txt

cat deployment/urls-$(date +%Y-%m).txt
```

### Automated Full Deployment Script

For next month, you can use this single script:

```bash
# Save as: deployment/deploy-full-infrastructure-feb-2026.sh
# Update credentials and run: bash deploy-full-infrastructure-feb-2026.sh
```

*(Script content would be a combination of all phases above)*

---

## 📞 Support & Contacts

- **Technical Lead:** Arturo Quiroga
- **Product Owner:** Will Casavan
- **GitHub Repository:** [Private - Contact Arturo]
- **Documentation:** See `ARCHITECTURE.md` for full system architecture

---

## ✅ Deployment Checklist

Use this checklist when recreating infrastructure:

- [ ] Phase 1: Core Infrastructure (15 min)
  - [ ] Resource Group created
  - [ ] Container Registry created
  - [ ] Log Analytics Workspace created
  - [ ] Container Apps Environment created

- [ ] Phase 2: Backend Deployment (30 min)
  - [ ] Seller backend built and deployed
  - [ ] Customer backend built and deployed
  - [ ] Health endpoints responding
  - [ ] Backend URLs saved

- [ ] Phase 3: Frontend Deployment (20 min)
  - [ ] `.env` file removed from frontend-react/
  - [ ] Seller frontend built with correct backend URL
  - [ ] Customer frontend built with correct backend URL
  - [ ] Both frontends deployed
  - [ ] Frontend URLs saved

- [ ] Phase 4: CORS Configuration (5 min)
  - [ ] Seller backend CORS updated
  - [ ] Customer backend CORS updated

- [ ] Phase 5: Verification (10 min)
  - [ ] All health checks passing
  - [ ] No `localhost:8000` in frontend bundles
  - [ ] Test queries working
  - [ ] Citations displaying correctly
  - [ ] SQL formatting working
  - [ ] DISTINCT enforcement working (88 results, not 328)

- [ ] Phase 6: Documentation
  - [ ] URLs saved to file
  - [ ] Credentials secured
  - [ ] Cost monitoring set up

---

**Last Deployment:** January 3, 2026  
**Next Scheduled:** February 1-3, 2026  
**Estimated Time:** 60-90 minutes  
**Estimated Cost:** $227-287/month
