# High-Net-Worth Gaps Implementation Guide

## Purpose

This document evaluates what it would take to make this repository materially more useful for high-net-worth portfolio management and, eventually, credible as a go-to HNW portfolio-management tool.

It answers four questions:

1. What HNW-relevant capability is already present in the repo?
2. What is still missing to support real HNW portfolio management?
3. What documents, regulations, data, and algorithms would be required to close those gaps?
4. In what order should those gaps be implemented?

## Bottom-Line Assessment

This repo is already useful for one narrow but important HNW use case: single-portfolio, pre-tax portfolio construction and rebalance analysis with practical implementation constraints.

It is not yet a go-to HNW portfolio-management tool.

The main reason is structural rather than cosmetic:

- the current system optimizes one portfolio at a time
- HNW portfolio management is usually household-level, tax-aware, policy-driven, and audit-sensitive
- the repo does not yet model tax lots, cross-account location, household objectives, legacy-position unwind plans, benchmark-relative mandates, or advisory compliance workflow

The current repo should be understood as an HNW decision-support engine for portfolio construction, not a full HNW operating platform.

## Are These Straightforward Coding Tasks Or Hidden-Issue Programs?

They are not all the same kind of work.

Some gaps are relatively straightforward engineering tasks:

- explicit do-not-buy and do-not-sell restrictions
- richer policy templates
- persisted run assumptions
- benchmark reference inputs
- explanation and rationale output
- recommendation audit records
- proposal and approval state tracking

These mostly extend the current API, schema, and service pattern without requiring a new mathematical or operating foundation.

Some gaps are moderate engineering tasks with material design risk:

- benchmark-aware optimization
- policy-constraint compilation
- household and account schema expansion
- scenario and stress overlays
- compliance trace capture and reproducibility controls

These are buildable, but requirements quality matters more than coding speed because rule precedence, contradiction handling, and explanation quality will determine whether the implementation is actually usable.

The most important gaps are not straightforward coding tasks at all. They are requirements, data, and governance programs with code attached.

That group includes:

- tax-aware rebalancing
- tax-lot optimization
- household-level optimization
- asset-location optimization
- concentrated-position unwind workflows
- custodian and books-of-record integration
- end-to-end advisor operating workflow support

The hidden issues behind those gaps are:

- ambiguous business rules, because there is no single correct tax-aware or household optimizer
- missing source data, especially tax lots, account metadata, household mappings, and custodial truth
- compliance and legal interpretation requirements
- mathematical complexity from lot-level and multi-account optimization
- testing difficulty, because many important cases become workflow and edge-case heavy rather than purely numerical

The practical implication is that the repo should not treat the entire HNW backlog as a sequence of ordinary coding tickets. Some parts are ordinary engineering. The hardest parts require policy design, data contracts, and compliance review before code can be written correctly.

## Known HNW Planning And Implementation Systems

The most useful comparison is not against one single competitor, because the HNW market is fragmented. In practice, firms assemble a stack spanning planning, portfolio accounting, proposal generation, rebalancing, tax management, and reporting.

The systems below are representative categories and examples, not a claim that every platform offers every capability in every deployment.

### Financial Planning Systems

Representative systems:

- eMoney Advisor
- MoneyGuidePro
- RightCapital

What they are strong at:

- goals-based planning
- cash-flow planning
- retirement projections
- scenario planning with client-facing workflows
- household-level financial context

How this repo compares:

- this repo is stronger on raw portfolio-construction logic than a pure planning tool
- this repo is much weaker on household planning, cash-flow modeling, and client/advisor planning workflow

### Portfolio Management, Reporting, And Rebalancing Platforms

Representative systems:

- Addepar
- Orion
- Black Diamond
- Envestnet Tamarac
- Morningstar Office or related advisor workstation tools

What they are strong at:

- books of record and custodial integration
- household views
- reporting
- proposal workflows
- billing, reconciliation, and operating controls
- rebalancing workflows integrated into advisory operations

How this repo compares:

- this repo can already be stronger than many broad platforms on customizable optimizer semantics per unit of code
- this repo is dramatically weaker on data integration, reporting, reconciliation, auditability, and operational workflow

### Tax-Aware Overlay, Direct Indexing, And Implementation Specialists

Representative systems or providers:

- Smartleaf
- 55ip
- Parametric
- Aperio

What they are strong at:

- tax-aware rebalancing
- tax-loss harvesting
- direct indexing workflows
- transition management
- client-specific implementation overlays

How this repo compares:

- this repo currently does not compete seriously here
- until tax lots, gain budgets, wash-sale handling, and after-tax optimization exist, it should not be positioned as equivalent to a tax-managed implementation engine

### Family Office And HNW Operations Ecosystem

Representative systems or categories:

- Addepar in family-office deployments
- specialized trust-accounting and reporting systems
- CRM and workflow systems such as Salesforce-based advisory stacks
- custodian portals and OMS/PMS integrations

What they are strong at:

- multi-entity and multi-account visibility
- operational workflow
- approvals, exceptions, and reporting
- integration across advisory, reporting, and execution teams

How this repo compares:

- this repo is currently an analytical engine, not an operating system for a family office or HNW advisory practice

## Scored Capability Matrix

Score meaning:

- `0`: essentially absent
- `1`: minimal or highly incomplete
- `2`: useful in a narrow workflow
- `3`: solid first-pass capability
- `4`: strong production-grade capability
- `5`: category-defining or core-system strength

The scores below are directional and are meant to help judge relative position, not to claim vendor-by-vendor precision.

| Capability Area                           | This Repo | Planning Systems | Advisor Platforms | Tax-Managed Implementation Systems |
| ----------------------------------------- | --------- | ---------------- | ----------------- | ---------------------------------- |
| Single-portfolio optimization flexibility | 4         | 1                | 2                 | 4                                  |
| Household modeling                        | 0         | 4                | 4                 | 2                                  |
| Tax-lot awareness                         | 0         | 1                | 2                 | 5                                  |
| Tax-aware rebalancing                     | 0         | 1                | 2                 | 5                                  |
| Concentrated-position workflows           | 1         | 2                | 2                 | 4                                  |
| Policy and restriction handling           | 2         | 2                | 4                 | 4                                  |
| Benchmark-relative mandate handling       | 1         | 2                | 3                 | 3                                  |
| Cash-flow and goals planning              | 0         | 5                | 2                 | 1                                  |
| Custodial and books-of-record integration | 0         | 1                | 5                 | 3                                  |
| Reconciliation and operational controls   | 0         | 1                | 5                 | 3                                  |
| Audit trail and compliance workflow       | 1         | 2                | 4                 | 4                                  |
| Proposal and advisor workflow support     | 1         | 4                | 5                 | 3                                  |
| Reporting and client-ready output         | 1         | 4                | 5                 | 2                                  |
| Transparent optimizer semantics           | 4         | 1                | 2                 | 3                                  |
| Custom quantitative extensibility         | 4         | 1                | 2                 | 3                                  |

## Readout From The Matrix

The matrix shows a non-obvious but important point.

This repo is already relatively strong where many broad advisor platforms are often weakest:

- transparent optimizer semantics
- customizable quantitative logic
- focused portfolio-construction flexibility

But it is weakest in exactly the areas that determine whether an HNW tool becomes central to daily practice:

- householding
- tax-lot and after-tax implementation
- books of record and custodial integration
- proposal workflow and reporting
- audit and compliance operating controls

That means the repo is closer to a quant engine than to an HNW operating platform.

It also means the path to relevance depends on which competitive lane matters most:

- if the target is better internal CIO or research tooling, the repo is already in a promising position
- if the target is advisor-platform relevance, workflow and data integration gaps dominate
- if the target is tax-managed implementation relevance, after-tax and lot-level logic dominate

## Where This Repo Stands Relative To Known Systems

The current repo sits in a useful but narrow position.

It is best described as:

- a customizable portfolio-construction and rebalance-analysis engine
- stronger on transparent optimization logic than many broad advisor platforms
- weaker than established HNW platforms on planning, books of record, tax management, householding, reconciliation, auditability, and workflow integration

If compared to planning systems, this repo is too narrow.

If compared to portfolio accounting and advisor platform systems, this repo is too thin operationally.

If compared to tax-aware direct-indexing and overlay systems, this repo is too early in after-tax and lot-level implementation.

That means the repo is currently most credible as one component inside an HNW stack, not as the stack itself.

## What Would Move It Up The Market Ladder Fastest

If the goal is to judge where the repo stands against known systems, the highest-leverage moves are not evenly distributed.

### To Compete Better With Broad Advisor Platforms

Most valuable additions:

- persisted recommendation records
- policy templates and restrictions
- household and account entities
- audit and explanation outputs
- proposal and approval workflows

These would move the repo closer to a usable advisor decision tool.

### To Compete Better With Tax-Managed Implementation Systems

Most valuable additions:

- tax-lot ingestion
- gain-budget-aware rebalancing
- wash-sale-aware harvesting logic
- after-tax objective functions

These are harder, but they define whether the repo is relevant for real taxable HNW implementation.

### To Compete Better With Planning Systems

Most valuable additions:

- household cash-flow modeling
- goals and spending-rule support
- trust and entity-aware planning logic
- client-facing scenario workflows

These would be a major expansion and are likely not the right immediate target unless the product direction explicitly shifts toward full planning.

## What Is Already Covered

The current repo already provides a useful foundation for HNW advisory and CIO workflows in the following areas:

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

- pre-trade portfolio recommendation
- first-pass rebalance analysis
- concentration diagnostics
- policy prototyping for sectors, position counts, and turnover
- implementation-aware comparison of candidate allocations

These capabilities are already reflected in [OPTIMIZATION_EXPERT_GUIDE.md](OPTIMIZATION_EXPERT_GUIDE.md).

## What Is Not Yet Covered Enough

The current documentation now states the limitations clearly, but it does not yet provide an implementation roadmap for closing them.

The main uncovered area is not awareness of the gaps. The main uncovered area is an execution plan across:

- data acquisition
- API and schema expansion
- algorithm design
- compliance and auditability
- workflow integration
- model governance

That is the purpose of this document.

## Capability Gaps That Matter Most

### 1. Household-Level Optimization

HNW relationships are usually managed across multiple legal accounts with different tax treatment, liquidity rules, and ownership structures.

Examples:

- taxable brokerage
- IRA and Roth IRA
- trust accounts
- donor-advised funds
- family entities

What is missing:

- a household entity model
- account-to-household mapping
- account-type-aware constraints
- cross-account asset-location optimization
- household objective functions with account-level implementation constraints

Why this matters:

Without householding, the optimizer can produce individually sensible account portfolios that are jointly inefficient, tax-suboptimal, or policy-inconsistent.

### 2. Tax-Aware Rebalancing And Tax-Lot Logic

For HNW work, taxes often dominate nominal optimizer improvements.

What is missing:

- tax-lot ingestion
- cost basis and acquisition date tracking
- short-term versus long-term gain treatment
- realized gain budgets
- wash-sale-aware replacement logic
- after-tax objective functions
- tax-loss harvesting logic
- charitable gifting candidate selection for highly appreciated positions

Why this matters:

Without tax-aware logic, the repo may recommend trades that are mathematically attractive pre-tax but economically inferior after taxes.

### 3. Concentrated-Position Management

Many HNW portfolios start with a concentrated low-basis legacy position, not a clean target allocation problem.

What is missing:

- prohibited-sell flags
- minimum-hold flags
- gradual unwind schedules
- gain-budget-constrained de-risking
- collar, exchange-fund, or overlay placeholder treatment if the product direction ever includes them

Why this matters:

Concentrated-position management is one of the most common HNW portfolio problems. A tool that cannot model it directly will remain a secondary tool.

### 4. Policy And Restriction Engine

HNW portfolios often require hard, client-specific rules.

Examples:

- do not sell these securities
- do not buy tobacco or weapons
- hold at least 5 percent cash in this trust
- do not let municipal bonds exceed a given share in taxable accounts
- this account may only hold ETFs and mutual funds

What is missing:

- a first-class restriction model
- account-specific and household-specific policy layers
- rule precedence and conflict handling
- audit-friendly rule evaluation output

Why this matters:

Advisors need to explain why a recommendation did or did not satisfy a client mandate. That requires explicit policy representation, not just hidden optimizer parameters.

### 5. Benchmark And Mandate-Aware Optimization

Many real HNW mandates are framed relative to benchmarks, policy portfolios, or spending rules.

What is missing:

- benchmark-relative risk and return controls
- tracking-error constraints or objectives
- policy-portfolio distance metrics
- withdrawal and distribution-aware planning
- liability-aware or cash-flow-aware optimization for trust and spending accounts

Why this matters:

The current repo is strong on absolute portfolio construction and weak on mandate-relative portfolio management.

### 6. Accounting, Books Of Record, And Corporate Actions

HNW portfolio management depends on clean holdings and transaction records, not just market prices.

What is missing:

- custodial position ingestion
- transaction history ingestion
- tax-lot books of record
- corporate action handling
- cash ledger behavior
- dividend and interest accrual awareness
- reconciliation workflows

Why this matters:

Without a credible position and ledger layer, optimization outputs remain recommendations rather than operationally controlled portfolio decisions.

### 7. Compliance, Explainability, And Auditability

A go-to HNW tool has to survive compliance review and advisor scrutiny.

What is missing:

- decision trace capture for each recommendation
- persisted assumption snapshots
- model versioning tied to outputs
- override logging
- pre-trade and post-trade compliance checks
- standardized suitability and rationale output
- reproducibility for the same inputs and model version

Why this matters:

In HNW advisory practice, explainability and audit trails are often as important as the optimization itself.

### 8. Data Breadth Beyond FMP

The repo intentionally uses FMP today, and that is adequate for the current scope.

It is not enough for a go-to HNW system.

What is missing:

- custodial data feeds
- tax-lot feeds
- account registration and household metadata
- benchmark and index data
- security master enrichment
- fixed-income analytics if bonds matter materially
- alternative-asset position handling if the product direction expands there
- more authoritative corporate action and classification data

Why this matters:

HNW portfolio management depends on internal and custodial truth, not only public market data.

### 9. Advisor Workflow And Operating Model Support

To become a default tool, the repo would need to support how HNW teams actually work.

What is missing:

- saved households and account profiles
- proposal versus approved-portfolio states
- advisor review queues
- exception handling workflows
- CIO override workflows
- proposal reports and client-readable rationale generation
- integration points for OMS, PMS, CRM, and custodian systems

Why this matters:

Even a mathematically strong optimizer will not become central if it does not fit the advisory operating model.

## Documents Needed To Build This Properly

These are the most important internal or external documents that would be needed to implement the missing HNW functionality well.

### Business And Policy Documents

- target operating model for advisors, CIOs, traders, and compliance reviewers
- sample investment policy statements for representative HNW client types
- household construction rules for taxable, tax-deferred, trust, and philanthropic accounts
- rebalancing policy and override policy
- tax-management policy, including gain budgets and loss-harvesting guardrails
- concentrated-position policy for restricted and low-basis holdings
- benchmark and policy-portfolio definitions by strategy
- restriction taxonomy for ESG, legal, trust, and client-specific constraints

### Data And Integration Documents

- custodian file specifications
- portfolio accounting data dictionaries
- tax-lot file layouts
- transaction and cash-ledger schemas
- corporate-action event schemas
- security master and asset-class mapping rules
- benchmark constituent and return source definitions
- household and account master-data definitions

### Model Governance Documents

- model inventory and model ownership
- model validation standards
- estimator selection policy
- transaction-cost calibration methodology
- benchmark selection methodology
- stress-test and scenario methodology
- exception and override review procedures

## Regulations And Legal Frameworks To Account For

This section is a requirements checklist, not legal advice. Counsel and compliance would need to confirm applicability for the firm and jurisdiction.

Likely relevant U.S. frameworks include:

- Investment Advisers Act of 1940 fiduciary obligations for RIAs
- SEC books and records requirements, including Advisers Act Rule 204-2
- Advisers Act Rule 206(4)-7 compliance program expectations
- Form ADV disclosures where model usage, conflicts, and process disclosures may be implicated
- SEC Marketing Rule considerations if portfolio analytics or backtested outputs are presented externally
- Regulation Best Interest if the operating context includes broker-dealer recommendations rather than only RIA advice
- Internal Revenue Code wash-sale rules under Section 1091
- cost-basis and holding-period rules relevant to tax-aware trading and reporting
- trust-law or prudent-investor standards where trust accounts are in scope
- client-specific legal restrictions, gifting rules, and entity-level constraints where family office structures are involved

If the product ever expands internationally, tax and suitability logic should be treated as jurisdiction-specific, not portable by default.

## Data Needed Beyond The Current Repo

The current repo mainly works from historical prices, metadata, and lightweight liquidity estimates.

To support real HNW management, the following data is needed.

### Required Core Data

- account master data
- household membership and ownership structure
- account tax status and legal type
- current positions by account
- tax lots by account and security
- cost basis, acquisition date, and holding period
- realized and unrealized gain summaries
- transaction history
- cash balances and pending cash flows
- income and withdrawal requirements

### Required Market And Security Data

- benchmark returns and benchmark constituents
- richer corporate action data
- more durable security master classifications
- fixed-income attributes if bonds and munis are material
- better liquidity data for large or less-liquid positions
- borrow availability and financing assumptions if shorting or leverage is in scope

### Useful Optional Data

- advisor and client restriction profiles
- ESG or values-based screening metadata
- external asset data for held-away positions
- alternative-asset placeholders and valuation data
- scenario and stress datasets

## Algorithms And Technical Components Needed

### 1. Household Allocation Engine

Needed capabilities:

- household objective function spanning multiple accounts
- account-level feasibility constraints
- asset-location optimization across account types
- household-to-account sleeve decomposition

Likely implementation shape:

- mixed-integer or structured constrained optimization
- objective terms for tax drag, turnover, tracking error, and policy deviation

### 2. Tax-Aware Rebalancing Engine

Needed capabilities:

- lot-level sell decision variables
- gain and loss realization accounting
- short-term and long-term tax-rate treatment
- gain-budget constraints
- loss-harvesting candidate selection
- wash-sale exclusion windows and replacement security rules

Likely implementation shape:

- mixed-integer optimization or decomposition heuristics
- post-optimization lot-selection refinement where exact optimization is too expensive

### 3. Concentrated-Position Unwind Engine

Needed capabilities:

- staged unwind schedules
- minimum residual holding rules
- annual tax budgets
- scenario analysis for unwind pace versus diversification benefit

Likely implementation shape:

- multiperiod optimization or rolling-horizon heuristic engine
- constraint templates for restricted or legacy positions

### 4. Restriction And Policy Compiler

Needed capabilities:

- translate policy rules into optimizer constraints
- detect contradictory rules
- produce plain-English explanations for active and binding constraints

Likely implementation shape:

- a rule layer that compiles to optimization parameters and hard constraints
- evaluation traces stored with each run

### 5. Benchmark-Aware And Cash-Flow-Aware Optimization

Needed capabilities:

- tracking error constraints
- benchmark-relative active weight controls
- policy-portfolio distance penalties
- withdrawal and contribution handling

Likely implementation shape:

- extensions to the objective function and risk model
- cash-flow-aware rebalance optimization

### 6. Scenario And Stress Framework

Needed capabilities:

- scenario return shocks
- factor stress analysis
- liquidity stress analysis
- concentration stress analysis
- downside or tail-risk-aware ranking overlays

Likely implementation shape:

- scenario matrices layered on top of current optimization outputs
- optional robust-optimization or stress-penalty extensions later

### 7. Audit And Explainability Layer

Needed capabilities:

- input snapshots
- model version hashes
- recommendation rationale generation
- override tracking
- reproducible run identifiers

Likely implementation shape:

- persistent recommendation records
- structured explanation objects returned alongside portfolio results

## Recommended Implementation Phases

### Phase 1: Make The Current Engine HNW-Ready For Decision Support

Primary goal:

- remain single-portfolio, but become materially more useful in HNW practice

Recommended additions:

- explicit restriction inputs such as do-not-buy and do-not-sell lists
- benchmark and policy-portfolio reference inputs
- richer output explanations and assumption capture
- saved policy templates and account metadata hooks
- persisted run records for auditability

Why first:

This is the fastest path to making the repo genuinely more useful without rewriting it into a full platform.

### Phase 2: Add Tax-Aware Single-Account Rebalancing

Primary goal:

- make taxable-account recommendations economically credible

Recommended additions:

- tax-lot data model
- gain-budget constraints
- short-term versus long-term gain handling
- basic wash-sale-aware harvesting support

Why second:

For many HNW workflows, tax-aware single-account optimization delivers more value than immediately attempting full household optimization.

### Phase 3: Add Household And Asset-Location Logic

Primary goal:

- optimize across related accounts instead of one account at a time

Recommended additions:

- household entity model
- account grouping and role metadata
- household-level policy constraints
- asset-location optimization

Why third:

This is where the repo starts moving from useful optimizer to real HNW portfolio-management engine.

### Phase 4: Add Multiperiod And Concentrated-Position Workflows

Primary goal:

- handle the legacy-position and staged-implementation problems common in HNW portfolios

Recommended additions:

- rolling-horizon concentration management
- planned unwind schedules
- cash-flow-aware household rebalance planning
- scenario and stress testing

Why fourth:

This is high value, but materially more complex than the earlier phases.

### Phase 5: Add Operating-System Features Around The Optimizer

Primary goal:

- become operationally central rather than analytically interesting

Recommended additions:

- custodian and portfolio-accounting integrations
- proposal, approval, and override workflows
- advisor and compliance dashboards
- export paths to OMS and reporting systems

Why fifth:

This is what would make the tool sticky in real advisory operations.

## Suggested File And Architecture Impact

If the repo follows the phased path above, the likely code impact would include:

- new household, account, policy, tax-lot, and benchmark schemas in the models layer
- new service modules for restrictions, tax logic, household optimization, and recommendation persistence
- a persistence layer for saved runs, policies, and audit trails
- expansion of the API beyond a single optimize endpoint into household, policy, and recommendation workflows
- significant new test coverage for tax, policy, auditability, and multi-account behavior

This is not a small incremental feature set. It is a deliberate expansion from optimizer API into HNW portfolio-management application.

## Minimum Standard To Call This A Go-To HNW Tool

At minimum, the repo would need all of the following before it could plausibly be described that way:

- tax-aware rebalancing for taxable accounts
- household and account modeling
- explicit restriction and policy support
- benchmark-aware mandate handling
- reproducible audit trails and rationale capture
- integration with custodial or portfolio-accounting source data
- advisor review and override workflow support

Without those capabilities, the repo can still be strong, but it should be described more narrowly as an HNW portfolio-construction and rebalance-analysis engine.

## Recommended Next Step

If the goal is to improve usefulness quickly rather than attempt a full HNW platform immediately, the best next implementation target is:

1. explicit restriction support
2. persisted run assumptions and explanation output
3. tax-lot schema design and taxable-account rebalancing requirements

That sequence would improve real advisory usefulness faster than jumping directly to full household optimization.
