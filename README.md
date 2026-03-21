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

| Model                        | Description                                                                        |
| ---------------------------- | ---------------------------------------------------------------------------------- |
| `LeverageShortSelling`       | Long-short utility optimization with gross leverage and short exposure limits.     |
| `LeverageBorrowing`          | Utility optimization with an explicit cash sleeve and borrowing allowance.         |
| `TurnoverConstrained`        | Mean-variance rebalancing with explicit turnover limits from current weights.      |
| `TransactionCostRebalancing` | Rebalancing model with explicit buy/sell variables and proportional trading costs. |

### Advanced First-Pass Models

| Model                       | Description                                                                                                       |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `FactorUtilityMaximization` | Utility maximization using either an explicit factor contract or a market-factor-implied covariance matrix.       |
| `FactorVarianceConstraint`  | Mean-variance optimization using either an explicit factor contract or a market-factor-implied covariance matrix. |
| `SectorAllocation`          | Mean-variance optimization with sector concentration caps.                                                        |
| `CardinalityMinBuyIn`       | Mean-variance optimization with a maximum holdings count and minimum buy-in weights.                              |
| `RoundLotAllocation`        | Integer lot-based allocation using latest prices, configurable lot sizes, and a cash remainder.                   |

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
  "lot_sizes": { "AAPL": 5, "MSFT": 10, "GOOGL": 5, "SPY": 1, "IEF": 1 }
}
```

Key request fields:

- `total_amount`: total investment amount in dollars.
- `risk_tolerance`: either a float in the range `0` to `10` or one of `low`, `medium`, `high`.
- `investment_horizon`: either a month count or one of `short`, `medium`, `long`.
- `tickers`: optional custom ticker list.
- `risk_free_rate`: annual risk-free rate used in performance metrics.
- `return_estimator`: return estimator, currently `sample` or `shrunk_mean`.
- `covariance_estimator`: covariance estimator, currently `sample` or `diagonal_shrinkage`.
- `mean_shrinkage`: shrinkage intensity for `shrunk_mean`.
- `covariance_shrinkage`: shrinkage intensity for `diagonal_shrinkage`.
- `max_gross_exposure`: gross leverage cap for long-short portfolios.
- `max_short_exposure`: per-asset short exposure cap.
- `max_cash_borrow`: borrowing allowance for cash-sleeve leverage.
- `max_turnover`: turnover cap for rebalance-aware models.
- `current_weights`: current portfolio weights used by turnover-aware and transaction-cost-aware rebalancing.
- `transaction_cost_model`: execution-cost baseline, currently `interactive_brokers_fixed`, `default`, or `custom`.
- `transaction_cost_rate`: one-way proportional trading-cost assumption.
- `market_impact_coefficient`: linear ADV-scaled market-impact penalty coefficient.
- `per_asset_transaction_costs`: optional per-asset trading-cost overrides keyed by ticker.
- `per_asset_market_impact_coefficients`: optional per-asset market-impact overrides keyed by ticker.
- `impact_adv_floor`: minimum ADV used when scaling market-impact penalties.
- `max_positions`: maximum number of open positions for cardinality-constrained runs.
- `min_position_weight`: minimum portfolio weight for newly opened positions.
- `sector_max_weights`: optional sector caps keyed by normalized sector names.
- `factor_exposures`: optional per-ticker factor exposures used by the factor model variants.
- `factor_covariance`: optional factor covariance matrix keyed by factor name.
- `specific_risk`: optional annualized specific variance keyed by ticker for explicit factor models.
- `lot_sizes`: optional minimum tradable unit keyed by ticker for round-lot allocation.

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

Execution-cost defaults:

- default transaction-cost model: `interactive_brokers_fixed`
- default one-way transaction-cost rate: `10` bps
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

- richer factor-model infrastructure beyond the current explicit-contract or market-factor proxy paths
- broader sector and metadata normalization, especially ETF treatment and richer taxonomy handling
- richer lot-size semantics beyond the current request-driven lot size assumptions
- deeper transaction-cost calibration beyond the current broker-calibrated default plus per-asset overrides, especially fixed-fee schedules
- more rigorous market-impact modeling beyond the current linear ADV-based formulation
- deeper estimator families and broader provider expansion beyond the current FMP-backed wrapper

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
