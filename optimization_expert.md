# Portfolio Optimization Expert Guide

This document is for someone who already understands portfolio construction, constrained optimization, estimation error, and production modeling tradeoffs.

It answers three questions:

1. What would an experienced optimization expert want to know before trusting or extending this repo?
2. Which use cases are valid for the current implementation?
3. What example regression and acceptance tests should be used to keep the implementation honest?

## What This Repo Is

This repository is a FastAPI service that builds a family of single-period portfolio construction candidates, ranks them, and returns both the ranked portfolios and an efficient frontier.

It is not a portfolio accounting system, execution engine, multiperiod stochastic program, or enterprise OMS.

The implementation combines:

- market data and metadata from FMP
- Azure Key Vault-backed credential retrieval
- estimator selection in the estimation layer
- SCIP-first constrained optimization with SciPy fallback for continuous formulations
- a ranking layer that chooses among multiple model families based on realized outputs and heuristic fit

## What An Optimization Expert Will Want To Know

### 1. Problem Class And Scope

The repo is a single-period portfolio construction service.

That means:

- decisions are made on one set of expected returns and risk inputs
- current holdings matter only for turnover-aware and transaction-cost-aware models
- there is no dynamic programming, scenario tree, or explicit multiperiod state transition model
- cash treatment is model-specific rather than managed through a full portfolio accounting ledger

This is appropriate for cross-sectional portfolio recommendation and first-pass rebalancing, not for path-dependent allocation research.

### 2. Implemented Model Families

The current surface covers 16 model families:

- minimum variance
- maximum return
- utility maximization
- max Sharpe
- mean variance
- equal weight
- risk parity
- leverage via short selling
- leverage via cash borrowing
- turnover-constrained mean variance
- factor utility maximization
- factor variance constraint
- sector allocation
- transaction-cost-aware rebalancing
- cardinality plus minimum buy-in
- round-lot allocation

That is enough to cover the major notebook-family categories the repo has been targeting.

### 3. Data And Estimation Assumptions

An expert will care less about model labels and more about how $\mu$ and $\Sigma$ are produced.

Current estimator support includes:

- return estimators:
  - sample mean
  - shrunk mean
  - EWMA mean
  - geometric mean
  - median mean
- covariance estimators:
  - sample covariance
  - diagonal shrinkage
  - EWMA covariance
  - constant-correlation shrinkage
  - semicovariance

Important implications:

- the service is no longer tied to a naive sample-mean and sample-covariance path
- there is now some robustness against outliers, regime weighting, and covariance overfitting
- there is still no full Bayesian estimator stack, Black-Litterman layer, robust optimization set, or explicit forecast model

An expert should interpret this as a practical estimator menu for a service API, not as a research-complete estimation lab.

### 4. Constraint Semantics Matter More Than Model Names

Several models are only meaningful if the semantics are understood correctly.

Current semantics include:

- leverage-short-selling uses explicit gross leverage and per-asset short exposure caps
- leverage-borrowing uses an explicit cash sleeve and borrowing allowance
- turnover-constrained optimization uses current weights and a turnover budget
- sector allocation excludes ETFs and assets with unstable sector labels from the constrained subproblem
- factor models accept either explicit factor contracts or inferred market-plus-statistical factor structure
- round-lot allocation solves integer lot units rather than rounding continuous weights after the fact
- transaction-cost-aware rebalancing supports proportional costs, fixed ticket charges, minimum commissions, linear market impact, and piecewise-linear market impact

For an expert, this means the repo is already beyond toy Markowitz demos. The real question is not whether constraints exist, but whether their semantics are acceptable for the intended use case.

### 5. Solver Behavior And Fallbacks

The service uses SCIP where mixed-integer or more structured constrained formulations are needed, with SciPy fallbacks for continuous formulations.

An expert would want to know:

- mixed-integer behavior is solver-dependent and can differ materially from continuous fallback behavior
- fallback paths are designed to preserve service availability, not to guarantee identical optimal solutions
- numerical conditioning is handled at the covariance level through positive-definite repair

This repo is therefore suitable for production-minded portfolio recommendation with controlled approximations, but not for claiming exact equivalence across solvers and fallback paths.

### 6. Ranking Is A Product Layer, Not A Pure Optimization Layer

The service does not expose one single "best" optimizer. It runs a family of candidates and ranks them.

That ranking blends:

- realized expected return
- realized expected risk
- realized Sharpe ratio
- efficient-frontier context
- heuristic fit to risk tolerance and horizon

An expert should treat the ranking layer as product logic on top of optimization outputs, not as part of the underlying mathematical formulation.

### 7. Current Known Limits

An experienced optimizer will want the limits stated plainly.

Current limits:

- only one real data source is active: FMP
- provider expansion is deliberately deferred until another real source is needed
- there is no enterprise transaction-cost calibration workflow
- there is no market microstructure model beyond the current linear and piecewise-linear impact assumptions
- there is no benchmark-relative optimization objective
- there is no scenario-based or multiperiod optimization layer
- there is no full forecast stack for expected returns
- the API response normalizes most outputs into a standard result shape, so some model-specific internal details are not surfaced directly to clients

Those limits do not invalidate the repo. They define the correct operating envelope.

### 8. Household And High-Net-Worth Suitability

For a reader managing many high net worth portfolios, the first practical question is whether this repo is a household optimizer or a single-portfolio optimizer.

Today it should be read as a single-portfolio construction and rebalance engine.

That means it is well suited to:

- one account at a time
- one strategy sleeve at a time
- prototyping household policy logic before account-level implementation is formalized

It is not yet built to natively optimize across:

- taxable and tax-deferred accounts jointly
- trusts, retirement accounts, donor-advised funds, and entities under one household objective
- account-location rules where one account absorbs bonds, another equities, and another concentrated legacy holdings

For an HNW practitioner, that distinction matters. The current engine can help generate high-quality candidate allocations, but household implementation logic would still need to be layered on top.

### 9. Tax Awareness And After-Tax Suitability

An HNW reader will usually ask about taxes before asking about Sharpe ratios.

The repo does not currently implement:

- tax-lot selection
- realized gain budgets
- short-term versus long-term gain penalties
- wash sale logic
- after-tax return objectives
- asset-location optimization across account types

The correct interpretation is that this is a pre-tax optimizer with implementation-aware trading frictions, not an after-tax wealth-management optimizer.

That does not make it unusable for HNW work. It means tax-aware suitability and execution policy still need to be applied outside or above this service.

### 10. Concentrated Positions And Legacy Holdings

Many high net worth portfolios do not begin from clean universes and clean weights. They begin from messy reality:

- concentrated founder stock
- low-basis appreciated positions
- restricted or illiquid holdings
- positions that are politically, legally, or emotionally difficult to sell

The repo can support first-pass handling of those situations only indirectly today, for example by using:

- current weights in turnover-aware models
- cardinality and buy-in controls
- sector caps
- lot and implementation constraints

What it does not yet expose as first-class semantics are:

- hard hold lists
- prohibited-sell lists
- gradual unwind schedules for legacy positions
- tax-aware concentrated-position liquidation logic

An HNW expert should therefore view the repo as useful for modeling around concentrated positions, but not yet as a dedicated concentrated-position unwind engine.

### 11. Liquidity And Capacity Envelope

The repo includes ADV-aware market-impact logic, which is useful, but an experienced allocator will still want a plain-English capacity statement.

The current implementation is most credible for:

- liquid listed securities
- moderate turnover portfolios
- first-pass implementation feasibility checks
- rebalance recommendations where the main cost questions are participation-sensitive, not venue-specific

The current implementation is less credible for:

- very large books where trade slicing dominates the problem
- less-liquid securities where market impact must be calibrated empirically
- intraday or multi-session execution design

In short: the engine has implementation awareness, but not a full execution-research stack.

### 12. Policy Constraint Translation

HNW readers often think in IPS language, not optimizer language. That translation should be explicit.

Examples of current policy-style requirements that map reasonably well to the repo:

- "Do not own more than 10 names"
  - maps to cardinality plus minimum buy-in
- "Keep turnover below 15%"
  - maps to turnover-constrained optimization
- "Do not let one sector dominate the portfolio"
  - maps to sector caps
- "Respect round lots and operational trading minima"
  - maps to round-lot allocation with lot bounds
- "Account for trading frictions before recommending a rebalance"
  - maps to transaction-cost-aware rebalancing

Examples that do not yet map directly:

- "Do not realize more than $X of gains this year"
- "Place bonds in tax-deferred accounts and equities in taxable accounts"
- "Unwind this low-basis position over four quarters"
- "Track this custom benchmark within a tracking-error budget"

That line between supported and unsupported policy translation is important for client-facing suitability.

### 13. Inputs That Require Human Judgment

An experienced optimizer will not want defaults mistaken for truth.

The following inputs should be treated as governed assumptions rather than harmless knobs:

- return estimator choice
- covariance estimator choice
- shrinkage settings
- factor contracts
- sector caps
- transaction-cost coefficients
- market-impact coefficients
- current-weight inputs for rebalance problems

For HNW use, these are often investment-committee decisions or model-governance decisions. The API can carry them, but it should not be assumed that the default values are suitable for every client mandate.

### 14. Recommended Advisor Workflow

For a high net worth practice, the most defensible way to use this repo is as a decision-support engine in a staged workflow.

Recommended workflow:

1. Define the investable universe and remove clearly ineligible securities.
2. Identify concentrated, restricted, or low-basis legacy positions.
3. Decide whether the exercise is pre-trade recommendation, rebalance analysis, or implementation feasibility.
4. Choose the estimator family and any policy-level factor or sector assumptions.
5. Run the continuous model family first to understand unconstrained structure.
6. Run turnover-aware and transaction-cost-aware models using current holdings.
7. Run cardinality and round-lot variants if implementation practicality matters.
8. Compare ranked outputs, but interpret the ranking as guidance rather than truth.
9. Apply tax, household, and committee overlays outside the optimizer where needed.

That workflow is a better fit for this repo than treating it as a one-button final allocator.

## Valid Use Cases

These are valid uses of the current repo.

### Valid Use Case 1: Advisory-Style Portfolio Recommendation

Use the service to generate multiple candidate portfolios for a client or strategy profile based on:

- a selected universe
- a risk tolerance bucket or numeric score
- an investment horizon
- basic implementation assumptions

Why valid:

- multiple model families are available
- ranking is already output-aware
- the API can normalize user-friendly inputs into optimizer settings

### Valid Use Case 2: Research Comparison Across Constrained Portfolio Families

Use it to compare how different portfolio families behave on the same estimated inputs.

Why valid:

- the service runs a standardized family of models over the same $\mu$ and $\Sigma$
- the repo already includes leverage, turnover, factor, sector, transaction cost, cardinality, and round-lot variants

### Valid Use Case 3: First-Pass Rebalance Recommendation With Cost Awareness

Use transaction-cost-aware and turnover-aware models to produce rebalance candidates when you already have current weights.

Why valid:

- buy/sell decomposition exists
- proportional cost, fixed fee, minimum commission, and market-impact assumptions are supported
- turnover constraints are explicit

### Valid Use Case 4: Integer-Lot Feasibility Checks For Retail Or Operational Constraints

Use round-lot allocation when the feasibility of discrete trading units matters.

Why valid:

- integer lot units are solved directly
- repo-managed lot defaults exist
- minimum and maximum lot-unit bounds are supported

### Valid Use Case 5: Factor-Constrained Or Sector-Constrained Prototyping

Use explicit factor contracts or sector caps to test policy ideas.

Why valid:

- factor-model variants accept explicit contracts
- inferred factor structure exists when explicit contracts are absent
- sector caps work with normalized metadata handling

### Valid Use Case 6: High-Net-Worth Pre-Trade Decision Support

Use the service as a portfolio-construction engine beneath an advisor or CIO process for clients with large, bespoke portfolios.

Why valid:

- it can produce disciplined candidate portfolios under practical constraints
- it can incorporate current holdings and implementation frictions
- it is suitable as a portfolio recommendation layer before tax, household, and committee overlays are applied

### Valid Use Case 7: Legacy Position And Concentration Diagnostics

Use the service to study how a portfolio behaves around concentrated or awkward starting positions, even if final implementation is handled elsewhere.

Why valid:

- turnover-aware and cost-aware models can anchor the analysis on current holdings
- sector, cardinality, and lot semantics make the outputs more operationally plausible
- the system can function as an analytical comparison tool even when the full real-world policy set is not encoded

## Invalid Or Weak Use Cases

These are not strong fits for the current implementation.

### Invalid Use Case 1: High-Fidelity Institutional Execution Modeling

Do not treat this as a broker-calibrated execution optimizer.

Why not:

- cost semantics are useful but still simplified
- market-impact calibration is not tied to a rich empirical workflow
- there is no venue model, spread model, or intraday schedule optimizer

### Invalid Use Case 2: Liability-Aware Or Benchmark-Tracking Mandates

Do not use it as a full benchmark-relative or liability-driven optimization engine.

Why not:

- benchmark-relative tracking error objectives are not implemented
- liability streams and duration-matching semantics are absent

### Invalid Use Case 3: Multiperiod Asset Allocation Research

Do not use it as a dynamic allocation platform.

Why not:

- all models are single-period
- state evolution, scenario trees, and intertemporal tradeoffs are absent

### Invalid Use Case 4: Fully Auditable Portfolio Book Of Record

Do not treat the response as a complete portfolio accounting record.

Why not:

- the service is an optimizer and ranking API
- not all model-specific internal variables are exposed through the public response schema

### Invalid Use Case 5: Household Tax And Location Optimization

Do not present this as a household wealth-allocation engine across multiple legal account types.

Why not:

- cross-account location logic is absent
- tax-aware allocation and tax-lot semantics are absent
- household-level objective construction is not modeled explicitly

### Invalid Use Case 6: Client-Ready Autopilot Without Advisor Overlay

Do not treat ranked outputs as automatically suitable final recommendations for wealthy-client portfolios.

Why not:

- ranking is still a product layer, not fiduciary decision logic
- taxes, household context, and legacy-position realities may dominate the mathematically attractive answer
- manual or policy-level review is still required for real client use

## Important Unsupported High-Net-Worth Features

An HNW reader will usually want the missing features listed explicitly rather than inferred from the absence of code.

Important unsupported features today:

- household-level optimization across multiple account types
- tax-aware rebalancing and gain budgeting
- tax-lot-aware sell decisions
- asset-location optimization
- benchmark-relative tracking-error objectives
- explicit cash-flow withdrawal and distribution planning
- concentrated-position unwind scheduling
- custom exclusion frameworks such as household-specific ESG or legal restriction sets
- scenario stress testing and multiperiod plan design

This list should be read as a scope boundary, not a criticism. These features are precisely where many wealth platforms become much more complex than a high-quality portfolio-construction engine.

## Realistic High-Net-Worth Example Scenarios

The existing mathematical test cases are useful, but experienced practitioners also think in portfolio situations.

### Scenario 1: Low-Basis Concentrated Technology Position

A client arrives with a very large, low-basis position in one technology stock and a desire to diversify without wholesale liquidation.

Useful repo role:

- compare turnover-constrained and transaction-cost-aware candidates around the starting weights
- study how sector caps and cardinality choices change the diversified sleeve

Not yet supported directly:

- tax-budgeted sale pacing
- explicit prohibited-sell or partial-lock constraints

### Scenario 2: Retiree Household Seeking Lower Volatility

A retiree household wants lower volatility and more stable diversification without excessive implementation churn.

Useful repo role:

- compare minimum variance, risk parity, mean variance, and turnover-constrained models
- test whether cost-aware rebalance candidates differ meaningfully from naive risk reduction

### Scenario 3: Multi-Account Family Relationship

An advisor manages taxable, IRA, and trust accounts for the same family.

Useful repo role:

- generate sleeve-level target portfolios or account-level prototypes
- compare candidate allocations before household implementation logic is applied elsewhere

Not yet supported directly:

- household aggregation under one optimization objective
- tax-aware asset location

### Scenario 4: Philanthropic Or Restriction-Heavy Portfolio

A client needs to avoid certain sectors or hold a narrow approved universe.

Useful repo role:

- use custom universes, sector caps, and cardinality controls to prototype feasible diversified portfolios

Not yet supported directly:

- broad policy-rule engines for custom exclusion sets unless encoded upstream in the universe itself

### Scenario 5: Large Cash Deployment With Implementation Constraints

A client has substantial idle cash to deploy into a liquid listed universe while respecting trading practicality.

Useful repo role:

- run continuous allocations first
- compare them with round-lot and transaction-cost-aware outputs to assess implementation slippage from the ideal target

## Example Expert Test Cases

An experienced portfolio optimization practitioner will usually want tests that prove the repo is not silently violating its own mathematical intent.

### Core Continuous Sanity Tests

1. Full-investment feasibility
   - assert long-only models return weights summing to 1 within tolerance
   - assert risks and returns are finite

2. Efficient-frontier monotonicity
   - assert frontier risks are sorted ascending
   - assert expected returns are non-decreasing across frontier targets

3. Positive-definiteness repair
   - feed collinear or nearly singular assets into the estimator
   - assert the conditioned covariance remains positive definite

### Estimation Robustness Tests

1. Estimator differentiation
   - run sample, shrunk, EWMA, geometric, and median return estimators on the same price history
   - assert outputs differ where expected

2. Covariance-family differentiation
   - run sample, diagonal shrinkage, EWMA, constant-correlation shrinkage, and semicovariance on the same history
   - assert shape consistency and positive-definite conditioning after repair

3. Short-history failure
   - provide too little price history
   - assert the estimator fails clearly rather than returning unstable output

### Constraint-Integrity Tests

1. Turnover budget adherence
   - provide current weights and a small turnover cap
   - assert realized turnover does not exceed the cap beyond tolerance

2. Leverage semantics
   - for short-selling, assert negative weights occur and gross exposure is bounded
   - for borrowing, assert the cash sleeve behaves consistently with the borrow allowance

3. Cardinality and minimum buy-in
   - assert open positions do not exceed the requested maximum
   - assert positive positions respect buy-in thresholds

### Data-Driven Constraint Tests

1. Sector metadata filtering
   - include ETFs and missing-sector assets
   - assert they are excluded from the sector-constrained subproblem rather than breaking the request

2. Factor-contract validation
   - pass incomplete factor inputs
   - assert the service rejects inconsistent contracts
   - pass complete contracts and assert matrix dimensions align with the ticker universe

### Trading-Semantics Tests

1. Per-asset transaction cost calibration
   - set different proportional fees by ticker
   - assert the resulting penalty vectors preserve the requested ordering

2. Minimum commission behavior
   - use the tiered broker schedule and per-asset commission floors
   - assert minimum commission vectors are surfaced and non-negative

3. Piecewise-linear market impact
   - use heterogeneous ADV and impact coefficients
   - assert excess penalty components are non-negative and only activate past the threshold region

### Integer-Allocation Tests

1. Lot-feasibility test
   - assert shares are integer multiples of lot sizes
   - assert invested capital plus cash does not exceed the budget

2. Lot bound enforcement
   - set minimum and maximum lot units
   - assert realized lot units stay inside the requested range or are zero when infeasible

3. Repo-default lot semantics
   - omit lot sizes from the request
   - assert repo-managed defaults and metadata-aware fallbacks are applied consistently

### Service-Level Product Tests

1. Backward-compatible defaults
   - omit optional advanced fields
   - assert the service still returns the stable baseline models

2. Input validation
   - send unsupported estimator or transaction-cost model values
   - assert the API rejects them with validation errors

3. Loud credential failure
   - simulate missing FMP credentials
   - assert the request fails explicitly rather than silently degrading to a fake authenticated path

### High-Net-Worth Workflow Tests

1. Concentrated-starting-position stability
   - start from a portfolio dominated by one asset
   - assert turnover-aware and cost-aware outputs remain feasible and interpretable

2. Advisor-workflow consistency
   - run continuous, turnover-aware, and integer-feasible variants on the same universe
   - assert the outputs become more implementation-constrained in the expected direction

3. Policy translation sanity
   - encode practical advisor constraints such as sector caps, max positions, and lot bounds together
   - assert the joint constraint set either yields a feasible portfolio or fails clearly rather than silently dropping semantics

## Model Risk And Governance

An experienced HNW allocator will care not just about mathematical validity, but about governance.

Important governance points:

- estimator choice can dominate optimizer choice
- fallback solver behavior should be treated as an approximation path, not proof of equivalence
- ranking is a product recommendation layer, not fiduciary truth
- transaction-cost and impact parameters should be treated as policy assumptions unless empirically calibrated
- the best use of the engine is usually as structured decision support with advisor override, not as an autopilot allocator

That governance framing is often the difference between a useful optimization service and a misused one.

## Output Interpretation For Advisors

For advisory use, the returned portfolios should be interpreted comparatively.

Useful heuristics:

- use equal weight and risk parity as sanity anchors, not just production candidates
- use continuous models to understand the unconstrained structure of the opportunity set
- use turnover-aware and transaction-cost-aware outputs when current holdings matter materially
- use round-lot results when the recommendation must survive operational implementation
- ignore the ranking when a lower-ranked portfolio is more consistent with policy, tax, or client-specific realities not modeled here

## What An Expert Should Conclude

A portfolio optimization expert with decades of experience should view this repo as:

- a serious applied portfolio-construction service
- broad in model-family coverage
- reasonably strong on first-pass practical implementation constraints
- materially better than a toy Markowitz demo
- not yet a full institutional research or execution platform

That is the right conclusion.

The implementation is now strong enough for:

- advisory-style portfolio recommendation
- constrained portfolio family comparison
- first-pass rebalance recommendation
- factor, sector, integer, and cost-aware prototyping
- high-net-worth decision support before household and tax overlays are applied

The implementation is not yet positioned for:

- high-fidelity execution research
- multiperiod institutional asset allocation
- liability-relative or benchmark-relative optimization mandates
- full broker-calibrated transaction-cost analysis
- full household wealth optimization across account types
- tax-aware portfolio construction

## Suggested Reading Order For An Expert Reviewer

If an expert wants to inspect the code rather than just read summaries, the fastest path is:

1. `app/services/estimation.py`
2. `app/services/optimization.py`
3. `app/main.py`
4. `tests/test_estimation.py`
5. `tests/test_optimization.py`
6. `tests/test_api.py`
7. `base.md`

That sequence reveals the estimator assumptions first, then the formulation surface, then the API contract and regression coverage.
