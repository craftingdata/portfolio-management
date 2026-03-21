---
description: Generate an implementation plan from a design doc or requirement
tools: ["read", "search"]
---

Read the attached design or requirement. Produce a step-by-step implementation plan:

- One task per line, in dependency order
- For each task: what changes, which files, how to verify
- Flag any guardrail conflicts from `.github/copilot-instructions.md` and the matching `.github/instructions/*.instructions.md` files
- Do NOT write any code — plan only

Save the plan to a markdown file in the project root named after the feature (e.g., `feature-plan.md`) before ending.
