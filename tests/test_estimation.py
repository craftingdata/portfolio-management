import numpy as np
import pandas as pd
import pytest

from app.services import estimation


def test_estimate_market_inputs_collects_toolkit_metrics(monkeypatch):
    prices_df = pd.DataFrame(
        {
            "AAPL": [100.0, 102.0, 101.0, 104.0],
            "MSFT": [200.0, 201.0, 203.0, 206.0],
        },
        index=pd.date_range("2024-01-01", periods=4, freq="B"),
    )

    class _FakeRisk:
        def get_value_at_risk(self, period="daily"):
            return pd.DataFrame({"AAPL": [-0.02], "MSFT": [-0.01]}, index=[pd.Timestamp("2024-01-04")])

        def get_maximum_drawdown(self, period="daily"):
            return pd.DataFrame({"AAPL": [-0.10], "MSFT": [-0.08]}, index=[pd.Timestamp("2024-01-04")])

    class _FakeToolkit:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.risk = _FakeRisk()

    captured = {}

    def fake_get_toolkit_class():
        class _CapturingToolkit(_FakeToolkit):
            def __init__(self, **kwargs):
                captured.update(kwargs)
                super().__init__(**kwargs)

        return _CapturingToolkit

    monkeypatch.setattr(estimation, "get_toolkit_class", fake_get_toolkit_class)

    result = estimation.estimate_market_inputs(prices_df, api_key="test-key")

    assert result.returns_df.shape == (3, 2)
    assert result.mu.shape == (2,)
    assert result.sigma_matrix.shape == (2, 2)
    assert "daily_value_at_risk" in result.toolkit_risk_metrics
    assert result.toolkit_risk_metrics["daily_value_at_risk"]["AAPL"] == -0.02
    assert result.toolkit_risk_metrics["daily_maximum_drawdown"]["MSFT"] == -0.08
    assert captured["api_key"] == "test-key"
    assert captured["tickers"] == ["AAPL", "MSFT"]


def test_estimate_market_inputs_skips_toolkit_without_api_key(monkeypatch):
    prices_df = pd.DataFrame(
        {
            "AAPL": [100.0, 102.0, 101.0, 104.0],
            "MSFT": [200.0, 201.0, 203.0, 206.0],
        },
        index=pd.date_range("2024-01-01", periods=4, freq="B"),
    )

    def fail_if_called():
        raise AssertionError("FinanceToolkit should not be constructed without an API key")

    monkeypatch.setattr(estimation, "get_toolkit_class", fail_if_called)

    result = estimation.estimate_market_inputs(prices_df, api_key=None)

    assert result.returns_df.shape == (3, 2)
    assert result.toolkit_risk_metrics == {}


def test_estimate_market_inputs_keeps_covariance_positive_definite(monkeypatch):
    prices_df = pd.DataFrame(
        {
            "AAPL": [100.0, 100.0, 100.0, 100.0],
            "MSFT": [200.0, 200.0, 200.0, 200.0],
        },
        index=pd.date_range("2024-01-01", periods=4, freq="B"),
    )

    class _FailingToolkit:
        def __init__(self, **kwargs):
            raise RuntimeError("skip toolkit")

    monkeypatch.setattr(estimation, "get_toolkit_class", lambda: _FailingToolkit)

    result = estimation.estimate_market_inputs(prices_df)

    eigvals = np.linalg.eigvalsh(result.sigma_matrix)
    assert np.all(eigvals > 0)


def test_estimate_market_inputs_supports_explicit_estimators(monkeypatch):
    prices_df = pd.DataFrame(
        {
            "AAPL": [100.0, 101.0, 104.0, 103.0, 106.0],
            "MSFT": [200.0, 202.0, 204.0, 205.0, 207.0],
            "GOOGL": [300.0, 304.0, 306.0, 309.0, 312.0],
        },
        index=pd.date_range("2024-01-01", periods=5, freq="B"),
    )

    monkeypatch.setattr(estimation, "get_toolkit_class", lambda: (_ for _ in ()).throw(AssertionError("should not build toolkit")))

    sample = estimation.estimate_market_inputs(prices_df)
    shrunk = estimation.estimate_market_inputs(
        prices_df,
        return_estimator="shrunk_mean",
        covariance_estimator="diagonal_shrinkage",
        mean_shrinkage=0.5,
        covariance_shrinkage=0.4,
    )
    ewma = estimation.estimate_market_inputs(
        prices_df,
        return_estimator="ewma_mean",
        covariance_estimator="ewma",
        estimator_decay=0.90,
    )

    assert sample.mu.shape == shrunk.mu.shape == ewma.mu.shape == (3,)
    assert sample.sigma_matrix.shape == shrunk.sigma_matrix.shape == ewma.sigma_matrix.shape == (3, 3)
    assert not np.allclose(sample.mu, shrunk.mu)
    assert not np.allclose(sample.mu, ewma.mu)
    assert np.all(np.isfinite(shrunk.mu))
    assert np.all(np.isfinite(ewma.mu))
    assert np.all(np.linalg.eigvalsh(shrunk.sigma_matrix) > 0)
    assert np.all(np.linalg.eigvalsh(ewma.sigma_matrix) > 0)


def test_estimate_market_inputs_requires_minimum_history():
    prices_df = pd.DataFrame(
        {"AAPL": [100.0, 101.0], "MSFT": [200.0, 201.0]},
        index=pd.date_range("2024-01-01", periods=2, freq="B"),
    )

    with pytest.raises(ValueError, match="At least three price observations"):
        estimation.estimate_market_inputs(prices_df)
