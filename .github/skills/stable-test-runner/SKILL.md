---
name: stable-test-runner
description: Stable test-running guidance for this repo using uv and focused pytest targets.
---

# When This Skill Applies

- Running or re-running tests after changing Python application code or tests
- Choosing the smallest reliable pytest target for a change
- Checking whether local dependencies are installed before running tests

## Core guidance

- Prefer focused test runs over whole-suite runs.
- Install dependencies with `uv sync` and run pytest through uv or the project interpreter: `uv run pytest` or `python -m pytest`.
- There is no standard `dev` pytest marker in this repo. Use a file path or `-k` expression instead.

## Recommended workflow

1. Run `uv sync` if the environment is not prepared.
2. Verify `pytest` is importable before running tests.
3. Run the narrowest useful command first.
4. Expand scope only if the first run passes and the change warrants broader coverage.

## Quick recipes

```bash
# Single file
uv run pytest tests/test_api.py -q

# Focused keyword expression
uv run pytest tests/test_optimization.py -k "sharpe" -q

# Full repo tests only when justified
uv run pytest tests -q
```

## Guardrails

- Do not assume `pytest-xdist` is installed.
- Do not assume `dev`, `azure`, or other custom markers unless they are defined in the repo config.
- Do not assume `requirements.txt` is the source of truth once the repo has migrated to uv.

## References

- `pyproject.toml`
- `uv.lock`
- `tests/`
