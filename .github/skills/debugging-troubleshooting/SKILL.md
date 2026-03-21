---
name: debugging-troubleshooting
description: Diagnostics, logging, profiling, and troubleshooting common platform issues (multi-tenant bugs, Decimal precision, async issues).
---

# When This Skill Applies

- Investigating runtime errors, performance regressions, or production incidents
- Diagnosing tenant isolation bugs, authentication failures, or precision/decimal issues
- Performing container app or Azure deployment troubleshooting

Key guidance:

- Start with the failing wrapper command or validation step, not general speculation.
- For deployment issues, inspect `scripts/shire.ps1`, `scripts/validate-install.ps1`, and the latest workflow or terminal output before changing code.
- For Container Apps issues, check Key Vault secret refs, the current revision, and recent logs with `az containerapp logs show`.
- For config issues, remember this repo deep-merges `openclaw.json` overlays during provisioning; stale or preserved config can survive redeploys.

Advanced techniques: compare deployment outputs, validate Bicep inputs, and inspect Azure Files-backed config state when runtime behavior does not match the current repo files.

Sample prompts (use to trigger this skill):

- "Container app fails with managed identity Key Vault access denied — how to debug and fix?"
- "Database connection intermittent errors — what diagnostics should I run locally and in container apps?"

Quick commands:

```
# Show container app logs
az containerapp logs show --name <app-name> --resource-group <rg-name> --tail 100

# Run the repo validation path
./scripts/shire.ps1 verify -Slug <slug>
```

Failure triage checklist:

- Reproduce with the same slug inputs and wrapper command when possible.
- Collect logs, include revision and request context when possible.
- Check Key Vault permissions, current secret refs, and the active revision before broader changes.

Debugging escalation ladder:

1. Reproduce the failure once using the supported wrapper command.
2. Capture the exact failing artifact:
   - client ID
   - secret reference
   - revision
   - app registration ID
   - Key Vault secret version
3. If the first reproduction shows duplicate resource creation, configuration drift, or repeated lookup failures, stop live retries.
4. Reproduce the exact helper logic directly:
   - same CLI arguments
   - same Graph filter
   - same management API path
5. Add a focused regression test before the next deploy when the bug is in script logic.
6. Only redeploy after the helper-level behavior is explained.

Anti-churn rules:

- Do not repeat the same hypothesis after it has already failed in a live deploy.
- Do not perform cleanup of Azure artifacts until the repo-level failure mode is explained or the cleanup is explicitly mitigation-only.
- If a command returns usable JSON plus a nonzero exit code, inspect the response body before treating it as failure.
- If a second deploy shows the same class of drift, stop and switch to helper-level reproduction.

## References

- `docs/runbooks.md`
- `scripts/shire.ps1`
- `scripts/validate-install.ps1`
