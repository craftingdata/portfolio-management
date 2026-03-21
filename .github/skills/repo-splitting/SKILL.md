---
name: repo-splitting
description: Guidance to keep changes compatible with the planned Azure shell and vertical plugin split for Shire.
---

# Skill: Repo Splitting (Azure Shell + Plugins)

## Canonical plan

- Use `.github/instructions/repo-splitting.instructions.md` as the always-on rule set.
- Use `docs/myclaw.md` for the current hub/spoke and vertical-pack direction in this repo.

## Goal

Help every change make it easier to split this repository into:

- **Azure Shell**: reusable platform services (auth, telemetry/observability, config/Key Vault, Container Apps integration, generic APIs and background tasks)
- **Plugins**: vertical features such as Roth IRA guidance, Stripe-gated packs, and other domain-specific workflows.

All verticals are primarily delivered as a **chat experience**:

- **DevUI** for developers
- **Microsoft Teams** for end customers

The underlying agent toolkit is the **Microsoft Agent Framework**. The shell should provide the shared underpinnings to support this.

## Mental Model

- The shell provides **capabilities** (including chat/agent runtime primitives).
- Plugins provide **workflows** (domain logic expressed through prompts + tools + conversations).

Plugins should depend on the shell, not the other way around.

## Quick Classification Guide

### Shell candidates

- Authentication / principal context / tenant resolution
- Structured logging, tracing, metrics, diagnostics
- Azure Key Vault/App Configuration integration
- Container Apps deployment/runtime hooks
- Generic background task runner/orchestrator
- Microsoft Agent Framework integration and common agent runtime plumbing
- Channel adapters: DevUI (developer chat) and Teams (customer chat)
- Conversation/thread storage, message routing, tool invocation plumbing
- Generic data access patterns (not domain entities)

### Plugin candidates

- Any vertical business logic (IRA conversion, costing, records download)
- Vertical prompts, tools, and conversation flows for the domain
- Domain-specific Teams/DevUI UX choices (copy, cards, suggested actions) implemented via generic shell channel primitives

## Seams and Contracts

- Prefer **thin interfaces** at the seam (ports/adapters).
- Keep contracts independent of internal implementation details:
  - Avoid passing SQLAlchemy sessions/ORM objects across the seam
  - Prefer explicit DTOs and IDs

For chat/agent seams:

- Prefer passing **turn context + DTOs**, not raw framework/client objects.
- Keep a stable “tool contract” (name, args schema, idempotency expectations, error shape, diagnostics).

## Smell Checks

- Platform module importing vertical/domain modules → wrong direction.
- Domain logic in "common"/"agent" without clear boundaries → likely should be plugin.
- DevUI/Teams adapter branching on domain/tool names → likely should be plugin (or pushed behind a generic rendering hook).
- A change introduces a dependency that would force the shell repo to depend on a plugin repo → redesign.

## What to ask during review

- "If we moved this file to the shell repo tomorrow, what breaks?"
- "If we made a second plugin, would this code be reusable or conflicting?"
- "Is the seam contract stable enough to support multiple plugins?"

## Optional PR metadata

Add one line to PR descriptions:

- `Split-impact: shell` (or `plugin` / `mixed`)
- `Seam: <interface/adapter name or boundary>`
