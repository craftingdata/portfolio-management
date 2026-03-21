---
name: exa-search
description: Use Exa's HTTPS API for grounded web search, answer generation, and content retrieval when EXA_API_KEY is available on the slug. Prefer this on sam for web research that should stay within the approved Exa contract.
metadata:
  {
    "openclaw":
      {
        "emoji": "EXA",
        "requires": { "bins": ["curl"], "env": ["EXA_API_KEY"] },
      },
  }
---

# exa-search

## When to use

Use this skill when the task needs current web search, source-backed answers, or page contents and the slug already has `EXA_API_KEY` injected.

This repo can project the same shared Exa key from `sam` into child slugs during normal install or deploy convergence.

Do not bypass that reviewed Key Vault flow by hardcoding keys into config, prompts, or files.

## Guardrails

- Keep the query narrow and task-specific.
- Prefer `highlights` over full `text` unless the task requires contiguous page content.
- Prefer Exa results for research and retrieval, not arbitrary browsing.
- Do not write the API key into files, logs, or generated config.

## Search

Use Exa search for grounded results with highlights:

```bash
curl -sS https://api.exa.ai/search \
  -H "x-api-key: $EXA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "<query>",
    "type": "deep",
    "num_results": 5,
    "contents": {
      "highlights": {
        "max_characters": 4000
      }
    }
  }'
```

## Answer

Use Exa answer when the user wants a direct answer with citations:

```bash
curl -sS https://api.exa.ai/answer \
  -H "x-api-key: $EXA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "<question>"
  }'
```

## Contents

Use Exa contents when you already know the URLs:

```bash
curl -sS https://api.exa.ai/contents \
  -H "x-api-key: $EXA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"],
    "text": {
      "max_characters": 12000
    }
  }'
```

## Output handling

- Summarize the result for the user.
- Keep the cited URLs from the response when they matter to the task.
- If Exa returns no results, simplify the query before widening scope.
