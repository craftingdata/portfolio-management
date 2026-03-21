---
name: onenote-notes
description: Structured notebook, section, and page operations for controlled note capture and retrieval.
---

# When This Skill Applies

- Adding or reviewing OneNote-backed note capture or retrieval
- Designing operator or product note workflows that need a small, reviewable Graph surface
- Deciding whether notebook access belongs on `sam` only or in a user-facing slug

Key points:

- Keep the scope to specific notebooks, sections, and pages; do not expose broad tenant note discovery.
- Start on `sam` as an operator knowledge-capture surface.
- If notebooks become part of the product experience for child slugs, prefer a hub-mediated auth model instead of granting every child slug broad Graph Notes application permissions directly.
- Prefer managed identity or certificate-backed auth over long-lived static secrets.
- Do not expose free-form raw Graph write operations.

Recommended auth model:

- Treat the slug-scoped notebook stored in the slug SharePoint site as a required store, but do not assume that means the child slug should talk to Graph Notes directly.
- Preferred direct-access boundary: a hub-owned OneNote adapter with the minimum Graph Notes permissions needed, enforcing slug-to-notebook mapping server-side.
- Avoid giving each child slug app its own tenant-wide `Notes.ReadWrite.All` application permission unless you intentionally accept that blast radius.
- If a child slug needs direct notebook writes later, require an explicit design review for the notebook mapping, audit trail, and approval semantics.

Initial tool surface:

- List notebooks and sections within approved scope.
- Read notebook pages.
- Create new pages in approved sections.
- Append structured notes to an existing page.
- Search pages by title or simple content match.

Do not include in v1:

- Broad tenant notebook discovery
- Notebook permission changes
- Destructive delete flows
- A generic OneNote or raw Graph write endpoint

Implementation guidance:

- Use a narrow remote tool surface hosted on Azure Container Apps, or Azure Functions if the workload is sporadic.
- Keep auth material in Key Vault and prefer non-secret auth where practical.
- Emit structured telemetry and audit events for every create or append operation.

Sample prompts:

- "Create a repo-native OneNote note-capture surface for `sam` only."
- "Review whether this notebook workflow is narrow enough for v1."

## References

- `docs/myclaw.md`
- `.github/instructions/repo-splitting.instructions.md`
- `.github/skills/azure-integration/SKILL.md`
- `.github/skills/security-compliance/SKILL.md`
