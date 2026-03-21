import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app


def _make_mock_market_data(tickers=None, period_months=36):
    """Return synthetic market data for testing without network access."""
    if tickers is None:
        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META",
                   "TSLA", "JPM", "JNJ", "PG", "KO",
                   "SPY", "QQQ", "IEF", "GLD", "VNQ"]
    n = len(tickers)
    np.random.seed(42)

    mu = np.random.uniform(0.06, 0.15, n)
    vols = np.random.uniform(0.12, 0.30, n)
    corr = np.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            c = np.random.uniform(0.2, 0.7)
            corr[i, j] = c
            corr[j, i] = c

    # Ensure positive definite
    eigvals = np.linalg.eigvalsh(corr)
    if eigvals.min() < 1e-6:
        corr += (abs(eigvals.min()) + 1e-5) * np.eye(n)
        d = np.sqrt(np.diag(corr))
        corr = corr / np.outer(d, d)

    sigma = np.outer(vols, vols) * corr

    # Generate price data
    n_days = 252 * 3
    daily_returns = mu / 252
    daily_vols = vols / np.sqrt(252)
    prices = np.ones((n_days + 1, n)) * 100.0
    for t in range(n_days):
        ret = daily_returns + daily_vols * np.random.standard_normal(n)
        prices[t + 1] = prices[t] * (1 + ret)

    start_date = pd.Timestamp.today().normalize() - pd.offsets.BDay(n_days)
    dates = pd.bdate_range(start=start_date, periods=n_days + 1)
    prices_df = pd.DataFrame(prices, index=dates, columns=tickers)
    returns_df = prices_df.pct_change().dropna()

    return prices_df, returns_df, mu, sigma


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_list_models(client):
    response = client.get("/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) == 10
    model_names = [m["name"] for m in data["models"]]
    for expected in [
        "MinimumVariance",
        "MaximumReturn",
        "UtilityMaximization",
        "LeverageShortSelling",
        "LeverageBorrowing",
        "TurnoverConstrained",
        "MaxSharpeRatio",
        "MeanVariance",
        "EqualWeight",
        "RiskParity",
    ]:
        assert expected in model_names


def test_optimize_medium_risk(client):
    with patch("app.main.get_market_data", side_effect=_make_mock_market_data):
        response = client.post("/optimize", json={
            "total_amount": 100000,
            "risk_tolerance": "medium",
            "investment_horizon": "medium",
        })
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["optimization_status"] == "success"
    assert len(data["portfolios"]) == 10
    assert len(data["efficient_frontier"]) == 7
    # Check first portfolio structure
    p = data["portfolios"][0]
    for field in ["rank", "model_name", "weights", "expected_annual_return", "expected_annual_risk", "sharpe_ratio", "allocation", "applicability_score", "reasoning"]:
        assert field in p, f"Missing field: {field}"
    assert p["rank"] == 1


def test_optimize_numeric_inputs(client):
    with patch("app.main.get_market_data", side_effect=_make_mock_market_data):
        response = client.post("/optimize", json={
            "total_amount": 50000,
            "risk_tolerance": 7.5,
            "investment_horizon": 18,
        })
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total_amount"] == 50000
    assert data["risk_tolerance_normalized"] == 7.5
    assert data["investment_horizon_months"] == 18
    assert len(data["portfolios"]) == 10


def test_optimize_low_risk(client):
    with patch("app.main.get_market_data", side_effect=_make_mock_market_data):
        response = client.post("/optimize", json={
            "total_amount": 75000,
            "risk_tolerance": "low",
            "investment_horizon": "short",
        })
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["risk_tolerance_normalized"] == 2.0
    assert data["investment_horizon_months"] == 6
    assert len(data["portfolios"]) == 10
    # For low risk, top portfolio should be conservative
    top_model = data["portfolios"][0]["model_name"]
    assert top_model in ["MinimumVariance", "EqualWeight", "RiskParity", "UtilityMaximization", "TurnoverConstrained"]


def test_optimize_high_risk(client):
    with patch("app.main.get_market_data", side_effect=_make_mock_market_data):
        response = client.post("/optimize", json={
            "total_amount": 200000,
            "risk_tolerance": "high",
            "investment_horizon": "long",
        })
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["risk_tolerance_normalized"] == 8.0
    assert data["investment_horizon_months"] == 60
    assert len(data["portfolios"]) == 10


def test_validation_negative_amount(client):
    response = client.post("/optimize", json={
        "total_amount": -1000,
        "risk_tolerance": "medium",
        "investment_horizon": "medium",
    })
    assert response.status_code == 422


def test_validation_invalid_risk_tolerance(client):
    response = client.post("/optimize", json={
        "total_amount": 10000,
        "risk_tolerance": "extreme",
        "investment_horizon": "medium",
    })
    assert response.status_code == 422


def test_optimize_returns_500_when_api_key_missing(client):
    with patch("app.main.get_market_data", side_effect=RuntimeError("FMP API key is unavailable")):
        response = client.post("/optimize", json={
            "total_amount": 100000,
            "risk_tolerance": "medium",
            "investment_horizon": "medium",
        })

    assert response.status_code == 500
    assert "FMP API key is unavailable" in response.json()["detail"]


def test_portfolio_fields(client):
    """Test that each portfolio result has all required fields with correct types."""
    with patch("app.main.get_market_data", side_effect=_make_mock_market_data):
        response = client.post("/optimize", json={
            "total_amount": 100000,
            "risk_tolerance": 5.0,
            "investment_horizon": 12,
        })
    assert response.status_code == 200, response.text
    data = response.json()
    for portfolio in data["portfolios"]:
        assert isinstance(portfolio["rank"], int)
        assert isinstance(portfolio["model_name"], str)
        assert isinstance(portfolio["weights"], dict)
        assert isinstance(portfolio["expected_annual_return"], float)
        assert isinstance(portfolio["expected_annual_risk"], float)
        assert isinstance(portfolio["sharpe_ratio"], float)
        assert isinstance(portfolio["allocation"], dict)
        assert isinstance(portfolio["applicability_score"], float)
        assert isinstance(portfolio["reasoning"], str)
        # Weights should approximately sum to 1
        assert abs(sum(portfolio["weights"].values()) - 1.0) < 1e-3
        if portfolio["model_name"] not in ["LeverageShortSelling", "LeverageBorrowing"]:
            assert all(weight >= -0.001 for weight in portfolio["weights"].values())
        # Allocation should sum to approximately total_amount
        assert abs(sum(portfolio["allocation"].values()) - 100000) < 10


def test_portfolio_ranks_unique(client):
    """Test that each portfolio has a unique rank 1-6."""
    with patch("app.main.get_market_data", side_effect=_make_mock_market_data):
        response = client.post("/optimize", json={
            "total_amount": 100000,
            "risk_tolerance": "medium",
            "investment_horizon": "medium",
        })
    assert response.status_code == 200
    data = response.json()
    ranks = [p["rank"] for p in data["portfolios"]]
    assert sorted(ranks) == list(range(1, 11))
