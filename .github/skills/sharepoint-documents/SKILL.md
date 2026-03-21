---
name: sharepoint-documents
description: Controlled SharePoint and Teams-channel document access using explicit site allowlists and least-privilege Graph permissions.
---

# When This Skill Applies

- Adding or reviewing document read/write access for SharePoint libraries or Teams channel-backed sites
- Designing a repo-native tool surface for approved document retrieval, upload, or search
- Checking whether a SharePoint-facing capability stays inside the `sam` hub-first security boundary

Key points:

- Treat this as an Azure Shell integration capability, not a vertical product pack.
- Scope access with Microsoft Graph application permissions plus `Sites.Selected`; do not use tenant-wide SharePoint access as a shortcut.
- Limit the tool surface to explicit site, library, and folder allowlists.
- Start on `sam` only. Promote to child slugs only after the site mapping and entitlement model are explicit.
- Do not expose raw Graph calls, permission grants, or SharePoint admin operations through this skill.

Initial tool surface:

- List sites already granted to the runtime.
- List libraries and folders within an approved site.
- Read file metadata and download file content.
- Upload new files to an approved folder.
- Update file content for supported document types.
- Search files by name, path, or basic metadata within approved sites.

Do not include in v1:

- Tenant-wide site discovery
- SharePoint admin or permission-management operations
- Cross-site writes outside the allowlist
- A generic "call Microsoft Graph" endpoint

Implementation guidance:

- Prefer managed identity where possible; otherwise use Entra app credentials from Key Vault.
- Host the mature tool surface on Azure Container Apps behind Entra-authenticated ingress or an equivalent secure MCP pattern.
- Emit structured telemetry and audit events for every write action with slug, tool, target resource, requested action, approval state, and outcome.
- When a user asks for file body questions such as line counts, exact text, or content inspection, prefer the SharePoint `content` read path over generic permission fallback messaging.
- Resolve the target by explicit site-relative path or item id; a bare filename alone is usually ambiguous in Teams/SharePoint and may need disambiguation.
- For large or binary files, prefer `-AsBase64Only` or a tighter `-MaxContentBytes` limit instead of trying to decode arbitrary content as text.

Sample prompts:

- "Design the first repo-native SharePoint document tools for `sam` with `Sites.Selected` only."
- "Review whether this SharePoint access request can stay within site-scoped allowlists."
- "Read `/Shared Documents/todo.txt` and tell me how many lines it has."

## References

- `docs/myclaw.md`
- `.github/instructions/repo-splitting.instructions.md`
- `.github/skills/azure-integration/SKILL.md`
- `.github/skills/security-compliance/SKILL.md`
