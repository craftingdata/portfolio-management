import numpy as np
import pytest
from app.services.optimization import (
    minimum_variance,
    maximum_return,
    max_sharpe_ratio,
    mean_variance,
    equal_weight,
    risk_parity,
    run_all_models,
    compute_metrics,
)


@pytest.fixture
def synthetic_data():
    """Generate reproducible synthetic market data for testing."""
    np.random.seed(123)
    n = 5
    tickers = ["AAPL", "MSFT", "GOOGL", "JPM", "SPY"]
    mu = np.array([0.12, 0.11, 0.10, 0.09, 0.08])

    # Build a simple covariance matrix
    vols = np.array([0.25, 0.22, 0.23, 0.18, 0.15])
    corr = np.array([
        [1.00, 0.70, 0.65, 0.50, 0.60],
        [0.70, 1.00, 0.68, 0.52, 0.62],
        [0.65, 0.68, 1.00, 0.48, 0.58],
        [0.50, 0.52, 0.48, 1.00, 0.55],
        [0.60, 0.62, 0.58, 0.55, 1.00],
    ])
    sigma = np.outer(vols, vols) * corr
    return tickers, mu, sigma


def assert_valid_portfolio(result, n):
    """Common assertions for all portfolio results."""
    weights = result["weights"]
    assert len(weights) == n, f"Expected {n} weights, got {len(weights)}"
    assert abs(weights.sum() - 1.0) < 1e-4, f"Weights sum {weights.sum()} != 1"
    assert all(w >= -0.001 for w in weights), f"Negative weight found: {weights}"
    assert np.isfinite(result["expected_return"]), "expected_return is not finite"
    assert np.isfinite(result["expected_risk"]), "expected_risk is not finite"
    assert np.isfinite(result["sharpe_ratio"]), "sharpe_ratio is not finite"
    assert result["expected_risk"] >= 0, "expected_risk must be non-negative"


def test_minimum_variance(synthetic_data):
    tickers, mu, sigma = synthetic_data
    result = minimum_variance(mu, sigma)
    assert result["model_name"] == "MinimumVariance"
    assert_valid_portfolio(result, len(mu))


def test_maximum_return(synthetic_data):
    tickers, mu, sigma = synthetic_data
    result = maximum_return(mu, sigma, risk_level=0.5)
    assert result["model_name"] == "MaximumReturn"
    assert_valid_portfolio(result, len(mu))


def test_max_sharpe_ratio(synthetic_data):
    tickers, mu, sigma = synthetic_data
    result = max_sharpe_ratio(mu, sigma)
    assert result["model_name"] == "MaxSharpeRatio"
    assert_valid_portfolio(result, len(mu))


def test_mean_variance(synthetic_data):
    tickers, mu, sigma = synthetic_data
    result = mean_variance(mu, sigma, risk_level=0.5)
    assert result["model_name"] == "MeanVariance"
    assert_valid_portfolio(result, len(mu))


def test_equal_weight(synthetic_data):
    tickers, mu, sigma = synthetic_data
    result = equal_weight(mu, sigma)
    assert result["model_name"] == "EqualWeight"
    assert_valid_portfolio(result, len(mu))
    # All weights should be equal
    n = len(mu)
    expected_w = 1.0 / n
    assert all(abs(w - expected_w) < 1e-6 for w in result["weights"]), "Weights not equal"


def test_risk_parity(synthetic_data):
    tickers, mu, sigma = synthetic_data
    result = risk_parity(mu, sigma)
    assert result["model_name"] == "RiskParity"
    assert_valid_portfolio(result, len(mu))


def test_compute_metrics(synthetic_data):
    tickers, mu, sigma = synthetic_data
    n = len(mu)
    weights = np.ones(n) / n
    ret, risk, sharpe = compute_metrics(weights, mu, sigma, risk_free_rate=0.04)
    assert np.isfinite(ret)
    assert np.isfinite(risk)
    assert np.isfinite(sharpe)
    assert risk > 0


@pytest.mark.parametrize("risk_tol", [1.0, 5.0, 9.0])
def test_run_all_models(synthetic_data, risk_tol):
    tickers, mu, sigma = synthetic_data
    results = run_all_models(mu, sigma, tickers=tickers, risk_tolerance_normalized=risk_tol)

    expected_models = {"MinimumVariance", "MaximumReturn", "MaxSharpeRatio", "MeanVariance", "EqualWeight", "RiskParity"}
    assert set(results.keys()) == expected_models, f"Missing models: {expected_models - set(results.keys())}"

    n = len(mu)
    for model_name, result in results.items():
        assert_valid_portfolio(result, n)
