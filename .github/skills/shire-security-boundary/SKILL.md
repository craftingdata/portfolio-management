---
name: shire-security-boundary
description: Shire trust-boundary rules for slug isolation, Entra allowlists, Key Vault handling, and actions that must never be delegated.
---

# When This Skill Applies

- Deciding whether a new tool, skill, or workflow is safe to expose on `sam` or a child slug
- Reviewing changes that touch Entra auth, group allowlists, Key Vault, Azure Files, or cross-slug access
- Explaining the non-negotiable Shire security model to an operator or future runtime agent

Key points:

- One channel equals one slug equals one ACA app. Isolation is per-slug deployment, not in-app multitenancy.
- Entra auth is mandatory. Tenant-wide access is invalid; access must be restricted to the reviewed group allowlists.
- Keep secrets in Key Vault and prefer managed identity for runtime access.
- Treat child slugs as reduced-authority runtimes. `sam` is the higher-trust control-plane slug.
- Do not expose tenant-wide Graph discovery, raw Azure control-plane writes, or payment-writing actions on the default agent.
- External skills are untrusted until reviewed.

Use this skill to answer:

- What must stay on `sam` versus what can be inherited by every child slug?
- Which operations require explicit human approval or tighter audit?
- Which access pattern preserves slug isolation instead of weakening it?

Never approve by default:

- Broad Graph permissions to make a file or note workflow easier
- Cross-slug secret sharing that weakens the per-slug boundary
- Generic web plus payment mutation plus elevated tool access on the same default agent
- Child-slug access to tenant-wide audit history or admin surfaces

Sample prompts:

- "Review whether this new Microsoft Graph tool stays inside the Shire trust boundary."
- "What parts of this workflow must remain on `sam` rather than a child slug?"

## References

- `docs/myclaw.md`
- `.github/copilot-instructions.md`
- `.github/instructions/repo-splitting.instructions.md`
- `.github/skills/security-compliance/SKILL.md`
