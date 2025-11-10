param location string = 'swedencentral'
param environment string = 'dev'
param baseName string = 'indsolse'
param searchServiceName string
param notificationEmail string
@secure()
param sendGridApiKey string
param containerAppEnvName string = 'indsolse-dev-env'
param containerRegistryName string = 'indsolsedevacr'
param containerImage string = 'indsolsedevacr.azurecr.io/update-monitor:latest'

var containerAppName = '${baseName}-${environment}-updatemon-aca'

// Reference existing Container Apps Environment
resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-05-01' existing = {
  name: containerAppEnvName
}

// Reference existing search service
resource searchService 'Microsoft.Search/searchServices@2023-11-01' existing = {
  name: searchServiceName
}

// Container App with KEDA schedule trigger
resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8080
        transport: 'http'
        allowInsecure: false
      }
      registries: [
        {
          server: '${containerRegistryName}.azurecr.io'
          identity: 'system'
        }
      ]
      secrets: [
        {
          name: 'sendgrid-api-key'
          value: sendGridApiKey
        }
        {
          name: 'search-api-key'
          value: searchService.listAdminKeys().primaryKey
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'update-monitor'
          image: containerImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'AZURE_SEARCH_SERVICE'
              value: searchServiceName
            }
            {
              name: 'AZURE_SEARCH_INDEX'
              value: 'partner-solutions-integrated'
            }
            {
              name: 'AZURE_SEARCH_API_KEY'
              secretRef: 'search-api-key'
            }
            {
              name: 'NOTIFICATION_EMAIL_TO'
              value: notificationEmail
            }
            {
              name: 'NOTIFICATION_EMAIL_FROM'
              value: 'noreply@indsolse.com'
            }
            {
              name: 'SENDGRID_API_KEY'
              secretRef: 'sendgrid-api-key'
            }
            {
              name: 'WEBSITE_TIME_ZONE'
              value: 'UTC'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
}

// RBAC: Assign Search Index Data Reader role to container app
resource searchDataReaderRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, containerApp.id, 'SearchIndexDataReader')
  scope: searchService
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '1407120a-92aa-4202-b7e9-c0e197c71c8f')
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// RBAC: Assign AcrPull role to container app for pulling images
resource acrPullRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerRegistryName, containerApp.id, 'AcrPull')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

output containerAppName string = containerApp.name
output containerAppUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output containerAppId string = containerApp.id
output principalId string = containerApp.identity.principalId
