# Investor Segment Gap Comparison

## Purpose

This document compares the two investor-segment gap analyses in this repository:

- [hnw_gaps.md](hnw_gaps.md)
- [accredited_investor_gaps.md](accredited_investor_gaps.md)

The goal is to make the difference in product direction explicit.

## Bottom-Line Difference

The high-net-worth path is primarily constrained by householding, tax complexity, governance, and advisor workflow.

The accredited-investor path is primarily constrained by alternatives, liquidity budgeting, offering workflow, and the interaction between liquid public sleeves and illiquid private sleeves.

Both require more than straightforward coding. They diverge in what kind of complexity dominates.

## Side-By-Side Comparison

| Dimension | High-Net-Worth Focus | Accredited-Investor Focus |
| --- | --- | --- |
| Core missing structure | household and multi-account modeling | multi-sleeve liquid and illiquid modeling |
| Primary implementation challenge | after-tax household optimization | alternatives, liquidity, and offering workflow |
| Most important data gap | tax lots, household/account mapping, custodial truth | private-product metadata, commitments, calls, distributions, liquidity terms |
| Most important workflow gap | proposal, approval, compliance, and household implementation workflow | suitability, offering eligibility, sleeve reporting, and liquidity oversight |
| Tax complexity | central and unavoidable | important, but often secondary to sleeve and product structure at first |
| Alternatives complexity | relevant but not always dominant | usually central to the segment definition |
| Planning overlap | high | moderate |
| Family-office operating overlap | high | lower unless the accredited investor is also an HNW household |
| Benchmark/policy need | policy portfolio and household mandate framing | sleeve policy and liquid-versus-illiquid allocation framing |
| Best current repo fit | pre-tax HNW decision-support engine for one portfolio at a time | liquid public-markets engine inside a broader accredited-investor stack |

## Where The Repo Is Closer Today

The repo is closer to the accredited-investor liquid-sleeve use case than to the full HNW operating-platform use case.

Reason:

- the repo already handles liquid public-market portfolio construction reasonably well
- it does not yet handle householding or tax-lot logic, which are central to full HNW relevance
- it also does not yet handle alternatives and offering workflow, which are central to full accredited-investor-platform relevance

So the repo is closest to a narrower accredited-investor outcome:

- optimize the liquid sleeve
- account for practical trading constraints
- treat the illiquid sleeve as an external policy input until deeper alternatives support is built

## Strategic Implication

If the product goal is faster near-term usefulness, the accredited-investor liquid-sleeve path is the lower-complexity market-adjacent expansion.

If the product goal is full wealth-platform relevance, the HNW path is broader and more defensible, but materially harder because the household, tax, compliance, and workflow stack becomes unavoidable.

## Recommended Decision Lens

Use these questions to decide which path deserves priority:

1. Is the intended product mostly a portfolio engine or a full advisory operating platform?
2. Is the immediate user more likely to need household tax coordination or alternative-investment sleeve management?
3. Does the available data source roadmap favor custodial and tax-lot integrations, or private-product and administrator integrations?
4. Is the near-term differentiation supposed to come from transparent quant logic or from operational completeness?

If the near-term objective is practical product traction with the least structural expansion, the accredited-investor liquid-sleeve path is the better first extension.

If the near-term objective is to become deeply embedded in wealth-management operations, the HNW path is eventually more strategic, but much harder.