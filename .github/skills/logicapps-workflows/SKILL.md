---
name: logicapps-workflows
description: Approved Logic Apps invocation patterns for a narrow, validated automation bus with slug-scoped authorization.
---

# When This Skill Applies

- Adding or reviewing Logic Apps-backed automation for approved downstream actions
- Designing a safe workflow invocation layer instead of exposing raw workflow URLs
- Checking whether a child slug can invoke only the workflows explicitly assigned to it

Key points:

- Treat Logic Apps as an automation bus behind an allowlist, not as an open workflow platform.
- Restrict calls to a small allowlist of workflow endpoints and documented payload contracts.
- Validate payload schemas before dispatch.
- Require server-side slug authorization so child slugs can invoke only workflows explicitly assigned to them.
- Start hub-first. Child slugs should call approved entrypoints, not raw Logic Apps endpoints.

Initial tool surface:

- List approved workflow names and short descriptions.
- Invoke a workflow with a validated payload.
- Poll or fetch workflow run status.
- Return a normalized success/failure response.

Do not include in v1:

- Arbitrary Logic App discovery across the subscription
- Editing workflow definitions
- Direct secret-bearing payload passthrough without validation
- Any workflow whose blast radius is not documented

Implementation guidance:

- Use signed or authenticated calls, preferably through Entra, APIM, or another approved gateway.
- Run the skill in `sam` or another hub-controlled service.
- Require child-slug requests to carry a slug identity that the workflow gateway validates before dispatch.
- Emit structured telemetry and audit events for every workflow invocation.

Sample prompts:

- "Design a hub-owned Logic Apps invocation surface with slug-scoped authorization."
- "Review this workflow contract for blast radius and payload validation gaps."

## References

- `docs/myclaw.md`
- `.github/instructions/repo-splitting.instructions.md`
- `.github/skills/azure-integration/SKILL.md`
- `.github/skills/operations/SKILL.md`
- `.github/skills/security-compliance/SKILL.md`
