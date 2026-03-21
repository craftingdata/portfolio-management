# Portfolio Optimization Implementation Handoff

This file is the execution brief for continuing this repository toward broader parity with the Gurobi finance notebook family, while keeping the current repository architecture intact.

The intended consumer is another model, so this document is explicit about:

- what already exists
- what rules must not be broken
- which files should be edited for each milestone
- what tests must be updated
- what the next implementation order should be

## Objective

Expand this FastAPI portfolio optimizer from its current small single-period model set into a more complete portfolio-construction system covering better estimation, more Markowitz variants, richer constraints, and eventually rebalancing and factor models.

The repo should continue using:

- FMP Ultimate as the market-data source
- Azure Key Vault for the FMP API key
- FinanceToolkit only when it is running with an FMP API key
- SCIP for constrained and mixed-integer formulations
- SciPy as a fallback only for continuous formulations

## Repository Snapshot

Current top-level structure:

- `app/main.py`: FastAPI entrypoint and `/optimize` endpoint
- `app/models/schemas.py`: request and response models
- `app/services/data_service.py`: FMP data fetch, Azure Key Vault secret lookup, synthetic fallback, estimation entrypoint
- `app/services/estimation.py`: return and covariance estimation plus FinanceToolkit risk diagnostics
- `app/services/optimization.py`: core Markowitz models plus utility, leverage, turnover, and `run_all_models`
- `app/services/ranking.py`: output-aware applicability ranking with efficient-frontier context
- `tests/test_api.py`: API tests
- `tests/test_optimization.py`: optimization tests
- `tests/test_ranking.py`: ranking tests
- `tests/test_data_service.py`: FMP and Key Vault tests
- `tests/test_estimation.py`: estimator tests
- `README.md`: public project documentation
- `pyproject.toml`: dependencies managed by `uv`

## Current Working Behavior

The current application behavior is:

1. `/optimize` receives investment amount, risk tolerance, investment horizon, tickers, and risk-free rate.
2. `app/main.py` calls `get_market_data()` in `app/services/data_service.py`.
3. `data_service.py` retrieves the FMP API key from Azure Key Vault using `DefaultAzureCredential` and `SecretClient`.
4. FMP historical prices are fetched and aligned.
5. `estimate_market_inputs()` in `app/services/estimation.py` computes returns, annualized expected returns, and annualized covariance.
6. FinanceToolkit risk diagnostics are collected only if an FMP API key is available.
7. `run_all_models()` in `app/services/optimization.py` runs the current portfolio constructors, including utility maximization, long-short leverage, borrowing/cash-sleeve leverage, and turnover-constrained rebalancing.
8. `generate_efficient_frontier()` produces an efficient frontier from the current mean/covariance inputs.
9. `rank_portfolios()` in `app/services/ranking.py` combines heuristic ordering with realized model outputs and frontier context.
10. The API returns ranked portfolios plus the efficient frontier.

## Implemented Already

These items are complete and should be treated as the baseline, not reintroduced as open work:

- FMP-based historical price retrieval exists.
- Azure Key Vault secret lookup for the FMP API key exists.
- Missing FMP credentials fail loudly.
- FinanceToolkit is not constructed through a local no-key branch anymore.
- Estimation currently computes annualized mean return and covariance from aligned price history.
- Utility maximization is implemented alongside the existing core Markowitz models.
- Efficient frontier generation is implemented and returned by the API.
- Long-short leverage, borrowing/cash-sleeve leverage, and turnover-constrained optimization are implemented.
- Ranking now uses realized portfolio outputs plus efficient-frontier context, not only static heuristics.
- The API request model now includes leverage and turnover controls plus current weights for rebalance-aware optimization.
- Factor-model utility/variance variants, sector-allocation limits, transaction-cost-aware rebalancing, cardinality/minimum-buy-in, and round-lot allocation are now implemented as optional advanced model families.
- Synthetic data still exists, but only as a fallback for non-authentication FMP fetch failures.
- Tests now cover the optimizer models, ranking behavior, API responses, FMP fetch behavior, Key Vault secret caching, estimator behavior, and API failure behavior when the FMP key is unavailable.

## Non-Negotiable Rules

Any future implementation must preserve these rules unless explicitly changed by the user:

1. Do not reintroduce `yfinance`.
2. Do not reintroduce a no-API-key FinanceToolkit branch using local `historical` input.
3. If FinanceToolkit is used, it should use the FMP-backed API-key path.
4. Missing FMP credentials must fail loudly, not silently degrade.
5. Keep changes surgical. This is a small Python service, not a framework rewrite.
6. Do not change the public API contract unless the task explicitly requires it.
7. Keep tests deterministic. Mock FMP and Azure Key Vault in unit and integration tests.
8. Do not rely on live FMP or live Azure for automated tests.

## Current Dependency State

Important packages already present in `pyproject.toml`:

- `fastapi`
- `pyscipopt`
- `scipy`
- `numpy`
- `pandas`
- `httpx`
- `azure-identity`
- `azure-keyvault-secrets`
- `financetoolkit`
- `pyyaml`
- `pytest`
- `pytest-asyncio`

No package-management migration is needed. Continue using `uv`.

## Known Technical Constraints

The next model should be aware of these repo-specific realities:

- `data_service.py` now has a lightweight FMP provider wrapper, but the public module still centralizes orchestration and synthetic fallback behavior.
- `optimization.py` currently exposes one function per strategy plus `run_all_models()`. It now includes utility, leverage, and turnover-aware models, but it is still not split into model-builder abstractions.
- `ranking.py` now blends heuristic tables with realized optimizer output quality and frontier context.
- The API request model now exposes leverage, turnover, sector-cap, calibrated transaction-cost and market-impact controls, basic cardinality controls, estimator selection, explicit factor-model inputs, and configurable lot sizes, but the surrounding provider and validation layers are still relatively thin.
- Synthetic fallback still exists in `data_service.py`; it should be treated as test/degradation behavior, not as a preferred production path.
- FinanceToolkit diagnostics are best-effort. The optimizer should not depend on FinanceToolkit outputs to function.

## Verified Test Command

The focused command that already passes after the latest changes is:

```bash
uv run pytest tests -q
```

Most recent verified result before this handoff: `45 passed`.

General repo test command:

```bash
uv run pytest tests -q
```

## Gaps Versus the Broader Gurobi Notebook Family

The repo now has first-pass implementations for the major advanced notebook families, but it is still short of broader parity in a few important areas:

- richer factor-model infrastructure beyond the current explicit-contract or market-factor proxy paths
- broader metadata normalization, ETF handling, and sector/industry semantics
- richer lot-size semantics beyond the current request-driven lot-size assumptions
- deeper transaction-cost calibration beyond the current Interactive Brokers-style baseline plus per-asset overrides, especially fixed-fee schedules
- more rigorous market-impact modeling beyond the current linear ADV-based formulation
- deeper provider expansion and estimator families beyond the current FMP wrapper and sample or shrinkage options

## Coverage Verification

The previous version of this handoff was enough for planning and sequencing, but not fully enough for direct implementation against the Gurobi notebook family.

What was missing before this update:

- explicit mapping from Gurobi notebook topics to repo tasks
- mathematical formulation guidance per notebook family
- required input data beyond prices and covariance
- clear indication of which techniques are continuous versus mixed-integer

After the additions below, `base.md` should be sufficient for another model to implement the techniques incrementally without first re-reading the Gurobi notebook index.

Current coverage is better than the previous version of this handoff: the repo now has direct implementations and tests for the basic Markowitz family, efficient frontier generation, leverage variants, turnover-constrained rebalancing, factor-model variants, sector-constrained optimization, transaction-cost-aware rebalancing, cardinality/minimum-buy-in, round-lot allocation, and output-aware ranking.

## Source Of Truth And Retrieval Pointers

Another model should not rely on this file alone if it needs to verify omissions or implementation details. These are the primary retrieval targets.

### External Source Of Truth

Use the Gurobi Finance notebook index as the canonical feature list:

- `https://gurobi-finance.readthedocs.io/en/latest/modeling_notebooks.html`

Important notebook pages to consult when implementing or verifying coverage:

- Data preparation:
  - `https://gurobi-finance.readthedocs.io/en/latest/modeling_notebooks/mean_covariance.html`
- Basic Markowitz family:
  - `https://gurobi-finance.readthedocs.io/en/latest/modeling_notebooks/basic_model_maxmu.html`
  - `https://gurobi-finance.readthedocs.io/en/latest/modeling_notebooks/basic_model_minsigma.html`
  - `https://gurobi-finance.readthedocs.io/en/latest/modeling_notebooks/basic_model_maxutility.html`
- Factor models:
  - `https://gurobi-finance.readthedocs.io/en/latest/modeling_notebooks/factor_models_objective.html`
  - `https://gurobi-finance.readthedocs.io/en/latest/modeling_notebooks/factor_models_constraint.html`
- Portfolio constraints:
  - `https://gurobi-finance.readthedocs.io/en/latest/modeling_notebooks/minimum_buy_in.html`
  - `https://gurobi-finance.readthedocs.io/en/latest/modeling_notebooks/concentration.html`
  - `https://gurobi-finance.readthedocs.io/en/latest/modeling_notebooks/leverage_short_selling.html`
  - `https://gurobi-finance.readthedocs.io/en/latest/modeling_notebooks/leverage_borrow.html`
  - `https://gurobi-finance.readthedocs.io/en/latest/modeling_notebooks/turnover.html`
  - `https://gurobi-finance.readthedocs.io/en/latest/modeling_notebooks/round_lots.html`
  - `https://gurobi-finance.readthedocs.io/en/latest/modeling_notebooks/sector_allocation.html`
- Transaction costs and slippage:
  - `https://gurobi-finance.readthedocs.io/en/latest/modeling_notebooks/transaction_costs.html`
  - `https://gurobi-finance.readthedocs.io/en/latest/modeling_notebooks/rebalancing.html`
  - `https://gurobi-finance.readthedocs.io/en/latest/modeling_notebooks/market_impact.html`

### Internal Source Of Truth

Use these repo files to determine what is already implemented and what is still missing:

- `README.md`: current public feature claims
- `app/services/optimization.py`: implemented optimization techniques and solver behavior
- `app/services/data_service.py`: implemented market-data pipeline and metadata limitations
- `app/services/estimation.py`: implemented estimator behavior and FinanceToolkit usage
- `app/services/ranking.py`: current ranking logic
- `app/models/schemas.py`: actual API-exposed inputs and outputs
- `app/main.py`: route-level orchestration and current contract behavior
- `tests/test_optimization.py`: what optimizer behavior is already asserted
- `tests/test_api.py`: what API behavior is already asserted
- `tests/test_data_service.py`: current FMP and Azure behavior under test
- `tests/test_estimation.py`: estimator and FinanceToolkit behavior under test

## How To Find Omissions

Another model should use the following comparison method, not guess from memory.

### Step 1: Enumerate Gurobi Feature Families

Build a checklist from the Gurobi notebook index:

- data preparation
- max return
- min variance
- max utility
- factor model objective
- factor model constraint
- minimum buy-in
- cardinality
- diversification
- leverage by short-selling
- leverage by borrowing cash
- turnover
- round lots
- sector allocation
- transaction costs
- rebalancing with costs
- market impact

### Step 2: Enumerate Repo Capabilities

Inspect these concrete repo functions and contracts:

- optimization functions in `app/services/optimization.py`
- request and response fields in `app/models/schemas.py`
- route behavior in `app/main.py`
- metadata availability in `app/services/data_service.py`
- tests under `tests/`

Current implemented optimizer techniques, based on repo code, are:

- minimum variance
- maximum return
- utility maximization
- leverage by short-selling
- leverage by borrowing cash
- turnover-constrained mean variance
- max Sharpe ratio
- mean variance
- equal weight
- risk parity
- factor-model utility maximization
- factor-model variance constraint
- sector allocation
- transaction-cost-aware rebalancing
- cardinality and minimum buy-in
- round-lot allocation

Current notable omissions, based on repo code, are now limited to further calibration and enrichment work rather than missing core model families:

- richer factor families beyond the current market-factor proxy
- more detailed liquidity and market-impact calibration
- broader provider metadata beyond sector and industry
- transaction-cost calibration beyond the default proportional assumptions

Review finding:

- output-driven ranking should no longer be treated as an omission
- the current repo already ranks using realized returns, risk, Sharpe ratio, and efficient-frontier context in `app/services/ranking.py`
- the remaining ranking work is extension, not initial implementation

### Step 3: Check Data Prerequisites

Before calling something an omission in the optimizer, confirm whether the supporting data exists.

Examples:

- sector allocation is blocked unless provider metadata includes sector classification
- round lots require current price and lot-size logic
- rebalancing requires current holdings or current weights in the request model
- factor models require factor exposure data that the repo does not yet source

### Step 4: Classify Each Omission

For each missing technique, classify it as one of:

- missing solver logic only
- missing API schema only
- missing market-data or metadata source
- missing both modeling and input data

This prevents another model from incorrectly trying to implement a technique only in `optimization.py` when the true blocker is missing data or missing request fields.

## Omission Detection Checklist

If another model needs to verify whether a technique is already implemented, use this checklist.

Mark the technique as fully implemented only if all of the following are true:

1. the solver logic exists in repo code
2. required inputs exist in schema or internal pipeline
3. route orchestration can pass those inputs end-to-end
4. tests assert the behavior
5. README or handoff documentation does not contradict the implementation

If any of those are missing, the technique should still be treated as omitted or only partially implemented.

## What Is Actually Gated By The Remaining Parity Gaps

Not all remaining parity work is equal. Some items are implementation cleanup or calibration work, while others still need richer data contracts or more explicit product semantics.

### Not Gated Or Only Lightly Gated

These can be implemented now with the current repo structure and current data pipeline:

- better continuous-model orchestration
  - blocker type: missing refactor only
  - why not gated: no new data source is needed

### Moderately Gated

These require solver work plus small schema or orchestration changes, but are not blocked by external data acquisition:

- leverage by short-selling
  - blocker type: implemented in solver and schema; remaining work is hardening, calibration, and richer validation if the feature becomes user-facing
- leverage by borrowing cash
  - blocker type: implemented in solver and schema; remaining work is hardening, calibration, and richer validation if the feature becomes user-facing
- turnover limits
  - blocker type: implemented in solver and schema; remaining work is holdings validation and richer rebalance scenarios

### Heavily Gated By Richer Data Or Metadata

These are no longer absent from the repo, but the remaining parity work is still upstream-data-sensitive:

- sector allocation constraints
  - blocker type: richer metadata normalization and ETF handling
  - current gap: sector metadata retrieval exists, but normalization policy and broader taxonomy support are still limited
- factor model objective and constraint variants
  - blocker type: richer factor data source
  - current gap: the repo currently derives a simple market-factor proxy rather than maintaining a reusable exposure matrix, factor covariance, and specific-risk pipeline across broader factor families
- round-lot constraints
  - blocker type: richer lot-size and execution semantics
  - current gap: the current implementation assumes one-share lots by default and does not yet support market-specific lot metadata

### Heavily Gated By Richer Trading Semantics

These have first-pass support, but parity work still spans schema, orchestration, calibration, and solver behavior:

- rebalancing with transaction costs
  - blocker type: richer trade and budget semantics
  - current gap: the repo now models buy/sell variables with proportional costs, but fixed-fee variants, share-level rebalance semantics, and richer broker schedules are still absent
- transaction-cost-aware investing
  - blocker type: calibration depth
  - current gap: the current optimizer supports proportional costs, but not a broader family of per-asset, broker-specific, or fixed-charge models
- market-impact modeling
  - blocker type: model fidelity and calibration
  - current gap: the repo now supports a linear ADV-based penalty path, but not a deeper calibration workflow or richer nonlinear formulations

### Ranking Is Gated By Upstream Outputs

- output-driven ranking
  - blocker type: partially improved and now implemented for current outputs
  - why: ranking now uses realized returns, risk, Sharpe ratio, and frontier context, but it can still be extended further once transaction-cost and factor outputs exist

## Review Findings Incorporated

The current review of `base.md` against the repo code produced these corrections:

- output-driven ranking is implemented and should not be listed as a current omission
- leverage-by-short-selling, leverage-by-borrowing, and turnover-constrained optimization are implemented end-to-end and covered by tests
- `OptimizeRequest` already includes `current_weights`, `max_turnover`, `max_gross_exposure`, `max_short_exposure`, and `max_cash_borrow`
- the real remaining rebalancing gap is transaction-cost-aware rebalancing, not basic turnover-aware rebalancing

## Are The Remaining Gaps Gated?

Not all remaining gaps are ready for direct implementation. Some are still gated by missing information, missing upstream data, or missing product semantics.

### Ready Or Mostly Ready

These are the least gated remaining areas:

- continuous-model cleanup and orchestration cleanup
  - mostly an internal refactor
  - no new external data source is required
- stronger validation around the already-implemented leverage and turnover features
  - request validation, holdings normalization, and calibration can be improved now
  - no new data source is required

### Gated By Missing Information Or Data

These are not ready for clean implementation without defining additional inputs first:

- factor models
  - gated by missing factor exposure matrix, factor covariance, and specific-risk inputs
- sector allocation constraints
  - gated by missing sector metadata retrieval in the provider layer
- round-lot constraints
  - gated by missing lot-size semantics and current-price-to-unit conversion rules

### Gated By Missing Trading Semantics

These are not ready as pure solver tasks because the contract and modeling inputs are still incomplete:

- transaction-cost-aware optimization
  - needs buy/sell variables, cost parameters, and explicit cost semantics
- rebalancing with transaction costs
  - needs a trade model built from current holdings plus a cost-aware budget equation
- market impact
  - needs impact coefficients or a documented proxy model tied to trade size and liquidity

### Practical Answer

The remaining parity gaps are not all the same kind of work.

- ready now: provider cleanup, estimator hardening, richer validation, README/base.md reconciliation, and calibration work around already-implemented advanced models
- still partially gated by richer inputs or semantics: broader factor pipelines, richer sector normalization, fuller lot metadata, deeper transaction-cost schedules, and higher-fidelity market-impact modeling

## Which Gates Can Be Removed By FMP Or FinanceToolkit

Using FMP directly or using FinanceToolkit on top of FMP does remove some of the current gates. It does not remove the need for schema design, orchestration, or mixed-integer solver work.

### Gates Removed By FMP Directly

FMP can remove the upstream data gate for these areas:

- sector and industry metadata
  - FMP exposes company profile, sector, industry, available sectors, available industries, and bulk profile endpoints
  - this removes the data-source gate for sector-allocation constraints once the repo adds metadata retrieval in `app/services/data_service.py`
- latest prices and quote inputs for unit-aware models
  - FMP exposes historical prices, quote endpoints, batch quotes, intraday data, market cap, float, and liquidity-style inputs
  - this removes the absence-of-price-data gate for round-lot logic, turnover calculations, and rebalance accounting
- benchmark and market inputs
  - FMP exposes treasury rates and market risk premium
  - this removes the need to invent risk-free or benchmark assumptions for utility and performance calculations
- ETF composition and sector breakdowns
  - FMP exposes ETF holdings, asset exposure, and ETF sector weightings
  - this can support benchmark decomposition and sector-aware analytics
- liquidity proxies for transaction-aware models
  - FMP exposes volume, float, market cap, and intraday data
  - this removes the complete data absence for first-pass transaction-cost or impact proxies

### Gates Removed By FinanceToolkit

FinanceToolkit removes analytics and calculation gates more than raw-data gates:

- risk analytics
  - VaR, cVaR, drawdown, correlations, and related risk diagnostics do not need to be implemented from scratch
- performance analytics
  - Sharpe, Sortino, Treynor, beta, Jensen's alpha, and related metrics are already available
- benchmark-aware analytics
  - FinanceToolkit can work with benchmark-relative metrics and historical-return analytics directly on top of FMP-backed data
- factor-analysis groundwork
  - FinanceToolkit exposes factor correlations and related performance analytics, which reduces the research gate for factor-model extensions
- portfolio analytics from transaction data
  - the portfolio module can analyze positions and transactions, which reduces the analytics gate for rebalancing workflows

### Important Limitation

FinanceToolkit does not remove the need to define the optimizer's own input structures. It helps with analytics, diagnostics, and some factor-related calculations, but it does not automatically create the exact optimization inputs needed for mixed-integer portfolio construction.

## Removed Versus Remaining Gates

This section is the condensed planning view for another model.

### Gates That Can Be Treated As Removed With FMP And FinanceToolkit

- sector and industry data availability
- latest-price availability for share-aware calculations
- benchmark and risk-free-rate sourcing
- basic liquidity proxies for trade-aware models
- risk and performance metric implementation from scratch
- portfolio analytics support from transaction records

### Gates That Are Reduced But Not Fully Removed

- factor models
  - reduced because FinanceToolkit offers factor-related analytics
  - still remaining because the repo does not yet define a clean exposure matrix, factor covariance, and specific-risk pipeline for optimization
- round-lot models
  - reduced because FMP supplies current prices
  - still remaining because the repo does not yet define lot-size semantics or unit-level optimization inputs
- rebalancing
  - reduced because FinanceToolkit can analyze transaction-based portfolios and FMP can supply current pricing
  - still remaining because the repo lacks an explicit trade-based rebalance formulation with transaction costs, even though `current_weights` and turnover-constrained optimization now exist
- transaction costs and market impact
  - reduced because FMP provides price, volume, float, and liquidity-style inputs
  - still remaining because the optimizer does not yet model buy/sell variables, cost parameters, or impact terms

### Gates That Still Remain Even With FMP And FinanceToolkit

- request and response schema expansion in `app/models/schemas.py`
- route and orchestration changes in `app/main.py`
- provider integration work in `app/services/data_service.py`
- explicit SCIP mixed-integer formulations in `app/services/optimization.py`
- solver-result packaging and ranking updates in `app/services/ranking.py`
- end-to-end tests for any newly exposed feature

Current status note:

- some of the above are already partially addressed in the codebase, but the remaining major gaps are factor-model inputs, sector metadata, round-lot semantics, and transaction-cost/rebalancing calibration

### Practical Interpretation

Using FMP and FinanceToolkit means the next model should not spend time building custom data collectors for sectors, quotes, benchmark rates, or standard risk metrics. The real remaining work shifts to:

- turning available data into repo-specific internal inputs
- expanding the API contract where needed
- implementing the actual optimization formulations
- testing solver behavior and end-to-end routing

## Immediate Versus Blocked Implementation Matrix

Use this quick classification before starting any task:

- implement now:
  - continuous-model cleanup
- implement after small schema additions:
  - richer holdings validation for turnover and rebalancing variants
- do not attempt as solver-only work:
  - sector allocation
  - factor models
  - round lots
  - rebalancing with transaction costs
  - market impact

## Are The Existing Pointers Sufficient To Avoid Gating?

For omission detection and work planning: yes.

For full implementation of every notebook family: not entirely, because some features are genuinely gated by missing data or missing contract surface in the codebase, not by missing documentation pointers.

The pointers currently provided are sufficient for another model to determine:

- whether a feature is missing in repo code
- whether the blocker is solver logic, schema, or data
- which repo files must change first
- which Gurobi notebook page to consult for the intended formulation

The pointers are not intended to fabricate missing business inputs. For example:

- factor models still need a source for factor exposures and specific risk
- sector allocation still needs sector metadata retrieval in the provider layer
- round lots still need lot-size semantics
- transaction-cost-aware rebalancing still needs explicit trade variables and cost semantics beyond the existing `current_weights` input

That means implementation is not gated by lack of discovery pointers, but some techniques remain gated by real upstream omissions in the system design.

## Practical Rule For Another Model

Before implementing any missing technique, first answer these three questions from repo code and the Gurobi notebook page:

1. is the formulation itself missing?
2. are the required inputs already available in `data_service.py` or `schemas.py`?
3. if not, is the correct first task to extend data retrieval, extend request schema, or extend the solver?

If question 2 is answered with no, the implementation is gated upstream and should not start in `optimization.py` alone.

## Gurobi Notebook Coverage Map

This section translates the Gurobi notebook families into concrete implementation work for this repo.

### Data Preparation

Gurobi notebook topic:

- Mean-Variance Data Preparation

What it means for this repo:

- build a stable preprocessing path from FMP prices to aligned returns
- support annualization consistently
- preserve a place to add shrinkage for the first moment and covariance regularization
- eventually support benchmark-aware statistics if needed

Repo implementation targets:

- `app/services/data_service.py`
- `app/services/estimation.py`
- `tests/test_data_service.py`
- `tests/test_estimation.py`

Required inputs:

- historical adjusted close prices by ticker
- trading calendar alignment across assets
- optional benchmark ticker later

### Basic Markowitz Model Family

Gurobi notebook topics:

- Maximizing Return
- Minimizing Variance
- Maximizing Utility

Implementation meaning:

- these are the core continuous models and should be implemented before advanced constraints

Target formulations:

1. Max return under risk cap:

- objective: maximize $\mu^\top x$
- constraints: $x^\top \Sigma x \leq \sigma^2_{max}$, $\sum_i x_i = 1$
- default long-only form: $0 \leq x_i \leq 1$

2. Min variance under return floor:

- objective: minimize $x^\top \Sigma x$
- constraints: $\mu^\top x \geq r_{min}$, $\sum_i x_i = 1$
- default long-only form: $0 \leq x_i \leq 1$

3. Utility maximization:

- objective: maximize $\mu^\top x - \lambda x^\top \Sigma x$
- or equivalent minimization form depending on solver setup
- parameter $\lambda$ is the risk-aversion coefficient

Repo implementation targets:

- `app/services/optimization.py`
- `tests/test_optimization.py`
- optional API exposure through `app/models/schemas.py` and `app/main.py`

### Factor Model Family

Gurobi notebook topics:

- Factor Model as Objective
- Factor Model as Constraint

Implementation meaning:

- support risk represented as factor exposures plus idiosyncratic risk rather than only a dense covariance matrix

Target formulation components:

- exposure matrix $B$
- factor covariance $F$
- specific variance diagonal matrix $D$
- implied covariance $\Sigma = BFB^\top + D$

Two required capabilities:

1. factor model in objective:

- optimize using factor-implied portfolio variance directly in the objective

2. factor model in constraint:

- keep the primary objective on return or utility, but constrain factor-implied variance

Repo implementation targets:

- new factor-model helper module under `app/services/`
- `app/services/optimization.py`
- `tests/test_optimization.py` or a dedicated factor-model test file

Required inputs beyond prices:

- factor exposures per asset
- factor covariance matrix
- specific risk per asset

### Portfolio Constraint Family

Gurobi notebook topics:

- Minimum Buy-In
- Cardinality Constraints
- Enforcing Diversification
- Leverage by Short-Selling
- Leverage by Borrowing Cash
- Limiting Turnover
- Round Lots
- Sector Allocation

Implementation meaning:

- this is where the current repo is furthest from the notebook family
- several of these require mixed-integer modeling and therefore should be SCIP-first

Constraint-by-constraint guidance:

1. Minimum buy-in:

- if position is opened, require $x_i \geq l_i$
- usually modeled with binary variables $b_i$ and linkage like $x_i \leq u_i b_i$, $x_i \geq l_i b_i$

2. Cardinality:

- limit number of open positions, for example $\sum_i b_i \leq K$

3. Diversification:

- enforce upper bounds on positions and optionally minimum number of holdings

4. Leverage by short-selling:

- allow negative positions with explicit gross or short exposure limits
- likely needs separate long and short components if implemented cleanly

5. Leverage by borrowing cash:

- include a cash or risk-free sleeve that can be negative within limits

6. Turnover limits:

- constrain distance from current portfolio, often using auxiliary buy and sell variables

7. Round lots:

- convert position sizing to integer unit or lot variables, not just continuous weights

8. Sector allocation:

- aggregate weights by sector and constrain sector totals
- requires sector metadata from the market-data provider layer

Repo implementation targets:

- `app/models/schemas.py`
- `app/services/optimization.py`
- likely new constraint helper module(s)
- `app/main.py`
- `tests/test_optimization.py`
- `tests/test_api.py`
- `app/services/data_service.py` for metadata support

Required inputs beyond prices:

- current holdings for turnover and rebalancing work
- sector metadata
- per-asset lot sizes or prices for round-lot constraints
- min and max position parameters

### Transaction Cost And Slippage Family

Gurobi notebook topics:

- Investing with Transaction Costs
- Rebalancing with Transaction Costs
- Market Impact Costs

Implementation meaning:

- move from pure allocation optimization to trading-aware optimization

Target modeling components:

1. Fixed and proportional transaction costs:

- model buy and sell decisions separately
- fixed charges usually introduce binaries
- proportional costs are continuous and depend on traded amount

2. Rebalancing with transaction costs:

- start from existing holdings, not all cash
- budget equation must include trading costs

3. Market impact:

- include a slippage penalty or approximation linked to trade size
- exact calibration can remain simple initially; structure matters more than realism in the first pass

Repo implementation targets:

- `app/models/schemas.py`
- `app/services/optimization.py`
- likely dedicated cost or rebalance helper module(s)
- `app/main.py`
- `tests/test_optimization.py`
- `tests/test_api.py`

## Required Data Inventory By Technique

This section defines what data must exist before each notebook family can be implemented.

### Data Needed For Current Base Models

- aligned historical prices
- returns matrix
- expected return vector
- covariance matrix

### Additional Data Needed For Factor Models

- factor exposure matrix
- factor covariance matrix
- specific risk vector

### Additional Data Needed For Sector Constraints

- sector classification per ticker
- optionally industry, sub-industry, or asset type later

### Additional Data Needed For Round Lots

- latest asset price
- lot size or minimum tradable quantity
- investment amount or budget

### Additional Data Needed For Rebalancing And Turnover

- current holdings or current weights
- latest prices
- current portfolio value or share counts

### Additional Data Needed For Transaction Costs

- fixed charge assumptions
- proportional cost rates
- optional market impact parameters

## Source Map For Remaining Gaps

This section identifies, for each remaining notebook family, where the formulation comes from, where the required data would come from in this repo, how that data should be obtained, and which decisions are still unresolved.

### Current Live Data Source In Repo

What exists today:

- historical prices come from Financial Modeling Prep (FMP) in `app/services/data_service.py`
- the FMP API key is retrieved from Azure Key Vault using `DefaultAzureCredential`
- the default vault and secret names are controlled by `AZURE_KEYVAULT_NAME` and `FMP_API_SECRET_NAME`
- raw prices are fetched from FMP `historical-price-full/{ticker}`
- expected returns and covariance are derived locally in `app/services/estimation.py` from the fetched price history
- optional FinanceToolkit diagnostics are computed only when an FMP API key is available

How to obtain it:

1. ensure Azure authentication works for the runtime using `DefaultAzureCredential`
2. store the FMP API key in Azure Key Vault under the configured secret name
3. set `AZURE_KEYVAULT_NAME` and `FMP_API_SECRET_NAME` if the defaults are not correct
4. call the existing market-data path through `get_market_data(...)`

What this means:

- the repo already has a working source for price history
- the repo now has first-class retrieval for sector metadata and average daily dollar volume in `app/services/data_service.py`
- the repo still does not maintain a reusable external factor-data pipeline or richer lot-size metadata beyond the current first-pass assumptions
- broader parity work now centers on turning the available provider data into cleaner internal abstractions and richer calibration inputs

### FMP Endpoint Map For Remaining Provider Work

The current repo uses the legacy FMP v3-style historical endpoint in `app/services/data_service.py`. The current FMP docs expose stable endpoints that should be used as the implementation reference for provider expansion.

Historical prices and volume:

- historical end-of-day price and volume: `https://financialmodelingprep.com/stable/historical-price-eod/full?symbol=AAPL`
- lighter historical chart variant: `https://financialmodelingprep.com/stable/historical-price-eod/light?symbol=AAPL`

Latest prices and live quote fields:

- real-time quote: `https://financialmodelingprep.com/stable/quote?symbol=AAPL`
- short quote: `https://financialmodelingprep.com/stable/quote-short?symbol=AAPL`
- batch quote for multiple symbols: `https://financialmodelingprep.com/stable/batch-quote?symbols=AAPL,MSFT,GOOG`

Sector and company metadata:

- company profile with sector and industry fields: `https://financialmodelingprep.com/stable/profile?symbol=AAPL`
- available sectors list for normalization: `https://financialmodelingprep.com/stable/available-sectors`
- available industries list for normalization: `https://financialmodelingprep.com/stable/available-industries`
- bulk profiles if provider throughput becomes a problem: `https://financialmodelingprep.com/stable/profile-bulk?part=0`

Liquidity and related fields:

- historical price and volume endpoint above is the primary source for computing average daily dollar volume
- real-time quote endpoints also expose volume fields for latest snapshots
- shares float and liquidity metadata: `https://financialmodelingprep.com/stable/shares-float?symbol=AAPL`
- top traded stocks reference endpoint: `https://financialmodelingprep.com/stable/most-actives`

ETF-specific supporting endpoints:

- ETF information: `https://financialmodelingprep.com/stable/etf/info?symbol=SPY`
- ETF sector weightings: `https://financialmodelingprep.com/stable/etf/sector-weightings?symbol=SPY`
- ETF holdings: `https://financialmodelingprep.com/stable/etf/holdings?symbol=SPY`

Implementation note:

- for this repo, sector constraints should use `profile?symbol=` as the first metadata source for operating companies
- average daily dollar volume should be computed from historical end-of-day close and volume, rather than inferred from only quote snapshots
- latest-price support should come from `quote?symbol=` or `batch-quote?symbols=` rather than reusing a historical endpoint for execution-time values

### Factor Models

Formulation source:

- Gurobi factor model notebooks
- portfolio-theory formulation: $\Sigma = BFB^\top + D$

Required data:

- factor exposure matrix per asset
- factor covariance matrix
- specific risk per asset

Likely data source:

- not currently sourced in repo
- possible external sources include FMP fundamentals and statement data, FinanceToolkit-derived factors, or a separate factor dataset/provider

How to obtain it:

1. choose the factor family first: market-only, style factors, or sector plus style factors
2. decide whether exposures are vendor-supplied or estimated in-house from historical data and fundamentals
3. add a provider layer that returns `B`, `F`, and `D` in a stable schema
4. add estimation tests that verify dimensions, symmetry, and positive semidefiniteness where required

Policy chosen:

- first factor family is market-only
- factor exposures should be estimated in-house initially
- use daily inputs with a weekly refresh cadence for the first factor-model implementation

Decisions that still remain:

- none for the initial implementation contract

Implementation status:

- implemented as a first-pass market-factor proxy; remaining work is broader factor-family support and a cleaner reusable factor-data pipeline

### Sector Allocation Constraints

Formulation source:

- Gurobi sector allocation notebook patterns
- linear aggregation constraints of the form $\sum_{i \in s} x_i \leq u_s$

Required data:

- sector classification per ticker
- optionally industry and sub-industry later

Likely data source:

- FMP company profile or similar metadata endpoint

How to obtain it:

1. extend `app/services/data_service.py` with a metadata fetch path for ticker classifications
2. normalize provider sector labels into a stable internal vocabulary
3. cache the metadata alongside price retrieval or in a separate provider helper
4. expose sector-bound inputs in `app/models/schemas.py`

Policy chosen:

- first version supports sector-level constraints only
- ETFs should be excluded from sector-constrained runs

Decisions that still remain:

- none for the initial implementation contract

Implementation status:

- implemented in a first-pass form using FMP profile sector data; remaining work is broader normalization, ETF treatment, and richer taxonomy support

### Cardinality And Minimum Buy-In

Formulation source:

- Gurobi minimum buy-in and cardinality notebooks
- mixed-integer formulations using binary open-position variables

Required data:

- minimum and maximum position thresholds
- optional per-asset buy-in thresholds if not global

Likely data source:

- mostly request-schema inputs rather than vendor data
- current prices may also be needed if thresholds are defined in dollars rather than weights

How to obtain it:

1. add request fields for max positions, minimum position size, and optional per-asset overrides
2. if thresholds are dollar-based, reuse latest-price retrieval from the provider layer
3. implement SCIP-first binary formulations in `app/services/optimization.py`

Policy chosen:

- thresholds should be expressed in portfolio weights first
- minimum buy-in applies to newly opened positions only
- if SCIP is unavailable for a mixed-integer request, the API should reject the request rather than silently relax it

Decisions that still remain:

- none for the initial implementation contract

Implementation status:

- implemented in a first-pass form with schema support, SCIP-first wiring, and focused tests; remaining work is richer per-asset threshold semantics if needed

### Round Lots

Formulation source:

- Gurobi round-lot notebook patterns using integer quantity variables

Required data:

- latest price per asset
- lot size or minimum tradable unit per asset
- portfolio budget or target capital

Likely data source:

- latest price can come from FMP
- lot size may need a repo-managed assumption layer because standard equities often trade in single shares while some markets/products have different lot semantics

How to obtain it:

1. add a latest-price retrieval path if the existing historical fetch is not sufficient for execution-time sizing
2. define where lot-size metadata lives: static config, provider metadata, or request input
3. extend response models to return share or lot counts in addition to weights if integer trading is requested

Policy chosen:

- U.S. equities default to one-share lots in the first version
- round-lot models should solve directly in integer units or lots, not through a weight-optimization step followed by a rounding post-pass

Decisions that still remain:

- none for the initial implementation contract

Implementation status:

- implemented in a first-pass form using latest prices and a one-share default lot assumption; remaining work is richer lot metadata and share-level response semantics if the API needs to expose them more explicitly

### Transaction-Cost-Aware Rebalancing

Formulation source:

- Gurobi transaction-cost and rebalancing notebooks
- buy/sell decomposition with budget adjustments for costs

Required data:

- current holdings or current weights
- latest prices
- transaction cost model parameters: fixed charges, proportional fees, spreads

Likely data source:

- current holdings already have a partial path via `current_weights` in the request schema
- latest prices can come from FMP
- transaction cost parameters are not available from the current provider layer and will likely start as request inputs or config defaults

How to obtain it:

1. keep using or extend `current_weights` for rebalance starting state
2. add latest-price retrieval if the formulation moves from weight-only to trade-size-aware execution
3. add explicit transaction-cost fields to `app/models/schemas.py`
4. model buy and sell variables separately in `app/services/optimization.py`

Policy chosen:

- first version uses a global proportional fee only
- fixed per-trade fees are deferred from the first version
- turnover-constrained and transaction-cost-aware rebalancing should remain separate model families

Decisions that still remain:

- none for the initial implementation contract

Implementation status:

- implemented in a richer first-pass form with calibrated Interactive Brokers-style defaults, explicit buy/sell variables, per-asset transaction-cost overrides, and request-level market-impact controls; remaining work is fixed-fee and more nonlinear execution models

### Market Impact

Formulation source:

- Gurobi market impact notebook patterns
- usually a penalty or constraint tied to trade size relative to liquidity

Required data:

- trade size
- recent volume or liquidity proxy
- impact coefficients or calibration assumptions

Likely data source:

- recent price and volume may be obtainable from FMP
- impact coefficients are not available in repo and likely need to be policy-driven assumptions or research inputs

How to obtain it:

1. extend provider retrieval to include recent volume or dollar-volume metrics
2. choose a simple first-pass impact model, such as linear or square-root penalty
3. expose calibration parameters in config or request schema
4. add tests that verify larger trades are penalized more heavily than smaller trades

Policy chosen:

- first version uses a linear market-impact penalty
- market impact is meant to approximate execution cost first
- liquidity should be normalized using average daily dollar volume

Decisions that still remain:

- none for the initial implementation contract

Implementation status:

- implemented in a calibrated first-pass form through an ADV-based linear penalty path, a request-level ADV floor, and optional per-asset impact overrides; remaining work is deeper nonlinear calibration and richer impact formulations

### Summary Of What Is Data-Sourced Versus Decision-Gated

Data source already live in repo:

- historical price history from FMP
- locally estimated returns and covariance
- optional FinanceToolkit risk diagnostics
- sector metadata from FMP company profiles
- average daily dollar volume derived from FMP historical price and volume data

Can likely be obtained with moderate provider extension:

- latest prices from existing or adjacent FMP endpoints
- richer lot-size metadata and broader execution-oriented provider inputs

Still requires product or quant decisions before coding:

- none for the initial implementation contract

## Resolved Policy Decisions

The following implementation policies are now fixed unless explicitly changed later.

### Factor Models

- start with a market-only factor model
- estimate exposures in-house rather than relying on a vendor-supplied factor feed
- use daily inputs with a weekly refresh cadence for the first factor-model implementation

Why this is important:

- market-only is the narrowest factor model that still changes the risk model architecture, so it lets the repo add factor infrastructure without first committing to a full style-factor research program
- estimating exposures in-house keeps the first implementation independent of a specialized vendor feed and avoids binding the API contract to an external factor taxonomy too early

Implications if changed later:

- moving from market-only to style or multi-factor models will expand the data contract from one exposure vector to a full exposure matrix and will likely require changes in estimation helpers, validation, and tests
- switching from in-house estimation to vendor-supplied exposures would change the provider layer and may change output comparability if the vendor uses a different factor definition or refresh cadence
- moving from weekly refresh to monthly refresh would reduce churn but make the factor model slower to react; moving to daily refresh would increase responsiveness at the cost of noisier estimates and more frequent cache invalidation

### Sector Constraints

- support sector-level constraints first
- exclude ETFs from sector-constrained runs
- if a ticker has missing or unstable sector metadata, exclude that ticker from the sector-constrained run rather than rejecting the entire request

Why this is important:

- sector-level bounds are easier to explain and validate than industry-level bounds, and they match the first likely user need: cap broad concentration risk
- excluding ETFs avoids false precision because many ETFs do not map cleanly into a single operating sector

Implications if changed later:

- adding industry-level constraints later will require more detailed metadata normalization and more edge-case handling for inconsistent provider labels
- allowing ETFs into sector-constrained runs will require an explicit classification rule, such as provider label, look-through holdings, or uncategorized treatment, and each choice changes feasibility and exposure totals
- changing from asset exclusion to hard rejection would improve strictness but make sector-constrained runs fail more often because of provider metadata gaps; changing to an uncategorized bucket would preserve more assets but require additional constraint semantics

### Cardinality And Minimum Buy-In

- express thresholds in portfolio weights first
- apply minimum buy-in only to newly opened positions
- reject mixed-integer requests when SCIP is unavailable rather than relaxing them silently

Why this is important:

- weights keep the API aligned with the rest of the current optimizer, which already operates primarily in allocation space rather than dollars or shares
- applying buy-in only to newly opened positions avoids forcing legacy holdings to be liquidated just because they fall below the buy-in threshold
- rejecting requests when SCIP is unavailable prevents the API from returning a materially different optimization problem than the caller requested

Implications if changed later:

- changing thresholds from weights to dollars or shares would require latest-price support, new request fields, and revised validation rules
- applying buy-in to all non-zero positions would materially change rebalance behavior and could force additional turnover
- allowing relaxed fallbacks would require response metadata that clearly tells the caller a different problem was solved

### Round Lots

- default U.S. equities to one-share lots in the first version
- do not allow fractional trading in the first version
- solve round-lot portfolios directly in integer units or lots, not by optimizing continuous weights and rounding afterward

Why this is important:

- one-share lots are the least opinionated default for U.S. equities and avoid inventing a special lot schedule where one may not exist
- this keeps the first integer-trading model simple enough to validate against continuous-weight outputs
- solving directly in integer units preserves the integrity of the optimization problem, so the returned portfolio is actually feasible under the lot constraints rather than only approximately feasible after rounding

Implications if changed later:

- introducing market-specific lot sizes will require per-asset metadata and may reduce feasibility for small portfolios
- allowing fractional shares would weaken or remove the need for some integer constraints and may change whether round-lot optimization should exist as a distinct model family
- switching to a rounding post-pass later would simplify implementation but could create portfolios that violate budget, diversification, or cardinality intent after rounding and would weaken testability against the exact solver formulation

### Transaction Costs

- first version uses a global proportional fee only
- do not include fixed per-trade fees in the first version
- keep turnover-constrained and transaction-cost-aware rebalancing as separate model families
- use repo defaults first for transaction-cost and market-impact calibration, with user review and later override support if needed
- anchor transaction-cost defaults to Interactive Brokers pricing rather than an arbitrary internal fee assumption
- use Interactive Brokers Fixed pricing for the U.S. equity market as the v1 broker baseline
- simplify the IBKR U.S. Fixed schedule into a default one-way effective trading-cost rate of 10 bps for optimization purposes

Why this is important:

- a single proportional fee is the simplest cost model that still changes portfolio selection behavior in a meaningful way
- omitting fixed fees keeps the first version continuous or near-continuous where possible instead of immediately forcing additional binary complexity
- keeping turnover and transaction-cost models separate makes it easier to compare their behavior and test them independently
- using Interactive Brokers as the baseline ties transaction-cost assumptions to a real broker schedule instead of an invented placeholder
- using a 10 bps one-way default keeps the model in a range that still allows a growth-oriented portfolio to trade when expected upside is meaningful, while remaining conservative enough to avoid free-trading assumptions

Implications if changed later:

- adding per-asset or broker-specific costs will expand the request contract and complicate calibration and testing
- adding fixed fees will push the model further into mixed-integer territory and may increase solve time materially
- merging turnover and transaction-cost rebalancing into one configurable family would reduce API surface area but increase model branching and validation complexity
- moving from repo defaults to required per-request inputs would give callers more control but increase schema complexity and usage friction; moving to defaults plus optional overrides would be a reasonable second step once calibration stabilizes
- changing away from an IBKR baseline later would change backtest comparability and may require revisiting default cost levels across markets and account types
- changing the default rate materially above 10 bps will make the optimizer trade less and prefer lower-turnover portfolios; changing it materially below 10 bps will make the optimizer more willing to chase forecast return at the cost of more turnover

Why these additional decisions are important:

- weekly factor refresh is a middle ground: it avoids daily churn in factor estimates while staying more responsive than monthly recomputation
- excluding only assets with missing sector metadata keeps sector-constrained runs usable without pretending the missing classification is reliable
- disallowing fractional trading preserves the meaning of round-lot and integer-trading models instead of collapsing them back toward continuous allocation
- repo-default calibration keeps the first implementation deterministic and avoids forcing callers to invent transaction-cost and impact numbers before the product has validated defaults

### Market Impact

- first version uses a linear penalty
- treat market impact primarily as an execution-cost approximation
- use average daily dollar volume as the first liquidity proxy
- calibrate the v1 market-impact model for a growth investor: a trade equal to 10% of average daily dollar volume should add roughly 25 bps of impact cost
- implement that as a linear coefficient of 0.025 in the penalty term when impact is modeled as `coefficient * (trade_notional / ADV)`
- use a default ADV floor of $5,000,000 when computing impact so very low-liquidity names do not create unstable penalties from noisy data

Why this is important:

- a linear penalty is easier to reason about, calibrate, and debug than more nonlinear impact functions
- treating impact as execution cost keeps the first objective economically interpretable instead of mixing cost and abstract liquidity-risk controls
- average daily dollar volume is a more practical scaling measure than share volume when assets have very different prices
- calibrating to 25 bps at 10% ADV is growth-oriented rather than defensive: it still discourages oversized trades in thin names, but it does not suppress moderate trading in liquid growth names

Implications if changed later:

- switching to a square-root or other nonlinear impact model may require different solver treatment, different calibration data, and different user expectations around sensitivity
- treating impact as a risk-control constraint instead of a cost term would change both the formulation and how results are explained to users
- changing the liquidity proxy would alter calibration values and may make historical comparisons between runs inconsistent
- increasing the impact coefficient above this default will bias the optimizer more strongly toward mega-cap liquidity and lower turnover; decreasing it will make the optimizer more willing to trade smaller or less liquid names
- raising the ADV floor will make the model more forgiving to thinly traded names; lowering it will make the penalty more sensitive to small-cap liquidity conditions

### Calibration Defaults For Initial Implementation

These defaults are intended to remove gating for implementation. They are not meant to be a final execution model.

Transaction-cost default:

- broker baseline: Interactive Brokers Fixed, U.S. equities
- optimizer default: 10 bps one-way effective trading cost
- interpretation: a growth-oriented but still realistic default that allows trading when conviction is strong

Market-impact defaults:

- penalty form: linear in trade notional divided by average daily dollar volume
- coefficient: `0.025`
- interpretation: approximately 25 bps impact at 10% ADV, 12.5 bps at 5% ADV, and 50 bps at 20% ADV
- ADV floor: `$5,000,000`

Why these defaults fit a growth investor:

- they allow meaningful rebalancing when expected return improves, instead of locking the optimizer into ultra-low-turnover behavior
- they still penalize aggressive trading into thin liquidity, so the model does not behave like execution is frictionless
- they should favor liquid growth names without forcing the solution entirely into the largest-cap names

## Solver Guidance

This section should be used as an implementation rulebook.

### Continuous Problems

These can support SCIP and SciPy paths:

- max return under variance cap
- min variance under return floor
- utility maximization
- efficient frontier point generation
- risk parity if kept as a separate nonlinear routine

### Mixed-Integer Problems

These should be treated as SCIP-first or SCIP-only:

- minimum buy-in
- cardinality
- round lots
- fixed transaction costs
- any formulation that uses open-position binaries

### Validation Rule

If a user requests a mixed-integer technique and only a SciPy path is available, do not silently relax it unless the API and response clearly say that a relaxed approximation was solved.

## Acceptance Criteria By Notebook Family

These criteria are stricter than the high-level milestones and are intended to tell the next model when an implementation is actually complete.

### Basic Markowitz Family Complete When

- all three formulations exist: max return, min variance, max utility
- all satisfy full-investment and bound constraints
- utility model exposes risk aversion explicitly
- tests confirm feasibility and reasonable monotonic behavior

Current repo status:

- this family is implemented and covered by unit tests, including efficient frontier generation

### Factor Model Family Complete When

- factor-implied covariance can be computed from fixtures
- optimizer can use factor risk either in objective or in a variance constraint
- tests compare factor and dense behavior on controlled inputs

### Portfolio Constraints Family Complete When

- schema can express the new constraint
- solver enforces it
- error path exists for unsupported relaxed solver combinations
- tests verify the constraint materially changes the feasible set

Current repo status:

- leverage-by-short-selling, leverage-by-borrowing, and turnover-constrained optimization are implemented and covered by tests

### Transaction Cost Family Complete When

- trade variables are modeled explicitly
- rebalancing starts from existing positions
- budget equation includes costs
- tests show differing outcomes with and without costs

## Practical Next Steps For GPT-5.4 Mini

If another model is given only this file, the correct next implementation sequence is:

1. deepen factor-model support beyond the current explicit-contract and market-factor proxy paths into a cleaner reusable factor-data pipeline
2. broaden sector and metadata normalization, especially ETF treatment and richer taxonomy handling
3. harden round-lot semantics beyond request-driven lot sizes toward richer market-specific metadata
4. extend transaction-cost and market-impact modeling beyond the current broker-calibrated linear defaults toward fixed-fee and higher-fidelity formulations
5. keep documentation aligned with the implemented model surface as parity work lands

That sequence reflects the current state of the repo: first-pass advanced model families already exist, so the remaining work is cleanup, calibration, richer data contracts, and documentation alignment.

## Priority Order

Implement in this order unless the user changes priorities:

1. Richer factor-model support
2. Portfolio-constraint hardening and richer metadata semantics
3. Transaction-cost and market-impact calibration depth
4. Ranking cleanup for richer output families
5. API refinement only where new parity work truly requires it
6. Documentation alignment as parity work lands

## Priority 1: Provider Abstraction And Data Pipeline Cleanup

Status update:

- completed in a first-pass form through a lightweight FMP provider wrapper, shared price-alignment logic, and deterministic tests for metadata, liquidity, differing dates, and sparse ticker series
- remaining work in this area is broader provider expansion, not the initial abstraction

### Why This Comes First

The repo already talks to FMP through a lightweight provider wrapper. Future sector constraints, benchmark-aware estimation, and metadata-driven rules still need broader provider expansion, but the initial boundary is now in place.

### Primary Files To Edit

- `app/services/data_service.py`
- optionally add a new provider module under `app/services/` if needed
- `tests/test_data_service.py`
- `README.md`

### Desired End State

Refactor the current direct FMP flow into a cleaner provider-oriented structure while preserving behavior.

At minimum, separate these concerns:

- API key retrieval
- raw provider fetches
- price alignment and cleaning
- metadata retrieval
- estimation input assembly

### Suggested Implementation Shape

One acceptable approach is:

- keep `get_market_data()` as the public entrypoint
- add provider-specific helper functions or a lightweight provider class
- add metadata fetch support for fields such as sector, industry, asset name, and asset type when FMP exposes them
- return a richer internal object or tuple that can later support constraints and ranking without another fetch layer rewrite

### Acceptance Criteria

- Existing `get_market_data()` behavior still works.
- Missing-key loud failure still works.
- Non-auth FMP failure fallback behavior still works unless the user explicitly asks to remove it.
- Metadata can be fetched or at least a clear scaffold exists for it.
- Tests remain deterministic.

### Tests To Add Or Update

- add mocked tests for metadata retrieval
- add tests for cleaning and alignment when dates differ across tickers
- add tests for missing or sparse ticker series
- preserve current missing-key and fallback tests

## Priority 2: Estimation Pipeline Hardening

### Why This Comes Second

The current estimator computes sample mean and sample covariance only. That is adequate for a first pass, but too narrow for robust portfolio construction.

### Primary Files To Edit

- `app/services/estimation.py`
- `app/services/data_service.py`
- `app/models/schemas.py` if estimator settings are exposed through the API
- `tests/test_estimation.py`
- `tests/test_api.py` if request schema changes

### Current State

`estimate_market_inputs(prices_df, api_key=None)` currently returns:

- `returns_df`
- `mu`
- `sigma_matrix`
- `toolkit_risk_metrics`

The function also ensures covariance is positive definite.

### Desired End State

Support explicit estimator options while keeping the current sample estimator as the default.

Target estimation options:

- return estimation:
  - sample mean
  - optional shrinkage or more robust estimator later
- covariance estimation:
  - sample covariance
  - optional shrinkage or regularized covariance later
- optional benchmark statistics if needed later for relative metrics

### Acceptance Criteria

- current sample-based path remains the default and stays stable
- output shapes remain correct
- covariance stays positive definite or near-positive-definite after conditioning
- invalid short-history inputs fail clearly
- if API exposure is added, defaults remain backward compatible

### Tests To Add Or Update

- fixed-fixture tests for return calculations
- tests for too-short history
- tests for singular covariance or near-collinear assets
- tests for any new estimator selection config

## Priority 3: Base Markowitz Parity And Efficient Frontier

### Why This Comes Third

The optimizer currently has working point-in-time models, but it does not yet expose the broader family of Markowitz-style formulations cleanly.

### Primary Files To Edit

- `app/services/optimization.py`
- `tests/test_optimization.py`
- possibly `app/main.py` and `app/models/schemas.py` if frontier output is exposed through the API
- `README.md`

### Current State

Existing optimization functions:

- `minimum_variance`
- `maximum_return`
- `max_sharpe_ratio`
- `mean_variance`
- `equal_weight`
- `risk_parity`
- `run_all_models`

These functions return dictionaries containing weights and summary metrics.

### Desired End State

Add structure, not complexity.

Recommended improvements:

- separate model construction from orchestration where practical
- add explicit utility-maximization model with a risk-aversion parameter
- add efficient-frontier generation
- standardize fallback behavior between SCIP and SciPy for continuous models
- keep mixed-integer needs reserved for SCIP-only future work

### Acceptance Criteria

- existing models still work
- frontier output is monotonic in a reasonable test fixture
- solver fallback behavior is explicit and testable
- result objects remain easy to rank and serialize

### Tests To Add Or Update

- monotonic frontier tests on a deterministic small covariance fixture
- utility-maximization tests
- SCIP vs SciPy similarity tests for continuous formulations
- fallback-path tests when SCIP is unavailable or errors

## Priority 4: Factor Model Support

### Primary Files To Edit

- likely add one or more new modules under `app/services/`
- `app/services/optimization.py`
- `app/models/schemas.py` if API exposure is added
- `tests/test_optimization.py` or new factor-model tests

### Target Capability

Support optimization using factor structure rather than only a dense covariance matrix.

At minimum, support internal data structures for:

- factor exposure matrix
- factor covariance matrix
- specific risk vector

### Acceptance Criteria

- factor-implied risk can be computed correctly
- dense and factor representations can be compared on small fixtures
- dimension mismatch errors are explicit

## Priority 5: Portfolio Constraint Families

### Why This Is Important

A large portion of the Gurobi notebook value is in realistic portfolio-construction constraints, not just base Markowitz math.

### Primary Files To Edit

- `app/models/schemas.py`
- `app/services/optimization.py`
- possibly new constraint helper module(s)
- `app/main.py`
- `tests/test_optimization.py`
- `tests/test_api.py`

### Constraint Families To Add

- position lower and upper bounds
- sector allocation limits
- cardinality or maximum holdings count
- minimum buy-in
- round lots
- leverage or explicit cash sleeve
- short-selling permissions or bounds

### Important Design Rule

Do not silently pretend SciPy supports mixed-integer formulations. If a requested constraint requires SCIP, either:

- run a SCIP path, or
- return a clear validation or unsupported-feature error

### Acceptance Criteria

- request schema can express the constraint
- optimization layer enforces it
- unsupported solver/constraint combinations fail clearly
- sector constraints can use provider metadata when available

## Priority 6: Rebalancing And Transaction Costs

### Primary Files To Edit

- `app/models/schemas.py`
- `app/services/optimization.py`
- likely one or more helper modules for holdings or cost math
- `app/main.py`
- `tests/test_optimization.py`
- `tests/test_api.py`

### Target Capability

Support optimization from current holdings instead of assuming an all-cash start.

Needed inputs eventually include:

- current holdings or current weights
- turnover limits
- transaction fee assumptions
- fixed and proportional cost terms

### Acceptance Criteria

- turnover is computed correctly
- rebalance constraints affect the solution as expected
- infeasible rebalance requests fail clearly
- response payload can explain turnover and estimated costs

## Priority 7: Ranking Cleanup

### Why This Matters

`app/services/ranking.py` currently uses static tables keyed by risk tolerance and horizon. That is useful as a placeholder, but not a strong final design.

### Primary Files To Edit

- `app/services/ranking.py`
- `tests/test_api.py`
- possibly add direct ranking tests

### Desired End State

Use actual optimizer outputs in ranking, for example:

- expected return
- risk
- Sharpe ratio
- feasibility
- constraint satisfaction
- turnover or cost penalties later

Risk tolerance and horizon should remain preference weights, not hard-coded total order tables.

### Acceptance Criteria

- feasible solutions rank above degraded or fallback ones
- explanation text reflects real outputs
- ranking logic is deterministic under fixed fixtures

## Priority 8: API And Documentation Alignment

### Primary Files To Edit

- `app/models/schemas.py`
- `app/main.py`
- `README.md`
- tests for any changed contracts

### Desired End State

When new capabilities are added, expose them cleanly through Pydantic models instead of ad hoc dictionaries.

Likely future request fields:

- estimator settings
- solver preference
- portfolio constraints
- holdings
- turnover and transaction-cost controls

Likely future response fields:

- solver used
- optimization status
- diagnostics
- feasibility warnings
- turnover and estimated costs where relevant

## Testing Strategy

The next model should preserve the current testing discipline:

### Unit Tests

- use fixed fixtures
- mock FMP responses
- mock Key Vault interactions
- test math components independently from solver integration when possible

### Integration Tests

- keep API tests deterministic
- validate the chain from request validation through ranking
- do not depend on live Azure or live FMP

### Solver Tests

- compare SCIP and SciPy on continuous formulations using tolerances, not exact equality
- treat mixed-integer formulations as SCIP-only

### Regression Focus

Protect against silent regressions in:

- annualization
- covariance scaling
- ranking behavior
- missing-key failure behavior
- solver fallback behavior

## Explicit Near-Term Milestone

The best next milestone after this handoff is:

1. refactor the FMP flow into a cleaner provider/data-pipeline boundary
2. harden the estimator layer with clearer configuration and validation
3. add efficient-frontier support and at least one additional Markowitz variant
4. keep all tests passing with focused mocked coverage

That milestone is large enough to move the repo materially forward, but still small enough to complete without redesigning the entire service.

## File-Level Notes For The Next Model

### `app/services/data_service.py`

- keep `get_market_data()` as the stable entrypoint unless the user asks for a contract change
- preserve `MissingFMPAPIKeyError`
- preserve Key Vault lookup via `DefaultAzureCredential`
- if refactoring, avoid breaking the existing tuple return contract until API/schema changes are intentionally made

### `app/services/estimation.py`

- keep the current sample estimator path working
- do not add a local-history FinanceToolkit constructor path
- FinanceToolkit metrics should remain optional diagnostics, not a hard dependency for optimization success

### `app/services/optimization.py`

- prefer extracting helpers over large rewrites
- preserve current result-dictionary shape unless a deliberate schema update is made across the stack

### `app/services/ranking.py`

- current logic is placeholder logic
- if ranking is upgraded, base it on optimizer outputs and retain deterministic explanation strings

### `app/models/schemas.py`

- expand only when the implementation behind the new fields exists
- keep backward compatibility where possible

### `app/main.py`

- keep error handling explicit
- when new options are added, normalize and validate them in schema models first, not inline in the route handler

## Definition Of Done For Any New Change

A change should not be considered complete unless all of the following are true:

1. the narrowest relevant tests were updated or added
2. focused pytest targets pass locally
3. README and API docs are updated if user-visible behavior changed
4. the change preserves the FMP and Key Vault invariants listed above
5. the implementation remains small and understandable

## What Not To Spend Time On Yet

Avoid these unless the user explicitly asks for them:

- live end-to-end tests against FMP Ultimate
- production deployment work
- Azure infrastructure changes beyond the existing Key Vault secret usage
- large architectural rewrites
- full market-impact calibration

## Minimal Execution Loop For The Next Model

For each milestone:

1. inspect the target files listed above
2. make the smallest coherent code change
3. add or update focused tests
4. run the narrowest relevant `uv run pytest ...` command first
5. only then run broader repo tests if needed

This repository is small. Prefer precise incremental progress over broad speculative scaffolding.
