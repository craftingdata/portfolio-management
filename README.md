# Portfolio Management API

A Python portfolio optimization service built with [FastAPI](https://fastapi.tiangolo.com/), [PySCIPOpt](https://github.com/scipopt/PySCIPOpt), SciPy, and Financial Modeling Prep data sourced through Azure Key Vault-backed credentials. Given a total investment amount, risk tolerance, and investment horizon, the API runs a family of portfolio constructors and returns the results ranked by applicability.

The repository now covers the core Markowitz family plus a first-pass set of richer Gurobi-inspired portfolio construction models.

## Current Model Surface

The API currently exposes 16 model families through `GET /models` and returns the active set from `POST /optimize`.

### Core Continuous Models

| Model                 | Description                                                                                    |
| --------------------- | ---------------------------------------------------------------------------------------------- |
| `MinimumVariance`     | Minimize portfolio variance subject to full investment and long-only bounds.                   |
| `MaximumReturn`       | Maximize expected return under a risk budget.                                                  |
| `UtilityMaximization` | Maximize expected utility with explicit risk aversion.                                         |
| `MaxSharpeRatio`      | Maximize risk-adjusted return using a tangency-style search and SciPy refinement.              |
| `MeanVariance`        | Classic Markowitz mean-variance optimization with a target return derived from risk tolerance. |
| `EqualWeight`         | Equal allocation baseline.                                                                     |
| `RiskParity`          | Equalize risk contributions across assets.                                                     |

### Leverage And Rebalancing Models

| Model                        | Description                                                                                                    |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `LeverageShortSelling`       | Long-short utility optimization with gross leverage and short exposure limits.                                 |
| `LeverageBorrowing`          | Utility optimization with an explicit cash sleeve and borrowing allowance.                                     |
| `TurnoverConstrained`        | Mean-variance rebalancing with explicit turnover limits from current weights.                                  |
| `TransactionCostRebalancing` | Rebalancing model with explicit buy/sell variables, proportional trading costs, and optional flat ticket fees. |

### Advanced First-Pass Models

| Model                       | Description                                                                                                               |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `FactorUtilityMaximization` | Utility maximization using either an explicit factor contract or an inferred multi-factor covariance model.               |
| `FactorVarianceConstraint`  | Mean-variance optimization using either an explicit factor contract or an inferred multi-factor covariance model.         |
| `SectorAllocation`          | Mean-variance optimization with sector concentration caps on non-ETF assets with stable sector metadata.                  |
| `CardinalityMinBuyIn`       | Mean-variance optimization with a maximum holdings count and minimum buy-in weights.                                      |
| `RoundLotAllocation`        | Integer lot-based allocation using latest prices, configurable lot sizes, optional lot-unit bounds, and a cash remainder. |

## API

### Endpoints

| Method | Path        | Description                                              |
| ------ | ----------- | -------------------------------------------------------- |
| `GET`  | `/health`   | Health check                                             |
| `GET`  | `/models`   | List available optimization models                       |
| `POST` | `/optimize` | Run the model family and return ranked portfolio results |

### Request: `POST /optimize`

Example request:

```json
{
  "total_amount": 100000,
  "risk_tolerance": "medium",
  "investment_horizon": "long",
  "tickers": ["AAPL", "MSFT", "GOOGL", "SPY", "IEF"],
  "risk_free_rate": 0.04,
  "return_estimator": "shrunk_mean",
  "covariance_estimator": "diagonal_shrinkage",
  "mean_shrinkage": 0.25,
  "covariance_shrinkage": 0.2,
  "current_weights": {
    "AAPL": 0.2,
    "MSFT": 0.2,
    "GOOGL": 0.2,
    "SPY": 0.2,
    "IEF": 0.2
  },
  "transaction_cost_rate": 0.001,
  "fixed_ticket_charge": 1.0,
  "per_asset_fixed_ticket_charges": { "AAPL": 2.0 },
  "market_impact_coefficient": 0.025,
  "max_positions": 4,
  "min_position_weight": 0.05,
  "sector_max_weights": { "technology": 0.5, "financials": 0.3 },
  "factor_exposures": {
    "AAPL": { "market": 1.1, "quality": 0.2 },
    "MSFT": { "market": 1.0, "quality": 0.25 },
    "GOOGL": { "market": 1.05, "quality": 0.1 },
    "SPY": { "market": 1.0, "quality": 0.0 },
    "IEF": { "market": 0.3, "quality": 0.15 }
  },
  "factor_covariance": {
    "market": { "market": 0.04, "quality": 0.01 },
    "quality": { "market": 0.01, "quality": 0.03 }
  },
  "specific_risk": {
    "AAPL": 0.02,
    "MSFT": 0.02,
    "GOOGL": 0.025,
    "SPY": 0.01,
    "IEF": 0.015
  },
  "lot_sizes": { "AAPL": 5, "MSFT": 10, "GOOGL": 5, "SPY": 1, "IEF": 1 },
  "minimum_lot_units": { "AAPL": 2, "MSFT": 1 },
  "maximum_lot_units": {
    "AAPL": 5,
    "MSFT": 3,
    "GOOGL": 8,
    "SPY": 50,
    "IEF": 50
  }
}
```

Key request fields:

- `total_amount`: total investment amount in dollars.
- `risk_tolerance`: either a float in the range `0` to `10` or one of `low`, `medium`, `high`.
- `investment_horizon`: either a month count or one of `short`, `medium`, `long`.
- `tickers`: optional custom ticker list.
- `risk_free_rate`: annual risk-free rate used in performance metrics.
- `return_estimator`: return estimator, currently `sample`, `shrunk_mean`, or `ewma_mean`.
- `covariance_estimator`: covariance estimator, currently `sample`, `diagonal_shrinkage`, or `ewma`.
- `mean_shrinkage`: shrinkage intensity for `shrunk_mean`.
- `covariance_shrinkage`: shrinkage intensity for `diagonal_shrinkage`.
- `estimator_decay`: decay factor used by EWMA estimators.
- `max_gross_exposure`: gross leverage cap for long-short portfolios.
- `max_short_exposure`: per-asset short exposure cap.
- `max_cash_borrow`: borrowing allowance for cash-sleeve leverage.
- `max_turnover`: turnover cap for rebalance-aware models.
- `current_weights`: current portfolio weights used by turnover-aware and transaction-cost-aware rebalancing.
- `transaction_cost_model`: execution-cost baseline, currently `interactive_brokers_fixed`, `default`, or `custom`.
- `transaction_cost_rate`: one-way proportional trading-cost assumption.
- `fixed_ticket_charge`: optional flat dollar fee charged once per traded ticker.
- `market_impact_model`: market-impact curve, currently `linear` or `piecewise_linear`.
- `market_impact_coefficient`: base ADV-scaled market-impact penalty coefficient.
- `per_asset_transaction_costs`: optional per-asset trading-cost overrides keyed by ticker.
- `per_asset_fixed_ticket_charges`: optional per-asset flat ticket-fee overrides keyed by ticker.
- `per_asset_market_impact_coefficients`: optional per-asset market-impact overrides keyed by ticker.
- `impact_adv_floor`: minimum ADV used when scaling market-impact penalties.
- `impact_threshold_adv_ratio`: ADV participation threshold where piecewise-linear impact becomes steeper.
- `impact_excess_slope_multiplier`: slope multiplier applied above the market-impact threshold.
- `max_positions`: maximum number of open positions for cardinality-constrained runs.
- `min_position_weight`: minimum portfolio weight for newly opened positions.
- `sector_max_weights`: optional sector caps keyed by normalized sector names; ETFs and assets without stable sector classification are excluded from this model.
- `factor_exposures`: optional per-ticker factor exposures used by the factor model variants.
- `factor_covariance`: optional factor covariance matrix keyed by factor name.
- `specific_risk`: optional annualized specific variance keyed by ticker for explicit factor models.
- `lot_sizes`: optional minimum tradable unit keyed by ticker for round-lot allocation.
- `minimum_lot_units`: optional minimum integer lot count required when a position is opened.
- `maximum_lot_units`: optional maximum integer lot count per asset for round-lot allocation.

### Response

The optimize endpoint returns:

- normalized risk tolerance and investment horizon
- ranked portfolio results
- efficient-frontier points
- the market-data period used
- an optimization status string

Each portfolio result includes:

- `model_name`
- `weights`
- `expected_annual_return`
- `expected_annual_risk`
- `sharpe_ratio`
- `allocation`
- `applicability_score`
- `reasoning`

Some models also include internal fields such as `cash_weight`, `trade_cost`, `open_positions`, or `shares` during optimization, but the API response currently normalizes results through the standard response schema.

## Ranking

Portfolios are ranked by an applicability score that combines:

- heuristic ordering by risk tolerance and investment horizon
- realized expected return
- realized expected risk
- realized Sharpe ratio
- efficient-frontier context

The ranking layer is output-aware rather than relying only on static model labels.

## Market Data

Primary data behavior:

- historical prices are fetched from Financial Modeling Prep
- the FMP API key is retrieved from Azure Key Vault using `DefaultAzureCredential`
- missing FMP credentials fail loudly
- synthetic data is only used for non-authentication FMP fetch failures

Additional first-pass provider support:

- lightweight provider abstraction for FMP-backed prices, metadata, and liquidity retrieval
- sector and company metadata via FMP profile endpoints
- average daily dollar volume derived from historical price and volume data

Metadata and factor normalization behavior:

- inferred factor models now combine a market factor with additional statistical residual factors derived from aligned return history
- sector-constrained runs normalize common sector aliases, infer sectors from industry when possible, and exclude ETFs from sector caps
- assets with missing or unstable sector labels are dropped from the sector-constrained subproblem instead of aborting the full request
- the estimator layer now supports EWMA return and covariance estimators using only aligned price history already present in the repo
- market-impact modeling now supports either a linear ADV-scaled penalty or a steeper piecewise-linear schedule above a configurable ADV participation threshold
- round-lot defaults are now repo-managed through `app/config/lot_metadata.yml`, with request overrides taking precedence and asset-type-aware fallbacks for omitted inputs

Execution-cost defaults:

- default transaction-cost model: `interactive_brokers_fixed`
- optional tiered transaction-cost model: `interactive_brokers_tiered`
- default one-way transaction-cost rate: `10` bps
- default flat ticket charge: `$1.00` per traded ticker
- default minimum commission for the tiered schedule: `$0.35` per traded ticker
- default market-impact coefficient: `0.025`
- default ADV floor: `$5,000,000`

Environment variables:

- `AZURE_KEYVAULT_NAME` default: `rajesh-invest`
- `FMP_API_SECRET_NAME` default: `fmpapi`
- `FMP_BASE_URL` default: `https://financialmodelingprep.com/api/v3`

Default tickers:

`AAPL, MSFT, GOOGL, AMZN, META, TSLA, JPM, JNJ, PG, KO, SPY, QQQ, IEF, GLD, VNQ`

## Remaining Work For Broader Gurobi Notebook Parity

The repository has first-pass implementations for the major advanced portfolio families, but it is not yet at full broader parity with the Gurobi notebook family.

Main remaining gaps:

- broader provider expansion beyond the current FMP-backed wrapper
- estimator families beyond the current sample, shrinkage, and EWMA options

In other words: the major categories now exist, but some of them are still simplified first-pass implementations rather than complete notebook-family parity.

## Installation

```bash
uv sync
```

## Running The Server

```bash
uv run uvicorn app.main:app --reload
```

Interactive API docs are available at `http://localhost:8000/docs`.

## Running Tests

```bash
uv run pytest tests -q
```

## Project Structure

```text
app/
  main.py
  models/
    schemas.py
  services/
    data_service.py
    estimation.py
    optimization.py
    ranking.py
tests/
  test_api.py
  test_data_service.py
  test_estimation.py
  test_optimization.py
  test_ranking.py
```
