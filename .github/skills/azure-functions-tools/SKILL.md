---
name: azure-functions-tools
description: Narrow Azure Functions adapter patterns for validated helper operations without turning Functions into a generic execution surface.
---

# When This Skill Applies

- Adding or reviewing small Azure Functions-backed adapters for transforms, validation, approvals, or webhook handling
- Designing a controlled function-invocation surface instead of a general-purpose execution endpoint
- Deciding whether a function-backed tool is stable and low-blast-radius enough for child-slug exposure

Key points:

- Treat each function as a separate contract, not as one broad privileged tool.
- Require authenticated calls with Entra, APIM in front of function auth, or another controlled boundary.
- Keep secrets in Key Vault.
- Require slug-scoped authorization for every function callable by child slugs.
- Start with hub-controlled functions only.

Initial tool surface:

- Invoke named approved function endpoints.
- Validate input payloads per function contract.
- Return normalized outputs and error envelopes.
- Support idempotent helper operations such as transforms, enrichment, or validation.

Do not include in v1:

- General-purpose code execution
- Arbitrary function discovery
- Deployment or configuration mutation of the Functions app
- A shared "run anything" endpoint

Implementation guidance:

- Use Azure Functions for the adapters themselves.
- If several adapters become long-lived or stateful, move the mature surface behind Azure Container Apps instead.
- Promote individual function-backed tools to child slugs only after proving they are stable, idempotent, and low-blast-radius.
- Emit structured telemetry and audit events for every invocation and write-like side effect.

Sample prompts:

- "Define a narrow Azure Functions adapter contract for `sam` with idempotent helper operations only."
- "Review whether this function should remain hub-only or is safe for child-slug exposure."

## References

- `docs/myclaw.md`
- `.github/instructions/repo-splitting.instructions.md`
- `.github/skills/azure-integration/SKILL.md`
- `.github/skills/operations/SKILL.md`
- `.github/skills/security-compliance/SKILL.md`
