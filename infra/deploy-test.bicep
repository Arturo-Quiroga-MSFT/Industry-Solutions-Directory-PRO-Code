// Simplified deployment template for testing Industry Solutions Chat
// Single-file deployment with all resources inline for quick testing

targetScope = 'subscription'

@description('Environment name')
param environment string = 'dev'

@description('Primary Azure region')
param location string = 'swedencentral'

@description('Resource prefix (max 10 chars for naming constraints)')
@maxLength(10)
param resourcePrefix string = 'indsolchat'

// Generate unique suffix for globally unique resource names
var uniqueSuffix = substring(uniqueString(subscription().subscriptionId, resourcePrefix), 0, 6)
var resourceGroupName = '${resourcePrefix}-${environment}-rg'

// Resource Group
resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
  tags: {
    Environment: environment
    Project: 'Industry Solutions Chat'
    ManagedBy: 'Bicep'
  }
}

// Azure OpenAI Service
module openAiDeployment 'br/public:avm/res/cognitive-services/account:0.9.1' = {
  name: 'openai-deployment'
  scope: rg
  params: {
    name: '${resourcePrefix}-${environment}-ai-${uniqueSuffix}'
    location: location
    kind: 'OpenAI'
    customSubDomainName: '${resourcePrefix}-${environment}-ai-${uniqueSuffix}'
    sku: 'S0'
    deployments: [
      {
        name: 'gpt-4.1-mini'
        model: {
          format: 'OpenAI'
          name: 'gpt-4.1'
          version: '2025-04-14'
        }
        sku: {
          name: 'GlobalStandard'
          capacity: 100
        }
      }
      {
        name: 'text-embedding-3-large'
        model: {
          format: 'OpenAI'
          name: 'text-embedding-3-large'
          version: '1'
        }
        sku: {
          name: 'Standard'
          capacity: 100
        }
      }
    ]
    networkAcls: {
      defaultAction: 'Allow'
    }
    publicNetworkAccess: 'Enabled'
  }
}

// Azure AI Search
module searchDeployment 'br/public:avm/res/search/search-service:0.8.0' = {
  name: 'search-deployment'
  scope: rg
  params: {
    name: '${resourcePrefix}-${environment}-srch-${uniqueSuffix}'
    location: location
    sku: 'basic'
    replicaCount: 1
    partitionCount: 1
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
    disableLocalAuth: false
    publicNetworkAccess: 'Enabled'
  }
}

// Azure Cosmos DB
module cosmosDeployment 'br/public:avm/res/document-db/database-account:0.11.1' = {
  name: 'cosmos-deployment'
  scope: rg
  params: {
    name: '${resourcePrefix}-${environment}-db-${uniqueSuffix}'
    location: location
    disableLocalAuth: false
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    capabilitiesToAdd: [
      'EnableServerless'
    ]
    backupPolicyType: 'Continuous'
    backupPolicyContinuousTier: 'Continuous7Days'
    sqlDatabases: [
      {
        name: 'industry-solutions-db'
        containers: [
          {
            name: 'chat-sessions'
            paths: [
              '/sessionId'
            ]
            kind: 'Hash'
          }
        ]
      }
    ]
  }
}

// Log Analytics Workspace
module logAnalytics 'br/public:avm/res/operational-insights/workspace:0.9.1' = {
  name: 'loganalytics-deployment'
  scope: rg
  params: {
    name: '${resourcePrefix}-${environment}-logs'
    location: location
    skuName: 'PerGB2018'
  }
}

// Application Insights
module appInsights 'br/public:avm/res/insights/component:0.4.2' = {
  name: 'appinsights-deployment'
  scope: rg
  params: {
    name: '${resourcePrefix}-${environment}-insights'
    location: location
    workspaceResourceId: logAnalytics.outputs.resourceId
    applicationType: 'web'
  }
}

// Key Vault
module keyVault 'br/public:avm/res/key-vault/vault:0.11.0' = {
  name: 'keyvault-deployment'
  scope: rg
  params: {
    name: '${resourcePrefix}-${environment}-kv-${uniqueSuffix}'
    location: location
    sku: 'standard'
    enableRbacAuthorization: false
    enableVaultForDeployment: true
    enableVaultForTemplateDeployment: true
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
    publicNetworkAccess: 'Enabled'
  }
}

// Outputs for configuration
output resourceGroupName string = rg.name
output openAiEndpoint string = openAiDeployment.outputs.endpoint
output openAiName string = openAiDeployment.outputs.name
output searchEndpoint string = 'https://${searchDeployment.outputs.name}.search.windows.net'
output searchName string = searchDeployment.outputs.name
output cosmosEndpoint string = cosmosDeployment.outputs.endpoint
output cosmosAccountName string = cosmosDeployment.outputs.name
output keyVaultName string = keyVault.outputs.name
output keyVaultUri string = keyVault.outputs.uri
output appInsightsConnectionString string = appInsights.outputs.connectionString
output appInsightsInstrumentationKey string = appInsights.outputs.instrumentationKey
