# Deployment Guide

Complete step-by-step guide to deploy the Industry Solutions Chat Assistant to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Azure Infrastructure Setup](#azure-infrastructure-setup)
3. [Configure Azure Services](#configure-azure-services)
4. [Deploy Backend API](#deploy-backend-api)
5. [Data Ingestion](#data-ingestion)
6. [Deploy Frontend Widget](#deploy-frontend-widget)
7. [Integration with Existing Website](#integration-with-existing-website)
8. [Testing & Validation](#testing--validation)
9. [Monitoring & Maintenance](#monitoring--maintenance)
10. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

### Required Access
- [ ] Azure subscription with Contributor access
- [ ] Access to existing Industry Solutions Directory website codebase
- [ ] GitHub repository access (for CI/CD)

### Local Development Tools
- [ ] Python 3.11+
- [ ] Node.js 18+
- [ ] Azure CLI (latest version)
- [ ] Git
- [ ] VS Code (recommended)

### Azure Quotas
Verify you have sufficient quota for:
- [ ] Azure OpenAI in your target region
- [ ] Azure AI Search
- [ ] Azure App Service

```bash
# Check Azure OpenAI availability
az cognitiveservices account list-skus \
  --kind OpenAI \
  --location eastus
```

---

## Azure Infrastructure Setup

### Option 1: Automated Deployment (Recommended)

```bash
# 1. Clone the repository
git clone <repository-url>
cd Industry-Solutions-Directory-PRO-Code

# 2. Login to Azure
az login
az account set --subscription "<your-subscription-id>"

# 3. Deploy infrastructure
cd infra
az deployment sub create \
  --name industry-solutions-chat-prod \
  --location eastus \
  --template-file main.bicep \
  --parameters environment=prod \
  --parameters location=eastus \
  --parameters searchSku=standard \
  --parameters appServiceSku=S1

# 4. Capture outputs
DEPLOYMENT_OUTPUTS=$(az deployment sub show \
  --name industry-solutions-chat-prod \
  --query properties.outputs -o json)

echo $DEPLOYMENT_OUTPUTS > deployment-outputs.json
```

**Deployment Time**: ~15-20 minutes

### Option 2: Manual Deployment

Follow the manual setup guide in `infra/README.md`

---

## Configure Azure Services

### 1. Azure OpenAI - Deploy Models

```bash
# Get resource name from deployment outputs
OPENAI_NAME=$(echo $DEPLOYMENT_OUTPUTS | jq -r '.openAiName.value')
RG_NAME=$(echo $DEPLOYMENT_OUTPUTS | jq -r '.resourceGroupName.value')

# Verify models are deployed
az cognitiveservices account deployment list \
  --name $OPENAI_NAME \
  --resource-group $RG_NAME

# Expected output:
# - gpt-4-1-mini (capacity: 10)
# - text-embedding-3-large (capacity: 10)
```

### 2. Azure AI Search - Create Index

The index will be created automatically by the data ingestion script in the next step.

### 3. Azure Cosmos DB - Verify Setup

```bash
COSMOS_NAME=$(echo $DEPLOYMENT_OUTPUTS | jq -r '.cosmosName.value')

# Verify database and container
az cosmosdb sql database show \
  --account-name $COSMOS_NAME \
  --resource-group $RG_NAME \
  --name industry-solutions-db

az cosmosdb sql container show \
  --account-name $COSMOS_NAME \
  --resource-group $RG_NAME \
  --database-name industry-solutions-db \
  --name chat-sessions
```

---

## Deploy Backend API

### 1. Prepare Application Code

```bash
cd ../backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests (optional)
pytest tests/ -v
```

### 2. Configure Environment Variables

```bash
# Get App Service name
APP_SERVICE_NAME=$(echo $DEPLOYMENT_OUTPUTS | jq -r '.appServiceName.value')

# All secrets are already configured via Key Vault references
# Verify configuration
az webapp config appsettings list \
  --name $APP_SERVICE_NAME \
  --resource-group $RG_NAME
```

### 3. Deploy to App Service

**Option A: Azure CLI**

```bash
# Build and deploy
az webapp up \
  --name $APP_SERVICE_NAME \
  --resource-group $RG_NAME \
  --runtime "PYTHON:3.11"

# Restart app
az webapp restart \
  --name $APP_SERVICE_NAME \
  --resource-group $RG_NAME
```

**Option B: GitHub Actions (Recommended for Production)**

1. Set up GitHub secrets:
   ```bash
   # Get publish profile
   az webapp deployment list-publishing-profiles \
     --name $APP_SERVICE_NAME \
     --resource-group $RG_NAME \
     --xml
   ```

2. Add secret to GitHub repository:
   - Go to Settings > Secrets > Actions
   - Add `AZURE_WEBAPP_PUBLISH_PROFILE` with the XML content

3. Push to main branch to trigger deployment

### 4. Verify Deployment

```bash
# Get App Service URL
APP_URL="https://${APP_SERVICE_NAME}.azurewebsites.net"

# Health check
curl ${APP_URL}/api/health

# Expected response:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "dependencies": {
#     "azure_ai_search": "healthy",
#     "azure_openai": "healthy",
#     "azure_cosmos_db": "healthy"
#   }
# }
```

---

## Data Ingestion

### 1. Run Initial Data Load

```bash
cd ../data-ingestion

# Set environment variables
export AZURE_SEARCH_ENDPOINT=$(echo $DEPLOYMENT_OUTPUTS | jq -r '.searchEndpoint.value')
export AZURE_SEARCH_API_KEY="<from-key-vault>"
export AZURE_OPENAI_ENDPOINT=$(echo $DEPLOYMENT_OUTPUTS | jq -r '.openAiEndpoint.value')
export AZURE_OPENAI_API_KEY="<from-key-vault>"

# Run ingestion
python ingest_data.py

# Verify index was created
SEARCH_NAME=$(echo $DEPLOYMENT_OUTPUTS | jq -r '.searchName.value')
az search index show \
  --name partner-solutions-index \
  --service-name $SEARCH_NAME \
  --resource-group $RG_NAME
```

### 2. Schedule Regular Updates

**Option A: Azure Function (Recommended)**

Create a timer-triggered Azure Function to run daily:

```python
# function_app.py
import azure.functions as func
from data_ingestion import DataIngestionPipeline

app = func.FunctionApp()

@app.timer_trigger(schedule="0 0 2 * * *", arg_name="myTimer")
def daily_data_sync(myTimer: func.TimerRequest):
    pipeline = DataIngestionPipeline()
    await pipeline.run()
```

**Option B: GitHub Actions Workflow**

```yaml
# .github/workflows/data-sync.yml
name: Daily Data Sync
on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM UTC daily

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run data ingestion
        run: |
          cd data-ingestion
          python ingest_data.py
```

---

## Deploy Frontend Widget

### 1. Build Widget

```bash
cd ../frontend

# Install dependencies
npm install

# Build for production
npm run build

# Output will be in dist/
# Files: chat-widget.js, chat-widget.css
```

### 2. Deploy to Azure CDN

```bash
# Create storage account for CDN origin
STORAGE_NAME="indsolchatwidget"
az storage account create \
  --name $STORAGE_NAME \
  --resource-group $RG_NAME \
  --location eastus \
  --sku Standard_LRS

# Create container
az storage container create \
  --name widgets \
  --account-name $STORAGE_NAME \
  --public-access blob

# Upload widget files
az storage blob upload-batch \
  --destination widgets \
  --source dist/ \
  --account-name $STORAGE_NAME

# Get blob URL
WIDGET_URL="https://${STORAGE_NAME}.blob.core.windows.net/widgets/chat-widget.js"
echo "Widget URL: $WIDGET_URL"
```

### 3. Configure CDN (Optional, Recommended)

```bash
# Create CDN profile and endpoint
az cdn profile create \
  --name indsolchat-cdn \
  --resource-group $RG_NAME \
  --sku Standard_Microsoft

az cdn endpoint create \
  --name indsolchat-widget \
  --profile-name indsolchat-cdn \
  --resource-group $RG_NAME \
  --origin ${STORAGE_NAME}.blob.core.windows.net

# CDN URL
CDN_URL="https://indsolchat-widget.azureedge.net/chat-widget.js"
```

---

## Integration with Existing Website

### 1. Coordinate with Website Team

Contact: Nat Collective (hosting partner)

Provide:
- Widget script URL
- API endpoint URL
- Integration instructions

### 2. Add Widget to Website

**Snippet to provide to web team:**

```html
<!-- Add before closing </body> tag -->
<script src="https://indsolchat-widget.azureedge.net/chat-widget.js"></script>
<script>
  window.IndustrySolutionsChat.init({
    apiEndpoint: 'https://indsolchat-prod-api.azurewebsites.net',
    theme: 'auto',
    primaryColor: '#0078d4',
    position: 'bottom-right'
  });
</script>
```

### 3. Test on Staging

Before production:
1. Deploy to website staging environment
2. Test all major workflows
3. Verify analytics tracking
4. Check mobile responsiveness

---

## Testing & Validation

### 1. Functional Testing

```bash
# Test chat endpoint
curl -X POST ${APP_URL}/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What healthcare solutions are available?",
    "filters": {
      "industries": ["Healthcare & Life Sciences"]
    }
  }'

# Test history endpoint
curl ${APP_URL}/api/chat/history/<session-id>

# Test facets endpoint
curl ${APP_URL}/api/facets
```

### 2. Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Run load test (100 concurrent requests)
ab -n 1000 -c 100 -p test-payload.json -T application/json \
  ${APP_URL}/api/chat
```

### 3. End-to-End Testing

Manual test scenarios:
- [ ] Simple query: "What AI solutions are available?"
- [ ] Filtered query: "Financial services compliance tools"
- [ ] Multi-turn conversation
- [ ] Session persistence across refreshes
- [ ] Error handling (invalid queries)
- [ ] Mobile device testing

---

## Monitoring & Maintenance

### 1. Configure Alerts

```bash
# CPU usage alert
az monitor metrics alert create \
  --name high-cpu \
  --resource-group $RG_NAME \
  --scopes $APP_SERVICE_ID \
  --condition "avg Percentage CPU > 80" \
  --window-size 5m \
  --evaluation-frequency 1m

# Error rate alert
az monitor metrics alert create \
  --name high-error-rate \
  --resource-group $RG_NAME \
  --scopes $APP_INSIGHTS_ID \
  --condition "avg failed requests > 10" \
  --window-size 5m
```

### 2. Application Insights Queries

Common queries for monitoring:

```kql
// Error rate
requests
| where timestamp > ago(1h)
| summarize 
    Total = count(),
    Failed = countif(success == false),
    ErrorRate = 100.0 * countif(success == false) / count()
| project ErrorRate

// Average response time
requests
| where timestamp > ago(1h)
| summarize AvgDuration = avg(duration)

// Popular queries
customEvents
| where name == "ChatQuery"
| summarize Count = count() by Query = tostring(customDimensions.message)
| top 10 by Count
```

### 3. Regular Maintenance Tasks

**Weekly:**
- [ ] Review error logs
- [ ] Check API response times
- [ ] Review user feedback

**Monthly:**
- [ ] Analyze usage patterns
- [ ] Review and optimize costs
- [ ] Update dependencies
- [ ] Backup configurations

---

## Rollback Procedures

### Quick Rollback (App Service)

```bash
# List deployment slots
az webapp deployment slot list \
  --name $APP_SERVICE_NAME \
  --resource-group $RG_NAME

# Swap back to previous slot
az webapp deployment slot swap \
  --name $APP_SERVICE_NAME \
  --resource-group $RG_NAME \
  --slot staging \
  --target-slot production
```

### Full Rollback (Infrastructure)

```bash
# Restore from previous deployment
az deployment sub create \
  --name industry-solutions-chat-rollback \
  --location eastus \
  --template-file main.bicep \
  --parameters @parameters/prod-backup.json
```

### Emergency Disable

If critical issues arise:

```bash
# Stop the App Service
az webapp stop \
  --name $APP_SERVICE_NAME \
  --resource-group $RG_NAME

# Remove widget from website (manual - contact web team)
```

---

## Post-Deployment Checklist

After deployment, verify:

- [ ] All health checks passing
- [ ] Data indexed in Azure AI Search
- [ ] Chat widget loads on website
- [ ] Conversations saved to Cosmos DB
- [ ] Application Insights receiving telemetry
- [ ] All alerts configured
- [ ] Documentation updated
- [ ] Team trained on monitoring

---

## Support & Escalation

### On-Call Rotation
- Primary: Arturo Quiroga
- Secondary: Thomas
- Escalation: Jason

### Critical Issues
1. Check Application Insights for errors
2. Review App Service logs
3. Verify Azure service health
4. Contact Microsoft Support if needed

### Contact Information
- Technical Lead: Arturo Quiroga
- Product Owner: Will Casavan
- Partner (Nat Collective): [Contact info]

---

## Additional Resources

- [Architecture Documentation](../ARCHITECTURE.md)
- [Cost Estimation](./COST_ESTIMATION.md)
- [API Documentation](http://${APP_URL}/docs)
- [Azure Status Page](https://status.azure.com)
