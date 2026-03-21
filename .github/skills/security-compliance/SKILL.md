---
name: security-compliance
description: Audit, compliance, and security guidance (audit readiness, secrets handling, tenant isolation checks).
---

# When This Skill Applies

- Preparing for internal audits or compliance reviews
- Handling secrets and access control
- Verifying tenant isolation and audit trails

Key points:

- Keep secrets in Key Vault and use managed identities for runtime access.
- Log audit-relevant events for config changes, deploys, and access decisions; ensure logs include slug or request identifiers where possible.
- Follow the repo's documented security posture: Entra Easy Auth at the boundary, per-slug allowlists, and no tenant-wide access shortcuts.

Sample prompts (use to trigger this skill):

- "What security checks should run before enabling a new channel or external skill?"
- "How do we verify a slug stays restricted to the correct Entra groups?"

Audit checklist (short):

- Confirm secrets remain in Key Vault, not in config files or repo.
- Confirm the slug is still gated by the intended Entra groups.
- Confirm operator workflows still use the supported wrapper scripts rather than bypassing them.

Quick remediation:

- Rotate Key Vault secrets via process and validate managed identity access in staging before production.

## References

- `docs/security-architecture-soc2.md`
- `docs/runbooks.md`
