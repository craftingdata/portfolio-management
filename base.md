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

- `data_service.py` currently mixes provider concerns, cleaning, and estimation orchestration in one file.
- `optimization.py` currently exposes one function per strategy plus `run_all_models()`. It now includes utility, leverage, and turnover-aware models, but it is still not split into model-builder abstractions.
- `ranking.py` now blends heuristic tables with realized optimizer output quality and frontier context.
- The API request model now exposes leverage and turnover controls plus current weights, but it still does not expose estimator selection, factor data, sector metadata, or transaction-cost inputs.
- Synthetic fallback still exists in `data_service.py`; it should be treated as test/degradation behavior, not as a preferred production path.
- FinanceToolkit diagnostics are best-effort. The optimizer should not depend on FinanceToolkit outputs to function.

## Verified Test Command

The focused command that already passes after the latest changes is:

```bash
uv run pytest tests -q
```

Most recent verified result before this handoff: `34 passed`.

General repo test command:

```bash
uv run pytest tests -q
```

## Gaps Versus the Broader Gurobi Notebook Family

The repo is still missing major categories that appear in the Gurobi finance notebook collection:

- factor model formulations
- sector and metadata-aware constraints
- cardinality and minimum-buy constraints
- round-lot constraints
- transaction-cost-aware optimization
- market-impact approximations
- portfolio rebalancing with transaction costs

## Coverage Verification

The previous version of this handoff was enough for planning and sequencing, but not fully enough for direct implementation against the Gurobi notebook family.

What was missing before this update:

- explicit mapping from Gurobi notebook topics to repo tasks
- mathematical formulation guidance per notebook family
- required input data beyond prices and covariance
- clear indication of which techniques are continuous versus mixed-integer

After the additions below, `base.md` should be sufficient for another model to implement the techniques incrementally without first re-reading the Gurobi notebook index.

Current coverage is better than the previous version of this handoff: the repo now has direct implementations and tests for the basic Markowitz family, efficient frontier generation, leverage variants, turnover-constrained rebalancing, and output-aware ranking.

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

Current notable omissions, based on repo code, are:

- factor-risk formulations
- discrete constraint families
- cost-aware optimization
- market-impact modeling
- metadata-driven sector constraints
- output-driven ranking

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

## What Is Actually Gated By The Current Omissions

Not all omissions are equal. Some features can be implemented immediately in solver code, while others are gated by missing inputs, missing metadata, or missing API contract surface.

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

### Heavily Gated By Missing Data Or Metadata

These should not be treated as pure `optimization.py` tasks because the real blocker is upstream input availability:

- sector allocation constraints
  - blocker type: missing market-data metadata support
  - current gap: `app/services/data_service.py` fetches prices only and does not fetch sector metadata
- factor model objective and constraint variants
  - blocker type: missing factor data source
  - current gap: the repo does not currently source factor exposures, factor covariance, or specific risk inputs
- round-lot constraints
  - blocker type: missing lot-size and pricing semantics
  - current gap: current pipeline is weight-based and request schema does not expose lot-size or unit-level trading inputs

### Heavily Gated By Both Data And Contract Surface

These require a broader addition across schema, orchestration, and solver layers:

- rebalancing with transaction costs
  - blocker type: missing holdings inputs, missing trade variables, missing cost parameters
  - current gap: no current-holdings fields in `OptimizeRequest`; no rebalance path in the optimizer
- transaction-cost-aware investing
  - blocker type: missing cost parameters plus missing trade formulation
  - current gap: current optimizer allocates end-state weights only; it does not model buys and sells explicitly
- market-impact modeling
  - blocker type: missing trade-size modeling plus missing impact parameters
  - current gap: no transaction-level decision variables or impact coefficients exist in the request model or optimizer

### Ranking Is Gated By Upstream Outputs

- output-driven ranking
  - blocker type: partially improved and now implemented for current outputs
  - why: ranking now uses realized returns, risk, Sharpe ratio, and frontier context, but it can still be extended further once transaction-cost and factor outputs exist

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
  - still remaining because the API schema has no holdings inputs and the optimizer has no rebalance path
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
- rebalancing still needs holdings inputs added to the request model

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

1. refactor `app/services/data_service.py` into cleaner provider, cleaning, and metadata helpers without breaking `get_market_data()`
2. extend `app/services/estimation.py` with explicit estimator configuration while preserving current defaults
3. add factor-model support with explicit factor exposures, factor covariance, and specific risk
4. add sector metadata retrieval and sector-allocation constraints
5. add transaction-cost and rebalancing formulations with explicit trade variables

That sequence aligns directly to the Gurobi notebook progression: data prep first, basic Markowitz second, then richer formulations and constraints.

## Priority Order

Implement in this order unless the user changes priorities:

1. Provider abstraction and data pipeline cleanup
2. Estimation pipeline hardening
3. Base Markowitz parity already implemented; keep extending validation and documentation as needed
4. Factor model support
5. Portfolio constraint families
6. Rebalancing and transaction costs
7. Ranking cleanup
8. API expansion and documentation alignment

## Priority 1: Provider Abstraction And Data Pipeline Cleanup

### Why This Comes First

The repo already talks to FMP, but the provider logic is not yet abstracted. Future sector constraints, benchmark-aware estimation, and metadata-driven rules need a cleaner provider boundary.

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
