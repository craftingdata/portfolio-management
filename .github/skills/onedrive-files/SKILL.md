---
name: onedrive-files
description: Controlled OneDrive and shared-library file access with explicit drive and folder allowlists and hub-mediated fallback paths.
---

# When This Skill Applies

- Adding or reviewing OneDrive-backed file access for working documents, uploads, or exports
- Designing a narrow file surface that avoids broad personal-drive enumeration
- Deciding whether a child slug should access files directly or through `sam`

Key points:

- Treat this as a narrow document-store capability, not a generic Graph connector.
- Require an explicit allowlist of approved drive ids and approved folder roots.
- Do not grant tenant-wide file permissions to child slugs just to make the skill easy to implement.
- If the intended scope cannot be enforced cleanly with app-only Graph permissions, fall back to `sam`-mediated access or delegated user-authorized access.
- Start on `sam` with explicitly approved folders. Promote to child slugs only when there is a concrete product need.

Initial tool surface:

- List approved folders.
- Read file metadata and content.
- Upload files to approved folders.
- Replace file content in approved folders.
- Search files by name and folder path.

Do not include in v1:

- Broad personal-drive enumeration
- Sharing-link creation
- Permission management
- Move/copy across arbitrary drives
- A catch-all Graph file tool

Implementation guidance:

- Keep secrets in Key Vault and prefer managed identity, certificate-backed auth, or other non-static auth material.
- If exposed to child slugs, enforce slug-scoped authorization checks against the approved drive/folder allowlist before every read or write.
- Reuse the `sharepoint-documents` hosting pattern if the implementation is shared; otherwise use the same secure Azure Container Apps or MCP pattern.
- Emit structured telemetry and audit events for every write action.

Sample prompts:

- "Design the `onedrive-files` skill so child slugs never need tenant-wide file permissions."
- "Review whether this OneDrive use case should stay hub-mediated through `sam`."

## References

- `docs/myclaw.md`
- `.github/instructions/repo-splitting.instructions.md`
- `.github/skills/azure-integration/SKILL.md`
- `.github/skills/security-compliance/SKILL.md`
