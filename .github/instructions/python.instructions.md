---
applyTo: "**/*.py"
---

# Python Development Standards (condensed)

## Type Safety

- Use type hints on all public function signatures. Avoid `Any` in production code.

## Financial Precision

- Use `Decimal` for money and quantities; do not use floats for prices.

## Async / DB Patterns

- Use `async with` for `AsyncSession` and `await` for async operations.

## Formatting

- Prefer `ruff` for formatting and linting.
- Default loop: `uv run ruff format .` then `uv run ruff check .`.
- Follow repo tooling for line length and formatting; current `ruff` settings live in `pyproject.toml`.

## Configuration Sources

- Prefer centralized configuration: use Azure App Configuration and Key Vault for secrets and runtime settings.
- Avoid using raw environment variables for application secrets or multi-value configuration in production; prefer platform-managed config and secret stores.
