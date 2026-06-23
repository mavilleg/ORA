param location string = resourceGroup().location
param containerImage string = 'ora:latest'
param containerPort int = 8000

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2021-12-01-preview' = {
  name: 'log-${uniqueString(resourceGroup().id)}'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource cosmosDb 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: 'cosmos-${uniqueString(resourceGroup().id)}'
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
      }
    ]
    databaseAccountOfferType: 'Standard'
  }
}

resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-04-01-preview' = {
  name: 'env-${uniqueString(resourceGroup().id)}'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: reference(logAnalytics.id, '2021-12-01-preview').customerId
        sharedKey: listKeys(logAnalytics.id, '2021-12-01-preview').primarySharedKey
      }
    }
  }
}

resource containerApp 'Microsoft.App/containerApps@2023-04-01-preview' = {
  name: 'ora-api'
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: containerPort
        transport: 'auto'
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
    }
    template: {
      containers: [
        {
          image: containerImage
          name: 'ora'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'ARENA_MODELS'
              value: 'gpt4o_mini,phi4'
            }
            {
              name: 'COSMOS_ENDPOINT'
              value: reference(cosmosDb.id, '2023-04-15').documentEndpoint
            }
            {
              name: 'COSMOS_DB'
              value: 'ora-db'
            }
            {
              name: 'USE_ENTRA_ID'
              value: 'true'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

output containerAppUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
