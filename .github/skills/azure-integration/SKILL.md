---
name: azure-integration
description: Azure integration patterns (Container Apps, SQL, App Configuration, Key Vault, DefaultAzureCredential).
---

# When This Skill Applies

- Integrating with Azure services (SQL, Key Vault, App Configuration, AI Foundry)
- Diagnosing authentication, network, or container app issues
- Setting up local dev environment or CI validation for Azure

Key guidance:

- Repo split note: Azure auth/config/telemetry and Microsoft Agent Framework + chat-channel underpinnings (DevUI/Teams) are Azure Shell responsibilities. Avoid introducing vertical/business rules into this layer; keep those in plugins. See `.github/instructions/repo-splitting.instructions.md`.

- Local authentication: use `az login` and verify the correct subscription before running deploy or validation commands.
- Preferred operator path: use `scripts/shire.ps1` rather than ad hoc Azure CLI mutations whenever the wrapper supports the action.
- Bicep entrypoints for this repo are `infra/bicep/sub/main.bicep` and `infra/bicep/main.bicep`.
- Container Apps and Key Vault are slug-scoped in normal operation. Think in terms of `claw-<slug>` resource groups, not a shared app resource group.
- For install and validation, prefer the repo workflows documented in `docs/runbooks.md` and encoded in `scripts/shire.ps1`.

Common remediation steps: re-authenticate (`az logout && az login`), verify subscription (`az account set --subscription`), confirm the intended slug params file, and check Key Vault permissions.

Sample prompts (use to trigger this skill):

- "How do I configure `DefaultAzureCredential` for local dev and Container Apps?"
- "Troubleshoot Key Vault access denied errors for the container app managed identity."

Quick validation commands:

```
# Azure login + verify
az login
az account show

# Show wrapper help surface
./scripts/shire.ps1 list

# View container app logs
az containerapp logs show --name <app-name> --resource-group <rg-name> --tail 50
```

Common fixes:

- Re-run `az login` and set the correct subscription.
- Ensure managed identity has Key Vault access policy or RBAC role assignments.
- Confirm you are working against the intended slug resource group and params file.

Known resources (non-secret):

- Prefer `/.github/azure_resources.local.md` (git-ignored) for developer-specific identifiers like `tenantId`/`subscriptionId`.
- Use `/.github/azure_resources.md` for repo-wide, non-secret resource names the assistant can reference (resourceGroup, containerAppName, keyVaultName, appConfigName, postgresServer, etc.).

## References

- `docs/runbooks.md`
- `scripts/shire.ps1`
- `infra/bicep/sub/main.bicep`
- `/.github/azure_resources.local.md`
- `/.github/azure_resources.md`
