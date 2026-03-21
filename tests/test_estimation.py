import numpy as np
import pandas as pd

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
