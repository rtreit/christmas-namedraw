# deploy.ps1
$ErrorActionPreference = "Stop"

# Configuration
$ResourceGroup = "buddy-eastus2"
$AppName = "buddy-namedraw-$((Get-Random).ToString())" # Unique name
$Location = "eastus2" # Added quota here
$Sku = "F1" # Free Tier

# Read Secrets from .env
if (Test-Path .env) {
    Write-Host "Reading secrets from .env..."
    Get-Content .env | ForEach-Object {
        if ($_ -match "^(.*?)=(.*)$") {
            Set-Variable -Name $matches[1] -Value $matches[2] -Scope Global
        }
    }
} else {
    Write-Warning ".env file not found. Please ensure BUDDY_PASSWORD and FLASK_SECRET_KEY are set."
}

# Read Refresh Token
$RefreshTokenFile = "data/refresh_token.json"
if (Test-Path $RefreshTokenFile) {
    $RefreshTokenJson = Get-Content $RefreshTokenFile | ConvertFrom-Json
    $RefreshToken = $RefreshTokenJson.refresh_token
} else {
    Write-Warning "Refresh token file not found at $RefreshTokenFile"
}

# Read Config for Client ID/Tenant
$ConfigFile = "config.json"
if (Test-Path $ConfigFile) {
    $ConfigJson = Get-Content $ConfigFile | ConvertFrom-Json
    $ClientId = $ConfigJson.client_id
    $Tenant = $ConfigJson.tenant
    $RedirectUri = $ConfigJson.redirect_uri
} else {
    Write-Warning "config.json not found."
}

# 1. Prepare Deployment Artifact
Write-Host "Preparing deployment artifact..."
if (Test-Path deploy) { Remove-Item deploy -Recurse -Force }
New-Item -ItemType Directory -Path deploy | Out-Null

# Generate requirements.txt
Write-Host "Generating requirements.txt..."
uv export --format requirements.txt --no-hashes --no-dev -o deploy/requirements.txt

# Remove editable install of the project itself to prevent Azure build errors
(Get-Content deploy/requirements.txt) | Where-Object { $_ -notmatch "^-e \." } | Set-Content deploy/requirements.txt

# Copy Files
Copy-Item app.py deploy/
Copy-Item pyproject.toml deploy/
Copy-Item README.md deploy/ # Often needed by pyproject.toml
Copy-Item -Recurse namedraw deploy/
Copy-Item -Recurse static deploy/
Copy-Item -Recurse templates deploy/
if (Test-Path data/participants.json) {
    if (-not (Test-Path deploy/data)) { New-Item -ItemType Directory -Path deploy/data | Out-Null }
    Copy-Item data/participants.json deploy/data/
}
if (Test-Path data/scenarios.json) {
    if (-not (Test-Path deploy/data)) { New-Item -ItemType Directory -Path deploy/data | Out-Null }
    Copy-Item data/scenarios.json deploy/data/
}

# Zip
Write-Host "Zipping..."
$ZipFile = "deploy.zip"
if (Test-Path $ZipFile) { Remove-Item $ZipFile }
Compress-Archive -Path deploy/* -DestinationPath $ZipFile

# 2. Create Azure Resources (Bicep)
Write-Host "Creating Resource Group '$ResourceGroup'..."
az group create --name $ResourceGroup --location $Location

Write-Host "Deploying Infrastructure via Bicep..."
az deployment group create `
  --resource-group $ResourceGroup `
  --template-file main.bicep `
  --parameters `
    buddyPassword=$BUDDY_PASSWORD `
    flaskSecretKey=$FLASK_SECRET_KEY `
    refreshToken=$RefreshToken `
    clientId=$ClientId `
    tenant=$Tenant `
    redirectUri=$RedirectUri

if ($LASTEXITCODE -ne 0) { throw "Bicep deployment failed." }

# Get App Name from Bicep Output (Optional, but we know it from the script logic or can query it)
# For simplicity, we'll assume the Bicep uses the same naming logic or we can query the webapp in the RG
$WebAppResource = az webapp list --resource-group $ResourceGroup --query "[0].name" -o tsv
if (-not $WebAppResource) { throw "Could not find Web App in resource group." }
$AppName = $WebAppResource

# 3. Deploy Code
Write-Host "Deploying code to $AppName..."
# Wait for the app to be fully ready to accept deployments
Start-Sleep -Seconds 15
# Use legacy zip deploy which is sometimes more reliable for initial deployments
az webapp deployment source config-zip --resource-group $ResourceGroup --name $AppName --src $ZipFile --verbose
if ($LASTEXITCODE -ne 0) { throw "Failed to deploy code." }

Write-Host "Deployment Complete!"
Write-Host "App URL: https://$AppName.azurewebsites.net"
Write-Host "IMPORTANT: Update your Azure AD App Registration to allow redirect URI: https://$AppName.azurewebsites.net/getAToken (if applicable) or ensure the existing Redirect URI matches."
