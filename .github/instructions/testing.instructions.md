---
description: Assist-mode validation loop (format/lint/test) for all code changes
applyTo: "**/*.py,**/test_*,**/conftest*"
---

# Closing the Loop (Assist Mode)

## Default Validation Loop

- Prefer running a fast local loop before considering work complete:
  - `uv sync`
  - `uv run pytest <focused target>`

## Tests

- When changing behavior, add or update tests.
- If you intentionally skip tests (e.g., docs-only change, pure refactor with no behavior changes), explicitly state why and propose the follow-up validation to run.

## Script Validation

- When changing PowerShell deployment or provisioning scripts:
  - run a PowerShell parse check on the edited script
  - add or update a focused regression test for the changed decision path
  - if the bug depends on Azure CLI or Graph behavior, prefer a narrow test that asserts the helper control flow and mention the direct CLI reproduction used to validate the diagnosis

## Scope Discipline

- Keep changes surgical and localized to the request.
- Avoid broad refactors unless explicitly requested.
