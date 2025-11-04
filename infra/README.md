# Infrastructure Deployment Guide

This directory contains Bicep templates for deploying the Industry Solutions Chat infrastructure to Azure.

## Prerequisites

- Azure CLI installed and logged in
- Appropriate Azure subscription permissions
- Bicep CLI (included with Azure CLI)

## Quick Start

### 1. Login to Azure

```bash
az login
az account set --subscription "your-subscription-id"
```

### 2. Deploy Infrastructure

```bash
# Deploy to dev environment
az deployment sub create \
  --name industry-solutions-chat-dev \
  --location eastus \
  --template-file main.bicep \
  --parameters environment=dev \
  --parameters location=eastus

# Deploy to production
az deployment sub create \
  --name industry-solutions-chat-prod \
  --location eastus \
  --template-file main.bicep \
  --parameters environment=prod \
  --parameters location=eastus \
  --parameters searchSku=standard \
  --parameters appServiceSku=S1
```

### 3. Retrieve Outputs

```bash
# Get deployment outputs
az deployment sub show \
  --name industry-solutions-chat-dev \
  --query properties.outputs
```

## Directory Structure

```
infra/
├── main.bicep                  # Main orchestration template
├── parameters/
│   ├── dev.parameters.json    # Dev environment parameters
│   ├── staging.parameters.json
│   └── prod.parameters.json
└── modules/
    ├── openai.bicep           # Azure OpenAI module
    ├── search.bicep           # Azure AI Search module
    ├── cosmos.bicep           # Cosmos DB module
    ├── app-service-plan.bicep
    ├── app-service.bicep
    ├── key-vault.bicep
    └── app-insights.bicep
```

## Parameters

### Required Parameters

- `environment`: Environment name (dev, staging, prod)
- `location`: Azure region for deployment

### Optional Parameters

- `resourcePrefix`: Prefix for resource names (default: indsolchat)
- `openAiSku`: Azure OpenAI SKU (default: S0)
- `searchSku`: AI Search tier (default: basic)
- `appServiceSku`: App Service plan SKU (default: B1)

## Deployed Resources

The template deploys the following resources:

1. **Resource Group**: Container for all resources
2. **Azure OpenAI Service**: With GPT-4.1-mini and text-embedding-3-large deployments
3. **Azure AI Search**: For vector and hybrid search
4. **Azure Cosmos DB**: For storing chat sessions
5. **App Service Plan**: Hosting plan for the API
6. **App Service**: Python web app for the backend API
7. **Application Insights**: Monitoring and telemetry
8. **Key Vault**: Secure storage for secrets

## Post-Deployment Steps

After deployment completes:

1. **Update App Service Configuration**
   ```bash
   az webapp config appsettings set \
     --name <app-service-name> \
     --resource-group <resource-group> \
     --settings DEBUG=False
   ```

2. **Deploy Application Code**
   ```bash
   cd ../backend
   az webapp up --name <app-service-name>
   ```

3. **Run Data Ingestion**
   ```bash
   cd ../data-ingestion
   python ingest_data.py
   ```

4. **Verify Deployment**
   ```bash
   curl https://<app-service-name>.azurewebsites.net/api/health
   ```

## Cost Management

### Development Environment
- Estimated cost: $450-600/month
- Optimized for development and testing

### Production Environment
- Estimated cost: Scales based on traffic
- Includes redundancy and higher capacity

## Cleanup

To delete all resources:

```bash
az group delete --name indsolchat-dev-rg --yes --no-wait
```

## Troubleshooting

### Deployment Fails with Quota Error
**Error**: `Exceeded quota for deployment`

**Solution**: Request quota increase for Azure OpenAI in your subscription

### Search Service Creation Fails
**Error**: `Search service name not available`

**Solution**: Change the `resourcePrefix` parameter to a unique value

### App Service Deployment Issues
**Error**: `Cannot find runtime`

**Solution**: Ensure Python 3.11 runtime is available in your region

## Additional Resources

- [Azure OpenAI Documentation](https://learn.microsoft.com/azure/ai-services/openai/)
- [Azure AI Search Documentation](https://learn.microsoft.com/azure/search/)
- [Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
