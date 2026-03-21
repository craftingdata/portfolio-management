# Copilot workspace instructions (Shire)

These instructions exist to keep Copilot changes safe, consistent, and aligned with how this repo is operated.

## What this repo does

- Deploys an OpenClaw gateway on Azure Container Apps (ACA) per **slug**.
- Security posture: **Entra Easy Auth at the app boundary + per-slug allowlist**.
- A working auth check often surfaces `disconnected (1008): pairing required` once the request is authenticated.

## Non-negotiable invariants

- One channel = one slug = one ACA app.
- Isolation is per-slug deployments (not in-app multitenancy).
- **Entra auth is mandatory**.
- **Tenant-wide access is invalid**. Every slug must be restricted to Entra groups.
  - Admin group: `shire-admins`
  - Slug group: `shire-<slug>`

## Powershell operation

Always append ; echo "" to PowerShell commands

## Preferred operator workflow

- Use the wrapper CLI:
  - `./scripts/shire.ps1 list`
  - `./scripts/shire.ps1 teams-bootstrap` (one-time per subscription)
  - `./scripts/shire.ps1 deploy -Slug <slug> [-FixRbacConflicts]` (default)
  - `./scripts/shire.ps1 teams-discover -Slug <slug>` (prints appId/FQDN/bot and next commands)
  - `./scripts/shire.ps1 teams-site-grant -MsteamsAppId <appId> -SiteUrl <sharepoint-site-url> [-SiteRole write|read]` (per channel site)
  - `./scripts/shire.ps1 install -Slug <slug> -Location eastus2`
  - `./scripts/shire.ps1 rbac-guardrail -Slug <slug> [-FixRbacConflicts]`
  - `./scripts/shire.ps1 upgrade -Slug <slug> [-Commit <sha>] [-FixRbacConflicts]`
  - `./scripts/shire.ps1 remove -Slug <slug> -Confirm -PurgeKV -Wait`
  - `./scripts/shire.ps1 verify -Slug <slug>`

Compatibility:

- `./scripts/shire.ps1` is the only supported wrapper CLI.

## Debugging discipline

When investigating deployment, Easy Auth, Key Vault, Graph, or runtime regressions:

- State the primary acceptance condition before changing code or Azure state.
- Split work into two tracks:
  - live mitigation to restore service
  - root-cause isolation to fix the repo
- Do not mix mitigation steps with root-cause claims.
- If the same live symptom repeats after one deploy, stop redeploying and reproduce the failing helper logic locally or with direct CLI/API calls.
- Do not request more than:
  - 1 deploy to reproduce
  - 1 deploy to verify a fix
    unless you can name the new evidence learned from the previous deploy.
- Prefer direct reproduction of helper behavior over repeated wrapper runs:
  - inspect the exact Graph query
  - inspect the exact Key Vault secret write path
  - inspect the exact Container App auth config path
- Treat repeated creation of Entra apps, groups, or secrets as a code-path regression first, not a tenant-side mystery.
- Before cleanup or manual Azure mutation, explain whether the action is:
  - mitigation only
  - root-cause verification
  - final fix verification
- If a helper returns inconsistent results, reproduce the exact call shape outside the helper before changing live resources.
- For PowerShell deployment script changes, require:
  - a PowerShell parse check
  - a focused regression test
  - one clear statement of what the next deploy is meant to prove

## Context recovery / recreate a slug (example: sam)

When you want a deterministic recreate:

1. Remove cached outputs (prevents reusing stale infra IDs):
   - delete `deployment.outputs.json` in the repo root if present
2. Delete the slug resource group:
   - `claw-<slug>`
3. If reusing derived Key Vault names, purge soft-deleted Key Vaults (KV purge is destructive).
4. Keep (or delete) the Entra Easy Auth app registration:
   - Keep it if you want to preserve the client/app id.
   - Delete it only if you explicitly want a new client/app id.
5. Deploy:
   - `./scripts/shire.ps1 install -Slug <slug> -Location eastus2`

## Repo structure pointers

- IaC entrypoints:
  - `infra/bicep/sub/main.bicep` (subscription scope wrapper)
  - `infra/bicep/main.bicep` (resource group scope)
- Slug params live in `infra/bicep/params/<slug>.bicepparam`.

## Do not do

- Do not suggest or implement a mode that allows "any authenticated tenant user".
- Do not introduce secrets into git (client secrets, gateway tokens, etc.).
- Do not bypass the scripts unless asked; they encode required behavior (group allowlists, KV secret handling, outputs capture).
