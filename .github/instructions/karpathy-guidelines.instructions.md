---
description: Behavioral guardrails for safe, minimal, verifiable code changes (always-on)
applyTo: "**"
---

# Karpathy Guidelines (Always-On)

Apply these principles to all tasks in this repo.

## 1) Think Before Coding
- State assumptions explicitly; ask if unclear.
- If multiple interpretations exist, present them—don’t pick silently.
- Call out tradeoffs; prefer the simplest viable path.

## 2) Simplicity First
- Implement the minimum that solves the request.
- Avoid speculative flexibility, abstractions, or “nice-to-haves” unless asked.

## 3) Surgical Changes
- Touch only what the request requires.
- Match existing code style and patterns.
- Don’t refactor adjacent code unless necessary.
- If you notice unrelated issues, mention them—don’t fix them.

## 4) Goal-Driven Verification
- Define clear success criteria and verify.
- Prefer a fast local loop (format/lint/tests) when code changes.
- If skipping tests, explicitly say why and suggest what to run.
