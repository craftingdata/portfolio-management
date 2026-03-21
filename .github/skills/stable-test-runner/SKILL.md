---
name: stable-test-runner
description: Stable test-running guidance for this repo using requirements.txt and focused pytest targets.
---

# When This Skill Applies

- Running or re-running tests after changing Python application code or tests
- Choosing the smallest reliable pytest target for a change
- Checking whether local dependencies are installed before running tests

## Core guidance

- Prefer focused test runs over whole-suite runs.
- Install dependencies from `requirements.txt` and run pytest in module mode: `python -m pytest`.
- There is no standard `dev` pytest marker in this repo. Use a file path or `-k` expression instead.

## Recommended workflow

1. Install dependencies from `requirements.txt` if the environment is not prepared.
2. Verify `pytest` is importable before running tests.
3. Run the narrowest useful command first.
4. Expand scope only if the first run passes and the change warrants broader coverage.

## Quick recipes

```bash
# Single file
python -m pytest tests/test_api.py -q

# Focused keyword expression
python -m pytest tests/test_optimization.py -k "sharpe" -q

# Full repo tests only when justified
python -m pytest tests -q
```

## Guardrails

- Do not assume `pytest-xdist` is installed.
- Do not assume `dev`, `azure`, or other custom markers unless they are defined in the repo config.
- Do not assume `uv`, `pyproject.toml`, or `uv.lock` exist.

## References

- `requirements.txt`
- `tests/`
