---
name: stable-test-runner
description: Stable test-running guidance for this repo using the in-repo .venv, uv-managed dependencies, and focused pytest targets.
---

# When This Skill Applies

- Running or re-running tests after changing scripts, docs, or Bicep validation logic
- Choosing the smallest reliable pytest target for a change
- Checking whether the local environment is ready before running tests

## Core guidance

- Prefer focused test runs over whole-suite runs.
- Use the repository `.venv` and run pytest in module mode: `python -m pytest`.
- This repo uses `uv` metadata and keeps a committed `uv.lock`; do not replace that with Poetry-specific instructions.
- There is no standard `dev` pytest marker in this repo. Use a file path or `-k` expression instead.

## Recommended workflow

1. Activate the in-repo virtual environment if it exists.
2. Verify `pytest` is importable before running tests.
3. Run the narrowest useful command first.
4. Expand scope only if the first run passes and the change warrants broader coverage.

## Quick recipes

```bash
# Single file
python -m pytest tests/test_scripts_and_workflow.py -q

# Focused keyword expression
python -m pytest tests/test_scripts_and_workflow.py -k "remove_install" -q

# Full repo tests only when justified
python -m pytest -q
```

## Guardrails

- Do not assume `pytest-xdist` is installed.
- Do not assume `dev`, `azure`, or other custom markers unless they are defined in the repo config.
- Do not tell agents to install ad hoc tool versions. If environment refresh is needed, use the repo's committed manifests.

## References

- `pyproject.toml`
- `uv.lock`
- `tests/`
