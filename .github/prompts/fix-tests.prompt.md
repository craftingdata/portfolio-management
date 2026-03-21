---
description: Debug and fix failing tests
tools: ["editFiles", "read", "search"]
---

Debug the failing tests.

1. Run the smallest failing pytest target first and read the full failure output
2. Identify root cause before touching any code — state it explicitly
3. Fix the minimal code path: do not rewrite passing tests or refactor unrelated code
4. Re-run to confirm green

If the fix requires changing the public API contract, stop and flag it before proceeding.
