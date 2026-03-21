# Copilot Workspace Instructions

These instructions keep Copilot changes aligned with this repository's actual shape: a small Python FastAPI service for portfolio optimization.

## What this repo does

- Exposes a FastAPI API for portfolio optimization and portfolio ranking.
- Uses market data fetched in `app/services/data_service.py`, with synthetic fallback data when needed.
- Runs several optimization strategies in `app/services/optimization.py` and ranks them in `app/services/ranking.py`.

## Working assumptions

- The codebase is Python-only in its current form.
- Dependency management is driven by `requirements.txt`, not `uv`, Poetry, or a monorepo toolchain.
- Tests live under `tests/` and are run with `pytest`.

## Repo structure pointers

- API entrypoint: `app/main.py`
- Schemas: `app/models/schemas.py`
- Services: `app/services/`
- Tests: `tests/`

## Editing guidance

- Keep changes surgical. This is a small codebase; avoid introducing framework or architecture complexity unless the user asks for it.
- Preserve the public API contract unless the task explicitly requires changing request or response models.
- Prefer deterministic tests that mock external market-data access instead of relying on live network calls.
- When changing optimizer or ranking behavior, update the narrowest relevant tests in `tests/`.

## Verification

- Default local verification is:
  - `python -m pip install -r requirements.txt`
  - `python -m pytest tests -q`
- For focused changes, run the narrowest relevant pytest target first.

## Do not do

- Do not add Azure, deployment, or infrastructure guidance unless the repository actually grows those assets.
- Do not introduce secrets or environment-specific credentials into git.
- Do not rewrite the optimization stack or change model semantics without explicit user request.
