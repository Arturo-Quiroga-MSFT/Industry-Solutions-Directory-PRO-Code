# Azure Functions: ISD Update Monitor

**Owner:** Arturo Quiroga, Principal Industry Solutions Architect, Microsoft  
**Purpose:** Timer-triggered Azure Function to automatically monitor ISD website for updates  
**Last Updated:** November 8, 2025

---

## Overview

This Azure Function monitors the Microsoft Industry Solutions Directory (ISD) website for changes and sends notifications when new, modified, or removed solutions are detected.

**Features:**
- ⏰ **Automated Weekly Checks** - Runs every Monday at 9:00 AM UTC
- 🔍 **Change Detection** - MD5 hash comparison to identify modifications
- 📢 **Teams Notifications** - Sends alerts to Microsoft Teams via webhook
- 🔐 **Managed Identity** - Secure access to Azure Search without API keys
- 📊 **Application Insights** - Comprehensive monitoring and logging
- 🌐 **HTTP Endpoint** - Manual trigger option for on-demand checks

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Azure Function App                         │
│                  (Consumption Plan - Linux)                  │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Timer Trigger                                     │    │
│  │  Schedule: 0 0 9 * * 1 (Mon 9AM UTC)              │    │
│  │  - Fetch ISD solutions                            │    │
│  │  - Fetch indexed solutions                        │    │
│  │  - Compare & detect changes                       │    │
│  │  - Send Teams notification                        │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  HTTP Trigger (Manual)                            │    │
│  │  GET/POST /api/update-check                       │    │
│  │  - On-demand update check                         │    │
│  └────────────────────────────────────────────────────┘    │
└────────────┬────────────────┬──────────────────────────────┘
             │                │
             ▼                ▼
    ┌────────────────┐  ┌────────────────┐
    │  Azure Search  │  │   Teams API    │
    │  Index Query   │  │   Webhook      │
    └────────────────┘  └────────────────┘
```

---

## Project Structure

```
azure-functions/update-monitor/
├── function_app.py           # Main function code
├── requirements.txt          # Python dependencies
├── host.json                # Function App configuration
├── local.settings.json      # Local development settings (git-ignored)
├── .gitignore              # Git ignore rules
├── .funcignore             # Deployment ignore rules
└── README.md               # This file
```

---

## Prerequisites

### Local Development
- Python 3.11+
- Azure Functions Core Tools v4
- Azure CLI
- VS Code with Azure Functions extension (recommended)

### Azure Resources
- Azure Function App (Consumption Plan)
- Azure Search Service (existing)
- Azure Storage Account (for Function App state)
- Application Insights (for monitoring)
- Microsoft Teams webhook (optional but recommended)

---

## Setup Instructions

### 1. Local Development Setup

```bash
# Navigate to function directory
cd azure-functions/update-monitor

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Azure Functions Core Tools (if not already installed)
# On macOS:
brew tap azure/functions
brew install azure-functions-core-tools@4

# On Windows:
npm install -g azure-functions-core-tools@4 --unsafe-perm true
```

### 2. Configure Local Settings

Create `local.settings.json` (already git-ignored):

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_SEARCH_SERVICE": "your-search-service-name",
    "AZURE_SEARCH_KEY": "your-search-api-key",
    "AZURE_SEARCH_INDEX": "partner-solutions-integrated",
    "TEAMS_WEBHOOK_URL": "https://your-teams-webhook-url",
    "NOTIFICATION_EMAIL": "your-email@example.com"
  }
}
```

### 3. Test Locally

```bash
# Start Azurite (local storage emulator) in a separate terminal
azurite --silent

# Start the function locally
func start

# Test the HTTP endpoint
curl http://localhost:7071/api/update-check
```

---

## Azure Deployment

### Option 1: Deploy Infrastructure with Bicep

```bash
# Navigate to infra directory
cd ../../infra

# Set variables
RESOURCE_GROUP="indsolse-dev-rg"
LOCATION="swedencentral"
SEARCH_SERVICE="your-search-service"
TEAMS_WEBHOOK="https://your-webhook-url"

# Deploy Function App infrastructure
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file function-app.bicep \
  --parameters \
    location=$LOCATION \
    environment=dev \
    searchServiceName=$SEARCH_SERVICE \
    teamsWebhookUrl=$TEAMS_WEBHOOK \
    notificationEmail="your-email@example.com"

# Note the function app name from outputs
FUNCTION_APP_NAME=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name function-app \
  --query properties.outputs.functionAppName.value \
  --output tsv)

echo "Function App Name: $FUNCTION_APP_NAME"
```

### Option 2: Manual Deployment via CLI

```bash
# Create resource group (if not exists)
az group create \
  --name indsolse-dev-rg \
  --location swedencentral

# Create storage account
az storage account create \
  --name indsolsedevupdatestorage \
  --resource-group indsolse-dev-rg \
  --location swedencentral \
  --sku Standard_LRS

# Create Function App
az functionapp create \
  --resource-group indsolse-dev-rg \
  --name indsolse-dev-updatemon-func \
  --storage-account indsolsedevupdatestorage \
  --consumption-plan-location swedencentral \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --os-type linux \
  --assign-identity

# Configure app settings
az functionapp config appsettings set \
  --name indsolse-dev-updatemon-func \
  --resource-group indsolse-dev-rg \
  --settings \
    AZURE_SEARCH_SERVICE="your-search-service" \
    AZURE_SEARCH_INDEX="partner-solutions-integrated" \
    TEAMS_WEBHOOK_URL="https://your-webhook" \
    NOTIFICATION_EMAIL="your-email@example.com"
```

### Option 3: Deploy Code via GitHub Actions

The workflow `.github/workflows/deploy-functions.yml` automatically deploys when changes are pushed to `main` branch.

**Required GitHub Secrets:**
- `AZURE_CREDENTIALS` - Azure service principal credentials
- `AZURE_RESOURCE_GROUP` - Resource group name
- `AZURE_SEARCH_SERVICE` - Search service name
- `TEAMS_WEBHOOK_URL` - Teams webhook URL
- `NOTIFICATION_EMAIL` - Notification email

```bash
# Create service principal for GitHub Actions
az ad sp create-for-rbac \
  --name "github-indsolse-functions" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/indsolse-dev-rg \
  --sdk-auth

# Add the JSON output to GitHub Secrets as AZURE_CREDENTIALS
```

### Option 4: Deploy via VS Code

1. Install "Azure Functions" extension in VS Code
2. Sign in to Azure
3. Right-click on `function_app.py`
4. Select "Deploy to Function App"
5. Choose your subscription and function app
6. Confirm deployment

---

## Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `AZURE_SEARCH_SERVICE` | Yes | Name of Azure Search service | `indsolse-dev-search` |
| `AZURE_SEARCH_KEY` | No* | Search service API key | `abc123...` |
| `AZURE_SEARCH_INDEX` | Yes | Search index name | `partner-solutions-integrated` |
| `TEAMS_WEBHOOK_URL` | No | Teams incoming webhook URL | `https://outlook.office.com/webhook/...` |
| `NOTIFICATION_EMAIL` | No | Email for notifications | `admin@example.com` |

\* *Not required when using Managed Identity (recommended for production)*

### Timer Trigger Schedule

The function runs on a CRON schedule defined in `function_app.py`:

```python
@app.timer_trigger(
    schedule="0 0 9 * * 1",  # Every Monday at 9:00 AM UTC
    ...
)
```

**CRON Format:** `{second} {minute} {hour} {day} {month} {day-of-week}`

**Examples:**
- `0 0 9 * * 1` - Every Monday at 9 AM
- `0 0 6 * * 1-5` - Every weekday at 6 AM
- `0 0 */6 * * *` - Every 6 hours
- `0 0 0 1 * *` - First day of every month

---

## Usage

### Automatic Weekly Execution

The function runs automatically every Monday at 9:00 AM UTC. Check Application Insights for execution logs.

### Manual Execution via HTTP

```bash
# Get function key
FUNCTION_KEY=$(az functionapp keys list \
  --name indsolse-dev-updatemon-func \
  --resource-group indsolse-dev-rg \
  --query functionKeys.default \
  --output tsv)

# Trigger update check
curl -X POST \
  "https://indsolse-dev-updatemon-func.azurewebsites.net/api/update-check?code=$FUNCTION_KEY"
```

### Manual Execution via Portal

1. Navigate to Function App in Azure Portal
2. Select "Functions" → "isd_update_check_http"
3. Click "Code + Test"
4. Click "Test/Run"
5. Click "Run"

---

## Monitoring

### Application Insights

View function execution logs, errors, and performance metrics:

```bash
# View recent logs
az monitor app-insights query \
  --app indsolse-dev-updatemon-insights \
  --analytics-query "traces | where timestamp > ago(1h) | order by timestamp desc"

# View function executions
az monitor app-insights query \
  --app indsolse-dev-updatemon-insights \
  --analytics-query "requests | where timestamp > ago(7d) | summarize count() by bin(timestamp, 1d)"
```

### Teams Notifications

When changes are detected, a notification is sent to Teams:

**No Changes:**
```
✅ ISD Update Check Complete
No changes detected
The search index is up to date with the ISD website.
```

**Changes Detected:**
```
📊 ISD Website Update Detected
⚠️ 15 changes detected

🆕 New Solutions: 5
✏️ Modified Solutions: 8
🗑️ Removed Solutions: 2

[View ISD Website]
```

### Log Queries

Access logs via Azure Portal or CLI:

```bash
# Recent executions
az functionapp log tail \
  --name indsolse-dev-updatemon-func \
  --resource-group indsolse-dev-rg

# Live streaming logs
func azure functionapp logstream indsolse-dev-updatemon-func
```

---

## Troubleshooting

### Common Issues

#### 1. Function Not Triggering

**Check schedule:**
```bash
# View function configuration
az functionapp config show \
  --name indsolse-dev-updatemon-func \
  --resource-group indsolse-dev-rg
```

**Verify timer is enabled:**
- Check `host.json` has `"useMonitor": true`
- Function must be deployed (not just saved)

#### 2. Search Service Connection Errors

**Verify managed identity permissions:**
```bash
# Get function's managed identity
PRINCIPAL_ID=$(az functionapp identity show \
  --name indsolse-dev-updatemon-func \
  --resource-group indsolse-dev-rg \
  --query principalId \
  --output tsv)

# Assign Search Index Data Reader role
az role assignment create \
  --role "Search Index Data Reader" \
  --assignee $PRINCIPAL_ID \
  --scope /subscriptions/{sub-id}/resourceGroups/{rg}/providers/Microsoft.Search/searchServices/{search-service}
```

#### 3. Teams Notification Not Sending

**Verify webhook URL:**
```bash
# Test webhook directly
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"text": "Test message"}' \
  "https://your-teams-webhook-url"
```

**Check function logs:**
```bash
az monitor app-insights query \
  --app indsolse-dev-updatemon-insights \
  --analytics-query "traces | where message contains 'Teams' | order by timestamp desc"
```

#### 4. Python Dependencies Missing

**Redeploy with build:**
```bash
az functionapp deployment source config-zip \
  --resource-group indsolse-dev-rg \
  --name indsolse-dev-updatemon-func \
  --src function-package.zip \
  --build-remote true
```

---

## Cost Estimation

### Consumption Plan Pricing

- **Execution Time:** ~2-3 minutes per run
- **Weekly Executions:** 4 runs/month (every Monday)
- **Memory:** 512 MB
- **Free Grant:** 400,000 GB-s/month, 1M executions/month

**Estimated Monthly Cost:** **~$0.00** (within free tier)

### Associated Costs

- **Application Insights:** ~$2-5/month (minimal data)
- **Storage Account:** ~$1/month (minimal storage)

**Total Estimated Cost:** **~$3-6/month**

---

## Security Best Practices

1. ✅ **Use Managed Identity** - Avoid storing API keys
2. ✅ **HTTPS Only** - Enforce TLS 1.2+
3. ✅ **Function-level Auth** - Protect HTTP endpoints with function keys
4. ✅ **Secrets in Key Vault** - Store Teams webhook in Key Vault
5. ✅ **RBAC** - Least privilege access to Azure Search
6. ✅ **Network Isolation** - Consider VNet integration for production

---

## Maintenance

### Regular Tasks

**Weekly:**
- Review Teams notifications
- Check for failed executions in App Insights

**Monthly:**
- Review cost and usage metrics
- Update Python dependencies if needed

**Quarterly:**
- Review and update CRON schedule if needed
- Test manual HTTP endpoint
- Review security settings

### Updating Dependencies

```bash
# Update requirements.txt
cd azure-functions/update-monitor
pip install --upgrade azure-functions azure-search-documents
pip freeze > requirements.txt

# Redeploy function
func azure functionapp publish indsolse-dev-updatemon-func
```

---

## Future Enhancements

- 📧 **Email Notifications** - Add SendGrid/Azure Communication Services
- 🔄 **Auto Re-indexing** - Trigger ingestion pipeline when changes detected
- 📊 **Historical Tracking** - Store change history in Cosmos DB
- 🎯 **Intelligent Alerting** - Only alert on significant changes
- 🌍 **Multi-region** - Deploy functions to multiple regions
- 📱 **Mobile Notifications** - Push notifications via Azure Notification Hubs

---

## Support

**Owner:** Arturo Quiroga  
**Email:** arturo.quiroga@microsoft.com  
**Documentation:** See [FUTURE_ENHANCEMENTS.md](../../FUTURE_ENHANCEMENTS.md)

---

**Last Updated:** November 8, 2025
