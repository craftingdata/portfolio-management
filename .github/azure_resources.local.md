# Local Azure Resources (developer-specific, non-secret)

This file is **git-ignored** (see `.gitignore`).

Use it to store _non-secret_ Azure identifiers you want the coding assistant to remember locally.
Do **not** put secrets here (no client secrets, connection strings, keys, SAS tokens).

If you’re unsure whether something is a secret: treat it as a secret and put it in Key Vault.

## Primary context

- tenantId:
- subscriptionId:
- defaultLocation: eastus2

## Current slug you are operating on

- slug:
- resourceGroup: claw-<slug>

## Core resources for that slug

- keyVaultName:
- appInsightsName:
- logAnalyticsWorkspaceName:
- containerAppName:
- containerAppEnvironmentName:
- acrName:
- storageAccountName:

## Optional / as-needed

- appConfigName:
- foundryAccountName:
- teamsAppId:
