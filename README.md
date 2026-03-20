# Portfolio Management API

A Python portfolio optimization system using SCIP (via [PySCIPOpt](https://github.com/scipopt/PySCIPOpt)) and [FastAPI](https://fastapi.tiangolo.com/). Given a total investment amount, risk tolerance, and investment horizon, the API runs multiple portfolio optimization models and returns the results ranked by applicability to the specified inputs.

## Portfolio Optimization Models

The system implements six portfolio optimization techniques based on the [Gurobi Finance modeling notebooks](https://gurobi-finance.readthedocs.io/en/latest/modeling_notebooks.html), re-implemented using the open-source SCIP solver:

| Model | Description | Best For |
|---|---|---|
| **MinimumVariance** | Minimizes portfolio variance (risk). Solves `min xᵀΣx` s.t. `Σxᵢ=1, xᵢ≥0`. | Conservative investors, short horizons |
| **MaximumReturn** | Maximizes expected return within a risk budget. Solves `max μᵀx` s.t. `xᵀΣx ≤ σ²_max`. | Aggressive investors, long horizons |
| **MaxSharpeRatio** | Maximizes risk-adjusted return (Sharpe ratio / tangency portfolio). Uses parametric sweep with SCIP + scipy refinement. | Balanced risk/return |
| **MeanVariance** | Classic Markowitz mean-variance optimization. Minimizes variance subject to a target return derived from risk/horizon. | Moderate investors |
| **EqualWeight** | Simple 1/n equal allocation. Robust, no optimization required. | High uncertainty, very short horizons |
| **RiskParity** | Equalizes risk contributions from each asset. Solved via scipy SLSQP. | Balanced diversification |

## API

### Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/models` | List all available optimization models |
| `POST` | `/optimize` | Run all models and return ranked results |

### Request: `POST /optimize`

```json
{
  "total_amount": 100000,
  "risk_tolerance": "medium",
  "investment_horizon": "long",
  "tickers": ["AAPL", "MSFT", "GOOGL", "SPY", "IEF"],
  "risk_free_rate": 0.04
}
```

**Field descriptions:**

- `total_amount` *(required)*: Total investment in dollars (must be > 0).
- `risk_tolerance` *(required)*: Either a float `0–10` or one of `"low"` (→2), `"medium"` (→5), `"high"` (→8).
- `investment_horizon` *(required)*: Number of months as an integer, or `"short"` (→6 months), `"medium"` (→24 months), `"long"` (→60 months).
- `tickers` *(optional)*: List of ticker symbols. Defaults to a diversified set of 15 assets (US stocks, ETFs, bonds, gold).
- `risk_free_rate` *(optional)*: Annual risk-free rate for Sharpe ratio calculation. Defaults to `0.04` (4%).

### Response

```json
{
  "total_amount": 100000.0,
  "risk_tolerance_normalized": 5.0,
  "investment_horizon_months": 60,
  "portfolios": [
    {
      "rank": 1,
      "model_name": "MaxSharpeRatio",
      "model_description": "Maximizes risk-adjusted return (Sharpe ratio). Best for balanced risk/return.",
      "weights": {"AAPL": 0.15, "MSFT": 0.22, "SPY": 0.35, ...},
      "expected_annual_return": 0.112,
      "expected_annual_risk": 0.148,
      "sharpe_ratio": 0.486,
      "allocation": {"AAPL": 15000.0, "MSFT": 22000.0, "SPY": 35000.0, ...},
      "applicability_score": 100.0,
      "reasoning": "Optimizes risk-adjusted returns (Sharpe ratio) - versatile approach for medium risk tolerance (5.0/10) and 60-month horizon."
    },
    ...
  ],
  "data_period_used": "756 trading days",
  "optimization_status": "success"
}
```

## Ranking Logic

Models are ranked by an **applicability score** (0–100) computed from:

1. **Risk category** (low/medium/high based on `risk_tolerance`):
   - Low (0–3): MinimumVariance → EqualWeight → RiskParity → MeanVariance → MaxSharpeRatio → MaximumReturn
   - Medium (4–6): MaxSharpeRatio → MeanVariance → RiskParity → MinimumVariance → EqualWeight → MaximumReturn
   - High (7–10): MaximumReturn → MaxSharpeRatio → MeanVariance → RiskParity → EqualWeight → MinimumVariance

2. **Horizon adjustment**: Short horizons boost conservative models; long horizons boost aggressive models.

## Market Data

- **Primary**: Historical price data fetched via [yfinance](https://github.com/ranaroussi/yfinance).
- **Fallback**: If yfinance is unavailable, synthetic data is generated using geometric Brownian motion with realistic parameters per asset class.

Default tickers: `AAPL, MSFT, GOOGL, AMZN, META, TSLA, JPM, JNJ, PG, KO, SPY, QQQ, IEF, GLD, VNQ`

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## Running Tests

```bash
pytest tests/ -v
```

## Project Structure

```
app/
├── main.py               # FastAPI application
├── models/
│   └── schemas.py        # Pydantic request/response schemas
└── services/
    ├── data_service.py   # Market data fetching (yfinance + synthetic fallback)
    ├── optimization.py   # SCIP-based portfolio optimization models
    └── ranking.py        # Applicability scoring and ranking
tests/
├── test_optimization.py  # Unit tests for each optimization model
└── test_api.py           # Integration tests for the API endpoints
requirements.txt
```
