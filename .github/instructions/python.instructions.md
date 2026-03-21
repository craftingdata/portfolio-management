---
applyTo: "**/*.py"
---

# Python Development Standards

## Type Safety

- Use type hints on new or changed public function signatures.
- Prefer concrete types over `Any` unless a library boundary makes that impractical.

## Numerical Work

- Keep numerical code consistent with the existing implementation style.
- This repo currently uses `float`, NumPy arrays, pandas objects, and SciPy/SCIP inputs for optimization math. Do not force `Decimal` into solver-facing code unless the task is explicitly about numeric precision redesign.
- Be careful with shape assumptions, ticker ordering, and conversions between arrays, Series, and dict responses.

## FastAPI Patterns

- Keep request and response validation in Pydantic schemas where practical.
- Raise `HTTPException` for API-layer failures and keep service-layer logic separate from route handlers.

## Tests and Mocking

- Prefer deterministic tests that patch market-data fetching instead of calling external services.
- When changing behavior, add or update focused tests under `tests/`.

## Tooling

- This repo uses `pyproject.toml` and `uv.lock` for package management.
- Keep dependency changes in `pyproject.toml` and re-lock with `uv lock` or `uv add` as appropriate.
- Use the existing lightweight workflow unless the user asks to introduce new tooling.
