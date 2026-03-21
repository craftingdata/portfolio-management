---
name: shire-runbook
description: Preferred Shire operator workflows, wrapper commands, validation steps, and escalation paths for slug lifecycle work.
---

# When This Skill Applies

- Performing install, deploy, upgrade, verify, or remove operations for a slug
- Choosing between wrapper commands and lower-level scripts
- Recovering context on the supported operational path for this repo

Key points:

- Use `scripts/shire.ps1` as the supported operator interface when it covers the task.
- Prefer the repo’s wrapper and runbook flow over ad hoc Azure CLI mutation.
- Treat `deploy` as the default operator path for a healthy converge plus validation cycle.
- Treat Teams as optional/manual follow-up unless the slug explicitly needs it.
- Prefer Telegram as the first non-web channel when a slug needs channel access quickly.

Common operator surfaces:

- `./scripts/shire.ps1 list`
- `./scripts/shire.ps1 deploy -Slug <slug>`
- `./scripts/shire.ps1 verify -Slug <slug>`
- `./scripts/shire.ps1 upgrade -Slug <slug> -Commit <sha>`
- `./scripts/shire.ps1 remove -Slug <slug> -Confirm`
- `./scripts/shire.ps1 watch-status -Slug <slug>`

Runbook rules:

- Validate before destructive or privileged changes.
- Keep the stable ACA FQDN as the operator entrypoint; do not use revision-specific URLs as health signals.
- For brokered child-slug work, validate the brokered path separately from image-build noise when needed.
- Record durable operator guidance in docs or repo-native skills instead of relying on transient chat history.

Deploy budget for debugging:

- One deploy may be used to reproduce a deployment-time bug.
- A second deploy may be used only after:
  - the suspected failing helper or decision path has been isolated
  - a code or config change was made to that path
  - a focused local validation or regression test was run
- If a second deploy shows the same class of drift, switch to helper-level reproduction and stop further deploys until the root cause is explained.
- Each deploy during debugging should have one explicit purpose:
  - reproduce
  - verify mitigation
  - verify root fix

Sample prompts:

- "What is the supported deploy and verify flow for `sam`?"
- "Which wrapper command should I use instead of patching Azure resources directly?"

## References

- `docs/runbooks.md`
- `docs/myclaw.md`
- `scripts/shire.ps1`
- `.github/skills/operations/SKILL.md`
