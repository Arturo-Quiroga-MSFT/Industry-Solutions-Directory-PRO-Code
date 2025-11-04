// Main Bicep template for Industry Solutions Chat infrastructure
// Deploys Azure OpenAI, AI Search, Cosmos DB, and App Service

targetScope = 'subscription'

@description('Environment name (dev, staging, prod)')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Primary Azure region for resources')
param location string = 'eastus'

@description('Resource name prefix')
param resourcePrefix string = 'indsolchat'

@description('Azure OpenAI SKU')
@allowed(['S0'])
param openAiSku string = 'S0'

@description('Azure AI Search SKU')
@allowed(['basic', 'standard', 'standard2', 'standard3'])
param searchSku string = 'basic'

@description('App Service SKU')
@allowed(['B1', 'B2', 'S1', 'P1V3'])
param appServiceSku string = 'B1'

// Variables
var resourceGroupName = '${resourcePrefix}-${environment}-rg'
var openAiName = '${resourcePrefix}-${environment}-openai'
var searchName = '${resourcePrefix}-${environment}-search'
var cosmosName = '${resourcePrefix}-${environment}-cosmos'
var appServicePlanName = '${resourcePrefix}-${environment}-plan'
var appServiceName = '${resourcePrefix}-${environment}-api'
var keyVaultName = '${resourcePrefix}-${environment}-kv'
var appInsightsName = '${resourcePrefix}-${environment}-insights'

// Resource Group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: resourceGroupName
  location: location
  tags: {
    Environment: environment
    Project: 'Industry Solutions Chat'
    ManagedBy: 'Bicep'
  }
}

// Azure OpenAI Service
module openAi 'modules/openai.bicep' = {
  name: 'openai-deployment'
  scope: rg
  params: {
    name: openAiName
    location: location
    sku: openAiSku
    deployments: [
      {
        name: 'gpt-4-1-mini'
        model: {
          name: 'gpt-4'
          version: '0125-preview'
        }
        sku: {
          name: 'Standard'
          capacity: 10
        }
      }
      {
        name: 'text-embedding-3-large'
        model: {
          name: 'text-embedding-3-large'
          version: '1'
        }
        sku: {
          name: 'Standard'
          capacity: 10
        }
      }
    ]
  }
}

// Azure AI Search
module search 'modules/search.bicep' = {
  name: 'search-deployment'
  scope: rg
  params: {
    name: searchName
    location: location
    sku: searchSku
    replicaCount: environment == 'prod' ? 2 : 1
    partitionCount: 1
  }
}

// Azure Cosmos DB
module cosmos 'modules/cosmos.bicep' = {
  name: 'cosmos-deployment'
  scope: rg
  params: {
    name: cosmosName
    location: location
    databaseName: 'industry-solutions-db'
    containerName: 'chat-sessions'
    serverless: environment != 'prod'
  }
}

// App Service Plan
module appServicePlan 'modules/app-service-plan.bicep' = {
  name: 'app-service-plan-deployment'
  scope: rg
  params: {
    name: appServicePlanName
    location: location
    sku: appServiceSku
  }
}

// App Service (API)
module appService 'modules/app-service.bicep' = {
  name: 'app-service-deployment'
  scope: rg
  params: {
    name: appServiceName
    location: location
    appServicePlanId: appServicePlan.outputs.id
    appSettings: [
      {
        name: 'AZURE_OPENAI_ENDPOINT'
        value: openAi.outputs.endpoint
      }
      {
        name: 'AZURE_OPENAI_API_KEY'
        value: '@Microsoft.KeyVault(SecretUri=${keyVault.outputs.secretUriOpenAiKey})'
      }
      {
        name: 'AZURE_SEARCH_ENDPOINT'
        value: search.outputs.endpoint
      }
      {
        name: 'AZURE_SEARCH_API_KEY'
        value: '@Microsoft.KeyVault(SecretUri=${keyVault.outputs.secretUriSearchKey})'
      }
      {
        name: 'AZURE_COSMOS_ENDPOINT'
        value: cosmos.outputs.endpoint
      }
      {
        name: 'AZURE_COSMOS_KEY'
        value: '@Microsoft.KeyVault(SecretUri=${keyVault.outputs.secretUriCosmosKey})'
      }
      {
        name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
        value: appInsights.outputs.connectionString
      }
    ]
  }
}

// Application Insights
module appInsights 'modules/app-insights.bicep' = {
  name: 'app-insights-deployment'
  scope: rg
  params: {
    name: appInsightsName
    location: location
  }
}

// Key Vault
module keyVault 'modules/key-vault.bicep' = {
  name: 'key-vault-deployment'
  scope: rg
  params: {
    name: keyVaultName
    location: location
    secrets: [
      {
        name: 'openai-api-key'
        value: openAi.outputs.apiKey
      }
      {
        name: 'search-api-key'
        value: search.outputs.adminKey
      }
      {
        name: 'cosmos-key'
        value: cosmos.outputs.primaryKey
      }
    ]
  }
}

// Outputs
output resourceGroupName string = rg.name
output openAiEndpoint string = openAi.outputs.endpoint
output searchEndpoint string = search.outputs.endpoint
output cosmosEndpoint string = cosmos.outputs.endpoint
output appServiceUrl string = appService.outputs.defaultHostname
output appInsightsInstrumentationKey string = appInsights.outputs.instrumentationKey
