---
description: Create a new .github/skills/<topic>/SKILL.md from an existing script, workflow, or domain area
tools: ["read", "search"]
---

You are turning a script, workflow, or domain area into a first-class Copilot skill for this repo.

Work through the steps below in order. Do not skip any step.

## Step 1 — Gather context

Answer these questions (ask the user if any are unclear):

1. **What is the skill name** (slug, lowercase-hyphenated, e.g., `alpaca-orders`)?
2. **What does it do** — one sentence, action-oriented?
3. **What does the user have today** — a script path, a workflow, informal notes, or nothing yet?
4. **Which existing skills overlap?** — search `.github/skills/*/SKILL.md` for related content before creating a new file.
5. **Repo-split boundary** — does this skill belong to the generic Azure Shell or a vertical plugin? (See `.github/instructions/repo-splitting.instructions.md`.)

## Step 2 — Duplicate check

Read every `.github/skills/*/SKILL.md`. If an existing skill already covers this domain:

- Prefer **augmenting** the existing SKILL.md over creating a new file.
- Only create a new SKILL.md when the topic is clearly distinct and not covered.

## Step 3 — Draft the SKILL.md

Produce a complete SKILL.md following this exact template (preserve the backtick fence and YAML front-matter):

````skill
---
name: <slug>
description: <one-sentence description>
---
# When This Skill Applies
- <trigger condition 1>
- <trigger condition 2>

Repo split note: <shell vs plugin; reference .github/instructions/repo-splitting.instructions.md>

## Core guidance
<key rules, guardrails, and patterns — bullets; reference existing docs under docs/ where possible>

## Guardrails (NEVER violate)
<safety rules specific to this skill — operator workflow, secrets handling, supported file paths, error handling as applicable>

## Sample prompts (use to trigger this skill)
- "<natural-language prompt that should activate this skill>"
- "<second example>"

## Quick recipes
```
# Annotated commands or code snippets for the most common task
```

## References
- `<path/to/relevant/doc.md>`
- `<path/to/relevant/module.py>`
````

## Step 4 — Validate

Before writing the file, confirm:

- [ ] `name` slug matches the directory name that will be used (`.github/skills/<name>/SKILL.md`).
- [ ] No secret, credential, or hardcoded env-var value appears in the skill text.
- [ ] All referenced file paths exist in the repo (use `search` tool to verify).
- [ ] Guardrails section is present and covers the most dangerous failure modes for this domain.
- [ ] Repo-split boundary is explicit.

## Step 5 — Write the file

Write the complete SKILL.md to `.github/skills/<name>/SKILL.md`.

Then output a one-line summary: "Created `.github/skills/<name>/SKILL.md` — <what it covers> — Repo split: <shell|plugin|mixed>."

---

<!-- Describe the script, workflow, or domain area to formalise as a skill below this line -->
