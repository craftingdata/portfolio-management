---
name: github-pr-review-comments
description: Extract PR review comments (inline + top-level) from the active or open pull request, and present them in a review-ready structure.
---

# When This Skill Applies
- You need to **extract** all PR feedback to review it systematically
- You need both:
  - **Inline review comments** (attached to files/lines)
  - **Top-level PR conversation comments** (general discussion on the PR)

# Sample Prompts (to trigger this skill)
Use wording like the following in Copilot Chat:
- "Extract PR review comments from the active pull request (inline + top-level) and present a numbered summary and full details."
- "Pull all inline review comments for the current PR and list them by file and line."
- "Get all PR comments (review comments + conversation comments) and de-duplicate them; include comment IDs."
- "Use the GitHub PR tools to fetch the active PR and show review comments one by one."

# Goal
Produce a complete, de-duplicated list of PR comments with enough metadata to:
- summarize each comment (1 sentence)
- show full detail one-by-one
- (optionally) reply later using comment IDs

# Activation Notes (how Copilot decides)
Copilot will typically follow this skill when you explicitly mention:
- "active pull request" or "open pull request"
- "review comments" and/or "inline comments"
- "extract" / "list" / "summarize" PR feedback

If you want to be very explicit, start your request with:
- "Use the `github-pr-review-comments` skill to ..."

# Preferred Tools (in this repo)
1. `github-pull-request_activePullRequest` (best: includes changed files + review comments + status)
2. `github-pull-request_openPullRequest` (use if the PR is open/visible but not checked out)

# Extraction Procedure
## A) Fetch the PR context
- Call `github-pull-request_activePullRequest`.
- If there is no active PR, call `github-pull-request_openPullRequest`.

## B) Extract and normalize comment sets
From the returned PR payload, extract (at minimum) these categories:

### 1) Inline review comments (code comments)
Normalize each record into:
- `id` (numeric) — used for replying via REST
- `path` — file path in repo
- `line` / `original_line` (when present)
- `diff_hunk` (when present)
- `body`
- `author.login`
- `created_at`
- `in_reply_to_id` (when present)
- `pull_request_review_id` (when present)

### 2) Top-level PR conversation comments
These are comments on the PR conversation (not attached to a specific line).
Normalize each record into:
- `id`
- `body`
- `author.login`
- `created_at`

### 3) (Optional) Review summaries
If present, extract review-level info (APPROVE / REQUEST_CHANGES / COMMENT) and map to:
- `review_id`
- `state`
- `body` (top-level review body)
- `author.login`

## C) Present output in a review-ready structure
Return two views:

1) **Index view** (for scanning)
- list each comment with a stable label like `C1`, `C2`, …
- one-sentence summary per comment
- include `path:line` for inline comments

Default presentation: **group inline comments by file** (`path`), then by line.

2) **Detail view** (for step-through)
- for each comment, show full `body` plus key metadata (author, timestamp, file/line)

# Practical Options (choose in your request)
If you care about any of these, say so explicitly:
- **Only unresolved / latest**: exclude outdated comments on obsolete diffs (when detectable).
- **Group by file (default)**: cluster inline comments by `path`, then by line.
- **Threading**: show replies beneath their root comment using `in_reply_to_id`.
- **Sort order**: by file path, by timestamp, or by “most recent first”.

# Output Template
Use this structure when reporting extracted comments:

- **Summary (grouped by file)**
  - `<path/to/file.py>`
    - `C1` (L<line>) — <one sentence>
    - `C2` (L<line>) — <one sentence>
  - `<top-level>`
    - `C3` — <one sentence>

- **Details (grouped by file)**
  - `<path/to/file.py>`
    - `C1`
      - Author: <login>
      - When: <created_at>
      - Location: <path>#<line>
      - Comment ID: <id>
      - Body:
        <full body>
  - `<top-level>`
    - `C3`
      - Author: <login>
      - When: <created_at>
      - Comment ID: <id>
      - Body:
        <full body>

# Fallback: Extract via `gh api` (when tool payload lacks what you need)
If the PR tools don’t include all comment types or IDs, use GitHub CLI:

## 1) Determine owner/repo and PR number
- If you already have the PR URL, parse it.
- Or use: `gh pr view --json number,url,headRefName`

## 2) Inline review comments (PR review comments)
```bash
gh api repos/{owner}/{repo}/pulls/{pull_number}/comments
```

## 3) Top-level PR conversation comments (issue comments on the PR)
```bash
gh api repos/{owner}/{repo}/issues/{pull_number}/comments
```

## 4) Reviews (optional)
```bash
gh api repos/{owner}/{repo}/pulls/{pull_number}/reviews
```

# Notes / Gotchas
- The `comment_id` used to reply to a **review comment** is the numeric `id` field from `pulls/{pull_number}/comments`.
- Do **not** use GraphQL `node_id` when replying via REST.
- “Top-level PR comments” come from the Issues API because PRs are Issues underneath.

# Related (Optional) Follow-on Work
If you later want to reply or resolve threads:
- Reply to inline review comment:
  - `POST /repos/{owner}/{repo}/pulls/{pull_number}/comments/{comment_id}/replies`
- Resolve review threads via GraphQL `resolveReviewThread` mutation.
