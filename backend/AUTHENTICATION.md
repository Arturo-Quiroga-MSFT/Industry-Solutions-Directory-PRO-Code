# Authentication Guide

This backend uses **Azure CLI authentication (DefaultAzureCredential)** for all Azure services - no API keys required.

## Why Passwordless Authentication?

- **Security**: No secrets to manage, rotate, or accidentally commit
- **Simplicity**: Same credential works for all Azure services
- **Best Practice**: Follows Azure Well-Architected Framework security principles
- **Local & Cloud**: Works seamlessly in both development and production

## How It Works

The application uses `DefaultAzureCredential` from `azure-identity`, which automatically tries multiple authentication methods in this order:

1. **Environment Variables** (for production with managed identities)
2. **Azure CLI** (for local development - `az login`)
3. **Managed Identity** (when deployed to Azure App Service/Container Apps)
4. **Visual Studio Code** (if signed in)
5. **Azure PowerShell** (if signed in)

## Local Development Setup

### Step 1: Install Azure CLI

```bash
# macOS
brew install azure-cli

# Windows
winget install Microsoft.AzureCLI

# Linux
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

### Step 2: Login

```bash
az login
```

This opens a browser for authentication. After successful login, your credentials are cached locally.

### Step 3: Set Default Subscription (if you have multiple)

```bash
# List subscriptions
az account list --output table

# Set default
az account set --subscription "Your Subscription Name"
```

### Step 4: Verify Access

```bash
# Check current account
az account show

# Test Azure OpenAI access
az cognitiveservices account list
```

## Required RBAC Permissions

Grant these roles to your Azure identity (user or managed identity):

### Azure OpenAI Service

```bash
az role assignment create \
  --assignee <your-email-or-object-id> \
  --role "Cognitive Services OpenAI User" \
  --scope /subscriptions/<subscription-id>/resourceGroups/<rg-name>/providers/Microsoft.CognitiveServices/accounts/<openai-name>
```

### Azure AI Search

```bash
# For querying and writing to indexes
az role assignment create \
  --assignee <your-email-or-object-id> \
  --role "Search Index Data Contributor" \
  --scope /subscriptions/<subscription-id>/resourceGroups/<rg-name>/providers/Microsoft.Search/searchServices/<search-name>

# For managing search service
az role assignment create \
  --assignee <your-email-or-object-id> \
  --role "Search Service Contributor" \
  --scope /subscriptions/<subscription-id>/resourceGroups/<rg-name>/providers/Microsoft.Search/searchServices/<search-name>
```

### Azure Cosmos DB

```bash
az role assignment create \
  --assignee <your-email-or-object-id> \
  --role "Cosmos DB Built-in Data Contributor" \
  --scope /subscriptions/<subscription-id>/resourceGroups/<rg-name>/providers/Microsoft.DocumentDB/databaseAccounts/<cosmos-name>
```

## Service-Specific Implementation

### Azure OpenAI (SearchService & OpenAIService)

```python
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI

credential = DefaultAzureCredential()

# For embeddings and chat
client = AzureOpenAI(
    azure_endpoint=settings.azure_openai_endpoint,
    api_version=settings.azure_openai_api_version,
    azure_ad_token_provider=lambda: credential.get_token(
        "https://cognitiveservices.azure.com/.default"
    ).token
)
```

**Token Scope**: `https://cognitiveservices.azure.com/.default`

### Azure AI Search (SearchService)

```python
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient

credential = DefaultAzureCredential()

client = SearchClient(
    endpoint=settings.azure_search_endpoint,
    index_name=settings.azure_search_index_name,
    credential=credential
)
```

**Token Scope**: Automatically handled by SDK

### Azure Cosmos DB (CosmosDBService)

```python
from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient

credential = DefaultAzureCredential()

client = CosmosClient(
    url=settings.azure_cosmos_endpoint,
    credential=credential
)
```

**Token Scope**: Automatically handled by SDK

## Production Deployment

When deploying to Azure App Service or Container Apps, enable Managed Identity:

### Enable System-Assigned Managed Identity

```bash
az webapp identity assign \
  --name your-app-name \
  --resource-group your-rg
```

### Grant RBAC Permissions to Managed Identity

Use the same role assignment commands as above, but replace `<your-email-or-object-id>` with the managed identity's principal ID:

```bash
# Get the managed identity principal ID
PRINCIPAL_ID=$(az webapp identity show \
  --name your-app-name \
  --resource-group your-rg \
  --query principalId -o tsv)

# Grant permissions
az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Cognitive Services OpenAI User" \
  --scope /subscriptions/.../Microsoft.CognitiveServices/accounts/<openai-name>

# Repeat for Search and Cosmos DB
```

## Firewall Considerations

### Cosmos DB Public Network Access

If Cosmos DB has network restrictions:

1. **Add your public IP** (for local development):
   ```bash
   # Get your public IP
   MY_IP=$(curl -s ifconfig.me)
   
   # Add to Cosmos DB firewall
   az cosmosdb update \
     --name your-cosmos-name \
     --resource-group your-rg \
     --ip-range-filter $MY_IP
   ```

2. **For production**: Use VNet integration and private endpoints

### Azure OpenAI Network Access

If OpenAI has network restrictions, ensure:
- Public network access is enabled, OR
- Your App Service is VNet-integrated with private endpoint access

## Troubleshooting

### Error: "DefaultAzureCredential failed to retrieve a token"

**Cause**: Not logged in with Azure CLI or missing permissions

**Solution**:
```bash
# Re-login
az login

# Verify subscription
az account show

# Check your roles
az role assignment list --assignee <your-email> --output table
```

### Error: "Forbidden - Request originated from IP..."

**Cause**: Cosmos DB firewall blocking your IP

**Solution**: Add your public IP to the firewall (see Firewall Considerations above)

### Error: "Authorization failed for token"

**Cause**: Missing RBAC permissions

**Solution**: Grant required roles (see Required RBAC Permissions above)

### Token Expiration

Azure CLI tokens are valid for ~1 hour. If you see authentication errors after extended development sessions:

```bash
# Clear token cache and re-login
az account clear
az login
```

## Migration from API Keys

If migrating from API key authentication:

1. ✅ Remove API key environment variables from `.env`
2. ✅ Update code to use `DefaultAzureCredential` instead of `AzureKeyCredential`
3. ✅ Grant RBAC permissions
4. ✅ Test locally with `az login`
5. ✅ Enable managed identity in production
6. ✅ Disable local auth on Azure services (optional but recommended)

### Disable Local Auth (Optional)

For maximum security, disable API key access entirely:

```bash
# Cosmos DB
az cosmosdb update \
  --name your-cosmos-name \
  --resource-group your-rg \
  --disable-key-based-metadata-write-access true

# Azure OpenAI
az cognitiveservices account update \
  --name your-openai-name \
  --resource-group your-rg \
  --custom-domain your-openai-name \
  --disable-local-auth true

# Azure AI Search
az search service update \
  --name your-search-name \
  --resource-group your-rg \
  --auth-options aadOrApiKey
```

## References

- [Azure Identity SDK for Python](https://learn.microsoft.com/python/api/overview/azure/identity-readme)
- [DefaultAzureCredential Documentation](https://learn.microsoft.com/python/api/azure-identity/azure.identity.defaultazurecredential)
- [Azure RBAC Best Practices](https://learn.microsoft.com/azure/role-based-access-control/best-practices)
- [Managed Identities Overview](https://learn.microsoft.com/azure/active-directory/managed-identities-azure-resources/overview)
