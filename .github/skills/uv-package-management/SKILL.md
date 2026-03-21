---
name: uv-package-management
description: Use when initializing or migrating Python package management to uv, including conversion from requirements.txt to pyproject.toml and uv.lock.
---

# When This Skill Applies

- Initializing a new Python project with uv
- Migrating an existing repo from `requirements.txt` to `pyproject.toml` and `uv.lock`
- Adding, syncing, locking, or removing dependencies with uv
- Creating or refreshing a local `.venv` in the project directory

## Core guidance

- Prefer `uv` as the package manager for this repo.
- Keep the virtual environment inside the repository as `.venv`.
- Use `pyproject.toml` as the source of truth for dependencies and `uv.lock` for the resolved lock state.
- Do not add PyPI publishing steps unless the user explicitly asks for packaging or release automation.

## Migration flow from `requirements.txt`

1. If the repo already has a `requirements.txt`, add its contents to the uv project:
   ```bash
   uv add --requirements requirements.txt
   ```
2. Verify the generated `pyproject.toml` and `uv.lock` are present and correct.
3. Sync the local environment from the project metadata:
   ```bash
   uv sync
   ```
4. Archive or remove the old `requirements.txt` once the uv files are committed.

If you need a clean start instead of migration:

```bash
uv init --bare .
uv add fastapi uvicorn
uv sync
```

## Guardrails (NEVER violate)

- Do not leave the repo depending on both `requirements.txt` and `pyproject.toml` as competing sources of truth.
- Do not create the virtual environment outside the repository unless the user explicitly requests that.
- Do not assume publishing to PyPI is part of package management.
- Do not rewrite application code just to fit the package manager.

## Sample prompts (use to trigger this skill)

- "Initialize uv for this repo and migrate dependencies from requirements.txt"
- "Convert this project to uv package management and keep the venv local"
- "Add a dependency with uv and update the lockfile"

## Quick recipes

```bash
# Initialize a bare uv project in the current directory
uv init --bare .

# Create a local virtual environment in the repo root
uv venv .venv

# Migrate an existing requirements.txt file into uv metadata
uv add --requirements requirements.txt

# Sync the repo environment from pyproject.toml + uv.lock
uv sync

# Run tests through uv without activating the venv manually
uv run pytest tests -q
```

## References

- `pyproject.toml`
- `uv.lock`
- `README.md`
- `.github/workflows/run-tests.yml`
