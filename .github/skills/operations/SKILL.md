---
name: operations
description: Deployment and CI/CD patterns for the platform (Container Apps, pipelines, release validation).
---

# When This Skill Applies

- Deploying to Azure Container Apps or updating CI/CD pipelines
- Creating release validation and rollback procedures
- Managing pipeline secrets and runtime configuration

Key points:

- Use the repo's GitHub Actions workflows and `scripts/shire.ps1` wrapper; do not invent a parallel deployment path without a reason.
- Include pre-deploy validation steps: Bicep compile or validate, wrapper-level verify checks, and smoke tests where supported.
- Keep secrets in Key Vault and reference them via managed identity; avoid embedding secrets in workflow YAML or environment variables.
- Repo split note: CI/CD, Container Apps, Key Vault/App Config, App Insights, and shared chat runtime (DevUI/Teams, Microsoft Agent Framework) are Azure Shell concerns; avoid baking plugin-specific assumptions into pipeline templates.

Sample prompts (use to trigger this skill):

- "Add a pre-deploy smoke test step to GitHub Actions that validates Bicep and runs the repo verify flow."
- "What should our rollback procedure be if a container app revision fails health checks?"

CI checklist:

- Validate the relevant Bicep files and params before deployment.
- Prefer `./scripts/shire.ps1 deploy|install|upgrade|verify` over direct imperative mutations.
- Use Key Vault references and managed identity for runtime secrets; avoid storing secrets in repo or env vars.

Quick commands:

```
# Validate the wrapper entrypoint is available
./scripts/shire.ps1 list
```

## References

- `.github/workflows/prod-deploy.yml`
- `.github/workflows/dispatch-smoke.yml`
- `docs/runbooks.md`
- `scripts/shire.ps1`
