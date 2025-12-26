# Dual-Mode Deployment Guide

## 🚀 Quick Deployment

This will deploy **TWO separate Azure Container Apps**:
1. **Customer Mode** - External-facing, vendor-neutral
2. **Seller Mode** - Internal Microsoft, partner intelligence

---

## Prerequisites

### 1. Set Required Environment Variables

```bash
# Azure OpenAI Credentials
export AZURE_OPENAI_API_KEY="your-openai-key-here"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_CHAT_DEPLOYMENT_NAME="gpt-4o-mini"  # or your deployment name

# SQL Database Password
export SQL_PASSWORD="your-sql-password-here"
```

### 2. Ensure Azure CLI is Logged In

```bash
az login
az account set --subscription "your-subscription-id"
```

---

## 🎯 Deploy

From the project root:

```bash
cd deployment
./deploy-dual-mode-testing.sh
```

**Deployment Time**: ~15-20 minutes

---

## 📦 What Gets Deployed

### Customer Mode Applications:
- **Backend**: `isd-chat-customer-backend` (APP_MODE=customer)
  - Port: 8000
  - Features: Vendor-neutral insights, no partner rankings
  
- **Frontend**: `isd-chat-customer-frontend`
  - Port: 80
  - Connected to customer backend

### Seller Mode Applications:
- **Backend**: `isd-chat-seller-backend` (APP_MODE=seller)
  - Port: 8000
  - Features: Partner intelligence, competitive insights
  
- **Frontend**: `isd-chat-seller-frontend`
  - Port: 80
  - Connected to seller backend

---

## ✅ Post-Deployment Verification

### 1. Check Health Endpoints

```bash
# Customer Mode
curl https://isd-chat-customer-backend.[region].azurecontainerapps.io/api/health

# Seller Mode
curl https://isd-chat-seller-backend.[region].azurecontainerapps.io/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "pipeline": "ready",
  "mode": "customer",  // or "seller"
  "timestamp": "2025-12-22T..."
}
```

### 2. Test in Browser

Open both URLs and verify the mode indicator in the top-right:
- Customer Mode: 🛡️ **CUSTOMER MODE**
- Seller Mode: 💾 **SELLER MODE**

### 3. Run a Test Query

Try the same question in both modes:
```
"What solutions help with anti-money laundering?"
```

**Customer Mode** should show:
- ✅ Capability-focused insights
- ❌ NO partner names in insights

**Seller Mode** should show:
- ✅ Partner names and rankings
- ✅ Competitive intelligence

---

## 🔍 Monitoring & Logs

### View Logs

```bash
# Customer Backend
az containerapp logs show \
  -n isd-chat-customer-backend \
  -g indsolse-dev-rg \
  --follow

# Seller Backend
az containerapp logs show \
  -n isd-chat-seller-backend \
  -g indsolse-dev-rg \
  --follow
```

### View Metrics

```bash
# List all container apps
az containerapp list -g indsolse-dev-rg -o table

# Show specific app details
az containerapp show \
  -n isd-chat-customer-backend \
  -g indsolse-dev-rg
```

---

## 🔄 Update Deployment

If you need to redeploy after code changes:

```bash
# Update just the images
az containerapp update \
  -n isd-chat-customer-backend \
  -g indsolse-dev-rg \
  --image indsolsedevacr.azurecr.io/isd-chat-backend:v2.9

az containerapp update \
  -n isd-chat-seller-backend \
  -g indsolse-dev-rg \
  --image indsolsedevacr.azurecr.io/isd-chat-backend:v2.9
```

Or re-run the full deployment script (it will update existing apps).

---

## 🗑️ Cleanup (When Testing Complete)

To remove all deployed resources:

```bash
# Delete Customer Mode
az containerapp delete -n isd-chat-customer-backend -g indsolse-dev-rg -y
az containerapp delete -n isd-chat-customer-frontend -g indsolse-dev-rg -y

# Delete Seller Mode
az containerapp delete -n isd-chat-seller-backend -g indsolse-dev-rg -y
az containerapp delete -n isd-chat-seller-frontend -g indsolse-dev-rg -y
```

---

## 🔐 Security Configuration

### What's Protected:
- ✅ All connections use HTTPS
- ✅ Environment variables encrypted at rest
- ✅ Database in READ-ONLY mode
- ✅ CORS restricted to respective frontends
- ✅ Secrets stored in Azure Key Vault (optional enhancement)

### Recommended Enhancements:
1. **Add Azure AD Authentication** for Seller Mode
2. **Configure Private Endpoints** for backend-to-database
3. **Enable Application Insights** for detailed monitoring
4. **Set up Alerts** for errors and performance

---

## 📊 Cost Estimate

Per day (both modes running):
- Backend (2 instances): ~$3-5/day
- Frontend (2 instances): ~$1-2/day
- **Total**: ~$4-7/day for testing

**For testing only**: Consider scaling down to 0 replicas when not in use:
```bash
az containerapp update -n [app-name] -g indsolse-dev-rg --min-replicas 0
```

---

## 🐛 Troubleshooting

### Issue: Deployment fails with "image not found"

**Solution**: Make sure ACR credentials are configured:
```bash
az acr login --name indsolsedevacr
```

### Issue: Backend shows "database connection error"

**Solution**: Check SQL password is correct and firewall allows Azure services:
```bash
az sql server firewall-rule create \
  --resource-group [your-rg] \
  --server mssoldir-prd-sql \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### Issue: Frontend can't connect to backend

**Solution**: Check CORS settings in backend environment variables:
```bash
az containerapp show -n isd-chat-customer-backend -g indsolse-dev-rg \
  --query properties.template.containers[0].env
```

### Issue: Mode indicator shows wrong mode

**Solution**: Verify APP_MODE environment variable:
```bash
az containerapp show -n [app-name] -g indsolse-dev-rg \
  --query "properties.template.containers[0].env[?name=='APP_MODE']"
```

---

## 📞 Support

**For deployment issues**: Check Azure Container Apps documentation
**For application issues**: Review backend logs with `az containerapp logs show`

---

## ✅ Deployment Checklist

Before sharing with testers:

- [ ] Both modes deployed successfully
- [ ] Health endpoints return `"status": "healthy"`
- [ ] Customer mode shows vendor-neutral insights
- [ ] Seller mode shows partner rankings
- [ ] Mode indicators display correctly
- [ ] Export features work (JSON/Markdown)
- [ ] Token tracking displays correctly
- [ ] URLs added to TESTING_GUIDE.md
- [ ] Team notification sent

---

**Ready to Deploy?** Run `./deploy-dual-mode-testing.sh` 🚀
