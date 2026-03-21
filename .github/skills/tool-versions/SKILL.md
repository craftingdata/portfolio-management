---
name: tool-versions
description: Canonical inventory of software package versions so the assistant retrieves the correct upstream documentation for the versions in use.
---

# Tool Versions

When writing code or fetching docs, resolve the exact version in use:

1. **Python packages**: check `pyproject.toml` (constraints) and `uv.lock` (pinned resolved version)
2. **Containers / CLI / system packages**: check `.github/tool-versions.yml`

Map `name` + `version` to vendor docs. Prefer exact-version doc pages (e.g., `fastapi 0.115 docs`).

When bumping a dependency, update `.github/tool-versions.yml` (containers/CLI) and include a short `notes` entry explaining why.
