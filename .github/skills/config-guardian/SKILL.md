---
name: config-guardian
description: OpenClaw config validation, guardrail review, and rollback-oriented guidance for hub-side runtime configuration changes.
---

# When This Skill Applies

- Reviewing or changing `openclaw.json` overlays, channel config, model wiring, or runtime guardrails
- Deciding whether a config change is safe to roll out to `sam`
- Checking whether a proposed config mutation should be blocked, validated, or staged first

Key points:

- This is a hub/control-plane skill. Keep it on `sam`; do not inherit it to child slugs by default.
- Treat `openclaw.json` as a controlled surface, not an arbitrary free-form config file.
- Prefer additive overlays and explicit validation over direct destructive rewrites.
- Backups, validation, and rollback plans should exist before widening runtime capability.
- Keep secrets out of config files; use Key Vault-backed env wiring instead.

Use this skill to review:

- channel config changes
- model/provider wiring changes
- trusted-proxy and Easy Auth related settings
- skills or memory-search config changes that alter the runtime trust boundary

Do not include in scope:

- arbitrary Azure resource mutation
- plugin installation without separate review
- raw secret handling in checked-in files

Sample prompts:

- "Review this `openclaw.json` overlay for unsafe config drift before rollout."
- "What validation and rollback checks should run before enabling this new runtime capability on `sam`?"

## References

- `docs/myclaw.md`
- `scripts/provision-install.ps1`
- `scripts/patch-openclaw-config.ps1`
- `.github/skills/azure-integration/SKILL.md`
- `.github/skills/operations/SKILL.md`
