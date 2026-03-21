# Known Azure Resources (non-secret)

This file is the repo-wide, non-secret Azure inventory template for `shire`.

Use it for stable resource names or IDs that are safe to commit. Do not put secrets here.

If you need developer-specific values such as tenant or subscription IDs, use the local override file instead:

- `/.github/azure_resources.local.md`

Current repo model:

- primary deployment unit: one resource group per slug, usually `claw-<slug>`
- primary operator entrypoint: `scripts/shire.ps1`
- Bicep entrypoints:
  - `infra/bicep/sub/main.bicep`
  - `infra/bicep/main.bicep`

Shared non-secret identifiers to keep here if needed:

- subscriptionId:
- tenantId:
- defaultLocation: eastus2

Per-slug template:

- slug:
- resourceGroup: claw-<slug>
- containerAppName:
- keyVaultName:
- storageAccountName:
- managedEnvironmentName:
- acrName:
- appInsightsName:

Notes:

- Prefer slug-oriented naming, not a shared `investing` resource group model.
- Keep secrets, tokens, and connection strings in Key Vault only.
- If a value changes per slug or per developer, do not hardcode it here unless it is intentionally shared repo context.
