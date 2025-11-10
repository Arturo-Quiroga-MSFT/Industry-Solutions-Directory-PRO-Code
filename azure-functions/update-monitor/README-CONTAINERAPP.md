# Update Monitor - Container App Deployment

This is an alternative deployment approach using Azure Container Apps instead of Azure Functions.

## Benefits of Container Apps

- ✅ No storage account initialization issues
- ✅ Native VNet integration without SCM/Kudu complications
- ✅ KEDA cron trigger for scheduled execution
- ✅ Simpler deployment (Docker container)
- ✅ Scales to zero when not running
- ✅ Works with existing VNet and subnets

## Deployment Steps

### 1. Build and Push Container Image

```bash
# Login to Azure Container Registry (or use your existing registry)
az acr login --name <your-acr-name>

# Build and push the image
cd azure-functions/update-monitor
docker build -t <your-acr-name>.azurecr.io/update-monitor:latest .
docker push <your-acr-name>.azurecr.io/update-monitor:latest
```

### 2. Deploy Infrastructure

```bash
cd ../../infra
az deployment group create \
  --resource-group indsolse-dev-rg \
  --template-file container-app-monitor.bicep \
  --parameters \
    location=swedencentral \
    environment=dev \
    baseName=indsolse \
    searchServiceName=indsolse-dev-srch-okumlm \
    notificationEmail="arturo.quiroga@microsoft.com" \
    vnetName=indsolse-dev-vnet \
    acaSubnetName=aca-subnet \
    containerImage="<your-acr-name>.azurecr.io/update-monitor:latest"
```

### 3. Update Container Image (subsequent deployments)

```bash
az containerapp update \
  --name indsolse-dev-updatemon-aca \
  --resource-group indsolse-dev-rg \
  --image <your-acr-name>.azurecr.io/update-monitor:latest
```

## Schedule Configuration

The container app is configured with a KEDA cron trigger:
- **Schedule**: Monday at 9 AM UTC
- **Scale**: 0 to 1 replicas
- **Runtime**: Runs for 1 hour window, then scales to zero

## Manual Trigger

You can manually trigger the update check via HTTP:

```bash
curl -X POST https://<your-app-url>.azurecontainerapps.io/api/update-check
```

## Monitoring

View logs:
```bash
az containerapp logs show \
  --name indsolse-dev-updatemon-aca \
  --resource-group indsolse-dev-rg \
  --follow
```

## Cost Comparison

- **Azure Functions EP1**: ~$150/month
- **Container Apps**: ~$0-5/month (scales to zero, minimal compute)
