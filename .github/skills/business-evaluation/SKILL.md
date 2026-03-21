---
name: business-evaluation
description: Evidence-based framework for evaluating business ideas via assumption mapping, customer discovery, experiment design, and lightweight unit economics.
---

# When This Skill Applies
- Evaluating whether a business idea is worth pursuing
- Turning a vague idea into testable hypotheses and a 2–4 week validation plan
- Designing low-cost experiments for problem, solution, pricing, and channel risks
- Sanity-checking viability with simple unit economics (LTV/CAC, payback)

Sample prompts (use to trigger this skill):
- "Evaluate my idea for a B2B compliance assistant and tell me what to test first."
- "Help me validate a marketplace idea; what are the riskiest assumptions and experiments?"
- "Design a 2-week plan to test demand and pricing for my product idea."

# Goal
Help the user replace intuition with evidence by:
1) identifying the riskiest assumptions, 2) proposing fast experiments with clear success criteria, and 3) defining a decision rule for whether to proceed, pivot, or stop.

This is not legal, tax, investment, or medical advice. When relevant, encourage the user to consult qualified professionals.

# Core Output Contract (Always Use This Format)
When evaluating an idea, return:
1. **One-paragraph restatement** of the idea in concrete terms (who / what job / how they discover it / why now).
2. **Riskiest assumptions (top 5)** with a short rationale for each.
3. **Scorecard (0–5 each)** across four dimensions:
   - **Desirability** (problem intensity + willingness to switch/pay)
   - **Viability** (unit economics + competitive dynamics)
   - **Feasibility** (ability to build/deliver reliably)
   - **Integrity** (ethics, privacy, safety, regulatory reality)
4. **Experiments (2–6)** mapped to assumptions, each with:
   - hypothesis, method, cost/time, sample size target, success threshold, and what you’ll do next.
5. **2–4 week plan** (sequenced) with concrete next actions.
6. **Decision rule**: what evidence means “go”, “pivot”, or “stop”.

# Process (How To Evaluate)
## Step 1 — Clarify the context (ask only what you must)
Ask up to 8 focused questions if missing:
- Who is the customer (role, segment, urgency)?
- What’s the painful job-to-be-done today? What do they do instead?
- Trigger: what event makes them seek a solution?
- Where do they discover solutions (channels)?
- Buying motion (self-serve vs sales), price sensitivity, procurement constraints
- Why you / why now / what unfair advantage exists?
- Any regulated or sensitive data involved (privacy/security)?

If the user can’t answer, proceed with explicit assumptions and label them.

## Step 2 — Create an assumption map (risk × uncertainty)
Always separate assumptions into these buckets:
- **Customer**: who has the problem + ability to buy
- **Problem**: urgency, frequency, and current alternatives
- **Solution**: whether your approach actually improves outcomes
- **Price**: willingness-to-pay and budget owner
- **Channel**: reachable acquisition path and CAC
- **Retention**: repeated use or long-term contract renewal
- **Ops/Delivery**: support load, reliability requirements
- **Constraints**: legal/regulatory, privacy, security, accessibility

Prioritize assumptions that are both:
- High impact if wrong, and
- High uncertainty right now.

Use the template: `templates/assumption-map.md`.

## Step 3 — Choose the fastest experiment that can falsify
Bias toward experiments that:
- produce **disconfirming evidence** quickly,
- cost little, and
- can be run before building the full product.

Preferred experiment types (in order):
1) **Problem interviews** (qualitative truth)
2) **Concierge / manual prototype** (prove outcome)
3) **Paid pilot / pre-order** (prove willingness-to-pay)
4) **Landing page + intent capture** (channel + messaging)
5) **Wizard-of-Oz** (simulate solution, test adoption)

Use the template: `templates/experiment-canvas.md`.

## Step 4 — Do lightweight viability math
You don’t need a full model; you need a sanity check.
Compute:
- gross margin (target depends on business, but know your costs)
- CAC payback period
- rough LTV:CAC ratio
- break-even volume

If inputs are unknown, produce ranges and note sensitivity.
Use the worksheet: `templates/unit-economics-worksheet.md`.

Optional helper script: `scripts/unit_economics.py`.

Quick run:
```
python .github/skills/business-evaluation/scripts/unit_economics.py \
   --arpa 200 --cogs 40 --cac 800 --churn-per-month 0.05
```
## Step 5 — Use an evidence ladder
When scoring and making a decision, tag the best evidence you have:
- **E0 Guess**: assumptions only
- **E1 Anecdote**: friends/family, unstructured feedback
- **E2 Interviews**: consistent pain reported by target users
- **E3 Behavioral**: signups, usage, repeated engagement
- **E4 Monetary**: deposits, pilots, contracts, pre-orders
- **E5 Retention**: renewals, long-term usage, expansion

Prefer E3+ for “go”, and E4+ for price confidence.

# Guardrails (Anti-Patterns to Avoid)
- Don’t jump to building before you can state the top 3 assumptions.
- Don’t treat vanity metrics (views/likes) as validation.
- Don’t lead witnesses in interviews; never pitch during discovery.
- Don’t ignore integrity constraints (privacy, safety, regulation) “for later”.

# Templates and Examples
Templates:
- `templates/assumption-map.md`
- `templates/experiment-canvas.md`
- `templates/customer-interview-guide.md`
- `templates/pricing-smoke-test.md`
- `templates/unit-economics-worksheet.md`
- `templates/decision-memo.md`

Examples:
- `examples/b2b-saas-evaluation-example.md`

