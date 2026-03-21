---
description: Implement a feature from a saved plan file
tools: ["editFiles", "search", "read"]
---

Implement the feature described in the attached plan file.

- Follow the repo guardrails in `.github/copilot-instructions.md` and the matching `.github/instructions/*.instructions.md` files
- Write or update tests for any changed behaviour
- Default verification: run the narrowest relevant `python -m pytest ...` target for the files you changed
- Surgical changes only — do not refactor adjacent code unless the plan explicitly requires it
- After completing each checklist item, confirm it and move to the next
- If a guardrail blocks progress, propose a safe alternative — do not bypass it
