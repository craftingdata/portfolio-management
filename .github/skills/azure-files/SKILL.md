---
name: azure-files
description: Controlled access to a slug's Azure Files-backed workspace for durable memory banks, inbox items, audits, and agent artifacts.
---

# When This Skill Applies

- Reading or writing files that live in the slug's durable Azure Files workspace
- Inspecting or updating curated memory banks, inbox notes, audit artifacts, or synced workspace skills
- Verifying that a slug can access only its own Azure Files-backed workspace boundary

Key points:

- Treat this as an Azure Shell storage capability, not a vertical plugin feature.
- Scope access to the slug's own `openclaw-state` share only.
- Scope file operations to `workspace/` only; do not expose raw access to `openclaw.json` or arbitrary storage-account paths.
- Prefer the workspace for durable agent artifacts, curated memory banks, inbox items, and audit notes.
- Do not expose storage-account management, share creation/deletion, SAS generation, or cross-slug file access through this skill.

Initial tool surface:

- List directories within `workspace/`
- Show file or directory metadata inside `workspace/`
- Read file content from `workspace/`
- Write text or base64-decoded content into approved `workspace/` paths
- Move a file between approved `workspace/` paths
- Delete a file, or delete a workspace directory when explicitly requested with recursion

Do not include in v1:

- Storage account discovery outside the current slug
- Share creation, deletion, or quota changes
- Cross-slug file access
- Generic Azure Storage admin operations
- Direct config mutation of `openclaw.json`

Implementation guidance:

- Resolve the storage account from the slug resource group and prefer Entra-authenticated Azure Files access first.
- Use the slug Key Vault secret `openclaw-state-storage-key` only as a fallback for brokered or operator flows that lack Azure Files data-plane RBAC.
- Keep all file operations relative to `workspace/` so the tool cannot mutate runtime config or other share-root content.
- For large or binary files, prefer `-AsBase64Only` or a tighter `-MaxContentBytes` limit.
- Child slugs may inherit this skill because the storage boundary is slug-local: each `claw-<slug>` deployment gets its own storage account and `openclaw-state` share.

Sample prompts:

- "List the files in the slug workspace inbox."
- "Read `banks/core.md` from the Azure Files workspace."
- "Write a new inbox note into `inbox/2026-03-21.md`."

## References

- `docs/myclaw.md`
- `docs/runbooks.md`
- `.github/instructions/repo-splitting.instructions.md`
- `.github/skills/azure-integration/SKILL.md`
