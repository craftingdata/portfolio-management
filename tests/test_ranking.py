import numpy as np

from app.services.ranking import rank_portfolios


def test_rank_portfolios_uses_output_metrics_and_frontier():
    tickers = ["AAPL", "MSFT", "SPY"]
    total_amount = 100000.0

    portfolio_results = {
        "MeanVariance": {
            "weights": np.array([0.20, 0.20, 0.60]),
            "expected_return": 0.030,
            "expected_risk": 0.42,
            "sharpe_ratio": 0.01,
        },
        "RiskParity": {
            "weights": np.array([0.40, 0.35, 0.25]),
            "expected_return": 0.160,
            "expected_risk": 0.10,
            "sharpe_ratio": 1.60,
        },
    }

    efficient_frontier = [
        {"target_return": 0.04, "expected_return": 0.06, "expected_risk": 0.10, "sharpe_ratio": 0.40},
        {"target_return": 0.08, "expected_return": 0.10, "expected_risk": 0.16, "sharpe_ratio": 0.62},
        {"target_return": 0.12, "expected_return": 0.13, "expected_risk": 0.22, "sharpe_ratio": 0.59},
    ]

    ranked = rank_portfolios(
        portfolio_results=portfolio_results,
        tickers=tickers,
        total_amount=total_amount,
        risk_tolerance=5.0,
        investment_horizon_months=24,
        efficient_frontier=efficient_frontier,
    )

    assert [portfolio.model_name for portfolio in ranked] == ["RiskParity", "MeanVariance"]
    assert ranked[0].applicability_score > ranked[1].applicability_score
