# Accredited Investor Gaps Implementation Guide

## Purpose

This document evaluates what it would take to make this repository materially more useful for accredited investors and the advisors, CIOs, or platforms serving them.

It answers five questions:

1. What accredited-investor-relevant capability already exists in the repo?
2. What is missing to support accredited-investor workflows well?
3. Which gaps are straightforward engineering versus deeper requirements and data problems?
4. Which documents, regulations, data, and algorithms would be needed to close those gaps?
5. Where would this repo stand relative to known systems serving accredited investors?

## Bottom-Line Assessment

This repo is already useful for a meaningful accredited-investor use case: single-portfolio construction and rebalance analysis for liquid public-market portfolios with practical constraints.

It is not yet a go-to accredited-investor portfolio platform.

The reason is different from the HNW case in one important way.

For accredited investors, the biggest issue is not always householding. The bigger issue is that accredited-investor portfolios often mix:

- public equities and ETFs
- taxable implementation concerns
- private funds and alternatives
- illiquid sleeves with infrequent valuation updates
- lockups, gates, subscription windows, and capital-call behavior
- client-specific concentration and liquidity tolerances

The current repo does not model those features directly.

The current repo should therefore be understood as a public-markets portfolio-construction engine that may be useful inside an accredited-investor stack, not as a complete accredited-investor planning and implementation platform.

## What Is Already Covered

The current repo already provides a useful base for accredited-investor-oriented public-market allocation work in the following areas:

- single-period portfolio construction
- multiple optimizer families rather than one fixed optimizer
- turnover-aware and transaction-cost-aware rebalancing
- factor and sector constraints
- cardinality and minimum buy-in controls
- round-lot allocation
- current-holdings-aware analysis
- practical estimator selection for return and covariance inputs
- ranking across candidate portfolios rather than returning one opaque answer

That means the repo already supports:

- liquid-public-market portfolio recommendation
- first-pass rebalance analysis
- concentration diagnostics for listed holdings
- policy prototyping for sectors, turnover, and position counts
- implementation-aware comparison of candidate allocations

These strengths still matter for accredited investors because a large share of accredited-investor portfolios contain a substantial liquid sleeve.

## What Is Different From The HNW Case

An accredited investor is not automatically an HNW household with full family-office complexity.

That changes the priority order.

Compared with the HNW case, the accredited-investor gap analysis should put relatively more emphasis on:

- alternatives and semi-liquid products
- concentration and liquidity budgeting
- suitability and offering constraints
- subscription, redemption, and lockup rules
- capital-call and distribution-aware portfolio views
- benchmarking and sleeve construction across liquid and illiquid buckets

Compared with the HNW case, it often puts relatively less immediate emphasis on:

- multi-entity household optimization
- trust-specific workflows
- household asset location across many tax wrappers

Those can still matter, but they are not the defining gap for every accredited-investor use case.

## Are These Straightforward Coding Tasks Or Hidden-Issue Programs?

They are a mix.

Some gaps are relatively straightforward engineering tasks:

- explicit restriction inputs such as do-not-buy and do-not-sell lists
- benchmark and policy-sleeve reference inputs
- persisted run assumptions and rationale output
- concentration and liquidity-budget inputs
- proposal and approval state tracking
- recommendation audit records

These mostly extend the current API and service pattern.

Some gaps are moderate engineering tasks with design risk:

- benchmark-aware optimization
- sleeve-aware portfolio decomposition
- scenario and stress overlays
- compliance trace capture and reproducibility controls
- alternative-asset placeholder modeling

These are feasible, but correctness depends on good requirements and on how much of the portfolio must be represented formally versus approximately.

The hardest gaps are not straightforward coding tasks. They are requirements, data, valuation, and operational programs with code attached.

That group includes:

- illiquid and semi-liquid sleeve modeling
- capital-call and distribution-aware portfolio views
- subscription and redemption constraint handling
- private-fund cash-flow modeling
- tax-aware rebalancing if taxable implementation matters
- books-of-record and custodial integration
- offering eligibility and suitability workflow support

The hidden issues behind those gaps are:

- stale or irregular valuations for private assets
- inconsistent or incomplete position and cash-flow data
- ambiguous suitability and offering policies
- the need to reconcile liquid-market optimization with illiquid-sleeve realities
- testing difficulty because many edge cases are event-driven rather than daily-mark-to-market

The practical implication is that an accredited-investor roadmap can start with ordinary engineering, but it stops being ordinary as soon as alternatives, private funds, and offering workflow become first-class requirements.

## Capability Gaps That Matter Most

### 1. Multi-Sleeve Portfolio Representation

Many accredited-investor portfolios should be represented as at least two sleeves:

- liquid public markets
- illiquid or semi-liquid alternatives

What is missing:

- explicit sleeve definitions
- sleeve-level target ranges
- liquid versus illiquid allocation budgeting
- sleeve-aware reporting and optimization inputs

Why this matters:

Without sleeve-aware structure, the repo can optimize the liquid sleeve while ignoring the fact that the investor may already be overallocated to private credit, venture, real estate, or hedge funds.

### 2. Alternative Asset And Private Fund Modeling

Accredited investors often access products that do not behave like listed equities.

Examples:

- private equity funds
- venture funds
- hedge funds
- interval funds
- private credit vehicles
- private real estate funds

What is missing:

- alternative asset classifications
- stale-price and appraisal-based valuation handling
- commitment versus NAV distinction
- lockups, gates, and notice-period metadata
- subscription window and redemption window handling

Why this matters:

A portfolio engine that treats illiquid alternatives as if they were daily tradable securities will misstate risk, liquidity, and implementation feasibility.

### 3. Liquidity Budgeting And Cash-Flow Awareness

Accredited-investor portfolios often need explicit liquidity management even when they are not full HNW households.

What is missing:

- liquidity buckets
- minimum-liquid-reserve rules
- capital-call reserves
- distribution and cash-flow-aware portfolio views
- redemption-timeline-aware constraints

Why this matters:

Without liquidity budgeting, an apparently diversified target portfolio can still be operationally fragile.

### 4. Concentration And Exposure Controls

Accredited investors can have concentrated listed positions, concentrated alternative exposures, or both.

What is missing:

- cross-sleeve concentration controls
- issuer, manager, strategy, and vintage-year exposure limits
- more explicit hold and prohibited-sell semantics
- concentration-aware scenario analysis

Why this matters:

Traditional sector and ticker limits are not enough when concentration can also occur by fund manager, private strategy, or correlated illiquid sleeve.

### 5. Benchmark And Policy-Sleeve Handling

Accredited-investor portfolios are often managed relative to model portfolios or policy sleeves rather than a pure public-market benchmark.

What is missing:

- benchmark-relative risk and return controls
- policy-sleeve distance metrics
- target-range enforcement across sleeves
- public-versus-private allocation policy representation

Why this matters:

The repo is currently strong on absolute public-market optimization and weak on policy-portfolio management.

### 6. Suitability, Eligibility, And Offering Workflow

Accredited-investor offerings often depend on eligibility, investor status, risk tolerance, liquidity tolerance, and offering-specific documentation.

What is missing:

- investor-profile metadata for suitability
- offering eligibility flags
- documentation and approval checkpoints
- product-level restriction handling
- private-offering workflow support

Why this matters:

Even if the optimizer can recommend an allocation, it is not operationally useful if the product workflow for accredited offerings is absent.

### 7. Tax-Aware Implementation

Tax may not be the first differentiator for every accredited-investor use case, but it still matters for taxable public-market sleeves.

What is missing:

- tax-lot ingestion
- gain-budget-aware rebalancing
- wash-sale-aware harvesting logic
- after-tax objective options

Why this matters:

Without tax-aware logic, the public-market implementation layer remains economically incomplete.

### 8. Books Of Record, Custodial Data, And Private-Asset Data

Accredited-investor portfolios are often fragmented across custodians, fund administrators, portals, and internal records.

What is missing:

- custodial position ingestion
- transaction history ingestion
- cash ledger behavior
- private-asset position and cash-flow ingestion
- administrator data normalization
- reconciliation workflows

Why this matters:

Without a credible data layer, the system cannot represent the real portfolio, only the tradable public subset.

### 9. Reporting, Auditability, And Workflow Support

To become central to accredited-investor portfolio management, the repo would need more than optimization.

What is missing:

- proposal versus approved-portfolio states
- audit trails and assumption snapshots
- advisor or IC review workflow
- client-readable rationale output
- allocation and liquidity reporting across sleeves

Why this matters:

The repo is currently an analytical engine, not a workflow system.

## Documents Needed To Build This Properly

### Business And Policy Documents

- target operating model for advisors, CIOs, product teams, and compliance reviewers
- sample accredited-investor portfolio policies
- sleeve construction policy for liquid, semi-liquid, and illiquid buckets
- liquidity reserve policy and capital-call reserve policy
- concentration policy across issuers, managers, strategies, and sleeves
- approved-product and restricted-product taxonomy
- benchmark and policy-sleeve definitions by strategy
- offering approval and override policy

### Data And Integration Documents

- custodian file specifications
- private-fund administrator file layouts
- capital-call and distribution data schemas
- transaction and cash-ledger schemas
- security master and product master mappings
- benchmark constituent and return source definitions
- investor-profile and suitability master-data definitions

### Model Governance Documents

- model inventory and model ownership
- estimator and benchmark selection policy
- liquidity classification methodology
- stale-price and valuation handling policy
- scenario and stress methodology
- exception and override review procedures

## Regulations And Legal Frameworks To Account For

This section is a requirements checklist, not legal advice. Counsel and compliance would need to confirm applicability for the firm and jurisdiction.

Likely relevant U.S. frameworks include:

- accredited-investor eligibility concepts under Regulation D offerings
- suitability and recommendation-process obligations applicable to the operating model
- Investment Advisers Act of 1940 fiduciary obligations for RIAs where advisory activity is in scope
- SEC books and records requirements, including Advisers Act Rule 204-2 where applicable
- Advisers Act Rule 206(4)-7 compliance program expectations
- SEC Marketing Rule considerations if model outputs, performance illustrations, or backtests are shown externally
- offering-specific transfer, subscription, lockup, and eligibility restrictions
- tax rules relevant to taxable public-market implementation, including wash-sale treatment when applicable

If the product includes private offerings or adviser workflows, product, legal, and compliance review become part of the implementation path, not an afterthought.

## Data Needed Beyond The Current Repo

The current repo mainly works from historical prices, metadata, and lightweight liquidity estimates.

To support accredited-investor portfolio management more credibly, the following data is needed.

### Required Core Data

- investor profile and suitability metadata
- liquid public-market positions
- private-fund and alternative positions
- commitment amounts, funded amounts, and unfunded commitments
- capital-call history and expected cash needs
- distribution history
- cash balances and liquidity reserves
- transaction history

### Required Market And Product Data

- benchmark returns and benchmark constituents
- product metadata for private and semi-liquid vehicles
- liquidity terms such as lockups, gates, and notice periods
- richer corporate action data for public markets
- more durable security and product master classifications

### Useful Optional Data

- manager-level and strategy-level exposure mappings
- vintage-year and structure metadata for private funds
- scenario and stress datasets
- adviser-defined product restrictions and approved lists

## Algorithms And Technical Components Needed

### 1. Sleeve-Aware Allocation Engine

Needed capabilities:

- liquid and illiquid sleeve representation
- sleeve target ranges
- public-market optimization conditional on existing alternative exposures
- cross-sleeve exposure aggregation

Likely implementation shape:

- constrained optimization for the liquid sleeve
- policy accounting layer for illiquid sleeves that are not fully tradable

### 2. Liquidity Budgeting Engine

Needed capabilities:

- liquidity bucket scoring
- reserve constraints
- capital-call reserve handling
- redemption-window-aware portfolio rules

Likely implementation shape:

- rule layer plus constrained optimization penalties or hard limits

### 3. Alternative Exposure And Concentration Engine

Needed capabilities:

- manager, strategy, vintage, and issuer exposure aggregation
- cross-sleeve concentration controls
- stress overlays for correlated alternative exposures

Likely implementation shape:

- exposure mapping layer with reporting and optimization constraints where feasible

### 4. Benchmark-Aware And Policy-Sleeve Optimization

Needed capabilities:

- tracking error constraints
- policy-range enforcement
- benchmark-relative public-market optimization

Likely implementation shape:

- extensions to the objective function and risk model

### 5. Tax-Aware Public-Market Implementation Engine

Needed capabilities:

- tax-lot sell decisions
- gain-budget constraints
- wash-sale-aware harvesting support

Likely implementation shape:

- mixed-integer optimization or decomposition heuristics for taxable public sleeves

### 6. Scenario And Stress Framework

Needed capabilities:

- liquidity stress analysis
- alternative valuation shock scenarios
- concentration stress analysis
- downside overlays for public and private sleeves

Likely implementation shape:

- scenario matrices layered on top of current optimization outputs and portfolio exposures

### 7. Audit And Workflow Layer

Needed capabilities:

- input snapshots
- model version hashes
- suitability and approval traces
- client-readable rationale generation
- persisted recommendation records

Likely implementation shape:

- persistent recommendation records and workflow state transitions

## Known Accredited-Investor Planning And Implementation Systems

The accredited-investor market is also fragmented. In practice, firms combine planning, advisor-platform, alternative-investment, and portfolio-reporting systems.

Representative categories and examples include:

### Planning And Advisor Tools

- eMoney Advisor
- MoneyGuidePro
- RightCapital

Typical strengths:

- goals-based planning
- client workflow
- household context
- scenario planning

How this repo compares:

- stronger on transparent portfolio-construction logic
- weaker on planning workflow and client-facing planning context

### Portfolio Management And Reporting Platforms

- Addepar
- Orion
- Black Diamond
- Envestnet Tamarac

Typical strengths:

- custodial integration
- reporting
- proposal workflows
- operational controls
- multi-account visibility

How this repo compares:

- stronger on transparent customizable optimization
- much weaker on data integration, reconciliation, reporting, and workflow

### Alternative-Investment And Accredited-Offering Ecosystems

- iCapital
- CAIS
- platform-based alternative investment marketplaces and operating tools

Typical strengths:

- accredited-offering access and workflow
- product due diligence and distribution process support
- subscription document workflow
- alternative product administration context

How this repo compares:

- this repo does not currently compete here
- it lacks offering workflow, private-product metadata, and suitability gating

### Tax-Managed Implementation Specialists

- Smartleaf
- 55ip
- Parametric
- Aperio

Typical strengths:

- tax-aware rebalancing
- tax-loss harvesting
- personalized implementation

How this repo compares:

- the repo is not yet competitive until tax-aware implementation exists for taxable sleeves

## Scored Capability Matrix

Score meaning:

- `0`: essentially absent
- `1`: minimal or highly incomplete
- `2`: useful in a narrow workflow
- `3`: solid first-pass capability
- `4`: strong production-grade capability
- `5`: category-defining or core-system strength

The scores below are directional and are meant to help judge relative position, not to claim vendor-by-vendor precision.

| Capability Area                                   | This Repo | Planning Systems | Advisor Platforms | Alternative-Investment Platforms | Tax-Managed Implementation Systems |
| ------------------------------------------------- | --------- | ---------------- | ----------------- | -------------------------------- | ---------------------------------- |
| Liquid public-market optimization flexibility     | 4         | 1                | 2                 | 1                                | 4                                  |
| Liquid versus illiquid sleeve handling            | 0         | 2                | 2                 | 4                                | 1                                  |
| Alternative asset and private-fund representation | 0         | 1                | 2                 | 5                                | 1                                  |
| Liquidity budgeting and reserve handling          | 1         | 2                | 3                 | 4                                | 2                                  |
| Concentration and exposure controls               | 2         | 2                | 3                 | 3                                | 4                                  |
| Policy and restriction handling                   | 2         | 2                | 4                 | 3                                | 4                                  |
| Benchmark or policy-sleeve handling               | 1         | 2                | 3                 | 2                                | 3                                  |
| Tax-lot awareness                                 | 0         | 1                | 2                 | 0                                | 5                                  |
| Tax-aware rebalancing                             | 0         | 1                | 2                 | 0                                | 5                                  |
| Suitability and offering workflow                 | 0         | 2                | 3                 | 5                                | 2                                  |
| Custodial and books-of-record integration         | 0         | 1                | 5                 | 2                                | 3                                  |
| Audit trail and compliance workflow               | 1         | 2                | 4                 | 4                                | 4                                  |
| Proposal and advisor workflow support             | 1         | 4                | 5                 | 3                                | 3                                  |
| Reporting and client-ready output                 | 1         | 4                | 5                 | 3                                | 2                                  |
| Transparent optimizer semantics                   | 4         | 1                | 2                 | 1                                | 3                                  |
| Custom quantitative extensibility                 | 4         | 1                | 2                 | 1                                | 3                                  |

## Readout From The Matrix

The matrix shows that the repo already has real strength in one narrow lane:

- transparent optimization logic for liquid public-market portfolios
- customizable quantitative behavior
- implementation-aware public-market allocation analysis

It is weak in the areas that determine whether it can serve as an accredited-investor platform rather than just a portfolio engine:

- alternative asset representation
- liquidity budgeting for semi-liquid and illiquid sleeves
- offering and suitability workflow
- custodial, administrator, and reporting integration
- tax-aware implementation for taxable public sleeves

That means the repo is currently most credible as the liquid-sleeve optimization component inside an accredited-investor stack.

## Where This Repo Stands Relative To Known Systems

The current repo sits in a narrow but defensible position.

It is best described as:

- a customizable public-markets portfolio-construction and rebalance-analysis engine
- stronger on transparent optimizer behavior than many broad platforms
- weaker than accredited-investor platforms on alternative products, eligibility workflow, liquidity management, integration, and reporting

If compared to planning systems, this repo is too narrow.

If compared to advisor and reporting platforms, this repo is too thin operationally.

If compared to alternative-investment ecosystems, this repo is missing the entire offering and private-product workflow layer.

If compared to tax-managed implementation specialists, this repo is too early in after-tax and lot-level functionality.

That means the repo is currently most credible as one component inside an accredited-investor stack, not as the stack itself.

## What Would Move It Up The Market Ladder Fastest

### To Compete Better As An Accredited-Investor Portfolio Engine

Most valuable additions:

- sleeve-aware portfolio representation
- concentration and liquidity-budget controls
- benchmark and policy-sleeve inputs
- persisted recommendation records and rationale output

These would make the repo substantially more useful without forcing it to become a full alternatives platform immediately.

### To Compete Better With Alternative-Investment Platforms

Most valuable additions:

- alternative-product metadata model
- lockup, gate, and notice-period handling
- capital-call and distribution-aware portfolio views
- suitability and offering workflow support

These are higher complexity because they require business-process and data-integration decisions, not just math.

### To Compete Better With Tax-Managed Implementation Systems

Most valuable additions:

- tax-lot ingestion
- gain-budget-aware rebalancing
- wash-sale-aware harvesting logic
- after-tax objective functions

These are hard, but they define whether taxable public sleeves can be managed credibly.

## Ranked Engineering Backlog

The backlog below ranks work by a blend of market impact, dependency risk, and implementation realism.

Score meaning:

- `Effort`: `Low`, `Medium`, `High`, `Very High`
- `Dependency Risk`: `Low`, `Medium`, `High`
- `Market Impact`: `Low`, `Medium`, `High`, `Very High`

| Rank | Work Item                                                      | Effort    | Dependency Risk | Market Impact | Why It Belongs Here                                                                            |
| ---- | -------------------------------------------------------------- | --------- | --------------- | ------------- | ---------------------------------------------------------------------------------------------- |
| 1    | Add sleeve-aware portfolio inputs                              | Medium    | Medium          | Very High     | This is the first structural step toward representing accredited-investor portfolios honestly. |
| 2    | Add concentration and liquidity-budget controls                | Medium    | Medium          | Very High     | This improves real-world usability for portfolios mixing liquid and illiquid exposure.         |
| 3    | Persist recommendation assumptions and rationale               | Low       | Low             | High          | This improves advisor trust, repeatability, and product usability quickly.                     |
| 4    | Add recommendation records and workflow states                 | Medium    | Medium          | High          | This moves the repo closer to an actual operating tool instead of a one-shot optimizer.        |
| 5    | Add benchmark and policy-sleeve inputs                         | Medium    | Medium          | High          | This makes the tool more suitable for model-portfolio and policy-range workflows.              |
| 6    | Define private-product metadata model                          | Medium    | High            | High          | This is a prerequisite for any serious alternative-investment support.                         |
| 7    | Add alternative-asset placeholder and reporting support        | Medium    | High            | High          | This allows the liquid sleeve to be optimized in the context of an existing alternatives book. |
| 8    | Add liquidity-term metadata such as lockups and notice periods | Medium    | High            | High          | This is required before the system can speak credibly about liquidity management.              |
| 9    | Add capital-call and distribution-aware portfolio views        | High      | High            | High          | This is a major step toward alternatives-aware portfolio management.                           |
| 10   | Add suitability and offering workflow support                  | High      | High            | Very High     | This is essential if the repo is meant to participate in accredited-offering workflows.        |
| 11   | Add tax-lot ingestion for taxable public sleeves               | High      | High            | High          | This is the prerequisite for after-tax public-market implementation.                           |
| 12   | Add tax-aware rebalance logic                                  | Very High | High            | High          | Important, but should follow the data-model work instead of coming first.                      |
| 13   | Add custodian and administrator integrations                   | Very High | High            | Very High     | This is strategically important but operationally expensive and integration-heavy.             |

## Minimum Feature Set: Credible Accredited-Investor Liquid-Sleeve Platform

This is the narrower and more achievable target state.

The repo can plausibly reach this position without becoming a full alternatives platform.

Minimum required features:

- sleeve-aware inputs that distinguish liquid public exposure from external illiquid exposure
- concentration limits across the liquid sleeve and policy-aware aggregate exposure checks
- liquidity-budget inputs and minimum reserve controls
- benchmark or policy-sleeve reference inputs
- persisted assumptions, rationale output, and recommendation records
- proposal versus approved recommendation states
- basic audit trail and reproducibility metadata
- alternative-asset placeholder reporting sufficient to condition liquid-sleeve optimization on existing illiquid exposure

What this would allow the product to claim credibly:

- public-market portfolio construction for accredited-investor portfolios
- liquid-sleeve optimization that respects the existence of alternatives
- advisor-usable recommendations with auditability and policy framing

What it would still not support credibly:

- full accredited-offering workflow
- private-fund operating workflow
- tax-managed implementation parity with specialist systems

## Minimum Feature Set: Credible Alternatives-Aware Accredited-Investor Platform

This is the broader and harder target state.

Minimum required features:

- all liquid-sleeve-platform features listed above
- private-product metadata model with lockups, gates, notice periods, and subscription or redemption constraints
- commitment, funded, unfunded, and NAV-aware position representation
- capital-call and distribution-aware portfolio views
- alternative manager, strategy, and vintage exposure aggregation
- suitability and accredited-offering eligibility workflow support
- private-product restriction and approval workflow
- administrator and custodial data ingestion with reconciliation support
- cross-sleeve reporting and liquidity analysis
- optional tax-aware public-market implementation for taxable sleeves

What this would allow the product to claim credibly:

- alternatives-aware portfolio construction for accredited-investor portfolios
- liquid and illiquid sleeve visibility in one decision process
- operational support for accredited-product portfolio workflow beyond pure optimization

What it would still not necessarily make the product:

- a full HNW family-office platform
- a category-defining alternative-investment marketplace
- a best-in-class tax-managed implementation engine

## Recommended Next Step

If the goal is to improve usefulness quickly without trying to become a full accredited-investor platform immediately, the best next implementation sequence is:

1. add sleeve-aware portfolio inputs for liquid versus illiquid allocations
2. add concentration and liquidity-budget controls
3. add persisted assumptions, rationale output, and recommendation records
4. define the private-product metadata and suitability data model before attempting deeper alternative-investment workflow

That sequence would make the repo more relevant to accredited-investor use cases without prematurely taking on the full complexity of HNW family-office or alternative-offering operating systems.
