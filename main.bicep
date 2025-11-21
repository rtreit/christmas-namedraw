param location string = resourceGroup().location
param appName string = 'buddy-namedraw-${uniqueString(resourceGroup().id)}'

@description('The SKU of App Service Plan')
param skuName string = 'F1'

@secure()
param buddyPassword string
@secure()
param flaskSecretKey string
@secure()
param refreshToken string
param clientId string
param tenant string
param redirectUri string

resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: '${appName}-plan'
  location: location
  sku: {
    name: skuName
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

resource webApp 'Microsoft.Web/sites@2022-03-01' = {
  name: appName
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appSettings: [
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'BUDDY_PASSWORD'
          value: buddyPassword
        }
        {
          name: 'FLASK_SECRET_KEY'
          value: flaskSecretKey
        }
        {
          name: 'REFRESH_TOKEN'
          value: refreshToken
        }
        {
          name: 'NAMEDRAW_CLIENT_ID'
          value: clientId
        }
        {
          name: 'NAMEDRAW_TENANT'
          value: tenant
        }
        {
          name: 'NAMEDRAW_REDIRECT_URI'
          value: redirectUri
        }
      ]
    }
  }
}

output appUrl string = 'https://${webApp.properties.defaultHostName}'
