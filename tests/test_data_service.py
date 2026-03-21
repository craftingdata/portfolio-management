from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from app.services import data_service


class _FakeSecretClient:
    def __init__(self, vault_url, credential):
        self.vault_url = vault_url
        self.credential = credential
        self.calls = 0

    def get_secret(self, name):
        self.calls += 1
        return SimpleNamespace(value=f"secret-for-{name}")


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_get_fmp_api_secret_uses_cache(monkeypatch):
    data_service._fmp_secret_cache = None
    fake_client = _FakeSecretClient("https://rajesh-invest.vault.azure.net", credential=object())

    monkeypatch.setattr(data_service, "DefaultAzureCredential", lambda **kwargs: object())
    monkeypatch.setattr(data_service, "SecretClient", lambda vault_url, credential: fake_client)

    first = data_service.get_fmp_api_secret()
    second = data_service.get_fmp_api_secret()

    assert first.value == "secret-for-fmpapi"
    assert second.value == "secret-for-fmpapi"
    assert fake_client.calls == 1


def test_get_market_data_uses_fmp(monkeypatch):
    payload = {
        "historical": [
            {"date": "2024-01-05", "adjClose": 104.0},
            {"date": "2024-01-04", "adjClose": 103.0},
            {"date": "2024-01-03", "adjClose": 101.0},
            {"date": "2024-01-02", "adjClose": 100.0},
        ]
    }

    captured_params = []

    def fake_get(url, params, timeout):
        captured_params.append((url, params, timeout))
        return _FakeResponse(payload)

    fake_estimated = SimpleNamespace(
        returns_df=pd.DataFrame([[0.01, 0.01], [0.02, 0.02], [0.03, 0.03]], columns=["AAPL", "MSFT"]),
        mu=np.array([0.12, 0.13]),
        sigma_matrix=np.array([[0.04, 0.01], [0.01, 0.05]]),
    )

    monkeypatch.setattr(data_service, "get_fmp_api_key", lambda: "test-fmp-key")
    monkeypatch.setattr(data_service.httpx, "get", fake_get)
    monkeypatch.setattr(
        data_service,
        "estimate_market_inputs",
        lambda prices_df, api_key=None, return_estimator="sample", covariance_estimator="sample", mean_shrinkage=0.0, covariance_shrinkage=0.0: fake_estimated,
    )

    prices_df, returns_df, mu, sigma = data_service.get_market_data(["AAPL", "MSFT"], period_months=1)

    assert list(prices_df.columns) == ["AAPL", "MSFT"]
    assert returns_df.equals(fake_estimated.returns_df)
    assert np.allclose(mu, fake_estimated.mu)
    assert np.allclose(sigma, fake_estimated.sigma_matrix)
    assert captured_params[0][1]["apikey"] == "test-fmp-key"


def test_get_market_data_raises_when_api_key_missing(monkeypatch):
    monkeypatch.setattr(data_service, "get_fmp_api_key", lambda: None)

    with pytest.raises(data_service.MissingFMPAPIKeyError):
        data_service.get_market_data(["AAPL", "MSFT"], period_months=1)


def test_get_market_data_falls_back_to_synthetic_for_non_auth_failure(monkeypatch):
    expected = (
        pd.DataFrame([[100.0, 101.0]], columns=["AAPL", "MSFT"]),
        pd.DataFrame([[0.01, 0.02]], columns=["AAPL", "MSFT"]),
        np.array([0.10, 0.12]),
        np.array([[0.04, 0.01], [0.01, 0.05]]),
    )

    monkeypatch.setattr(
        data_service,
        "_fetch_fmp_market_data",
        lambda tickers, period_months, return_estimator="sample", covariance_estimator="sample", mean_shrinkage=0.0, covariance_shrinkage=0.0: (_ for _ in ()).throw(RuntimeError("upstream fmp error")),
    )
    monkeypatch.setattr(
        data_service,
        "_generate_synthetic_data",
        lambda tickers, n_days, return_estimator="sample", covariance_estimator="sample", mean_shrinkage=0.0, covariance_shrinkage=0.0: expected,
    )

    actual = data_service.get_market_data(["AAPL", "MSFT"], period_months=1)

    assert actual[0].equals(expected[0])
    assert actual[1].equals(expected[1])
    assert np.allclose(actual[2], expected[2])
    assert np.allclose(actual[3], expected[3])


def test_get_market_metadata_uses_profile_endpoint(monkeypatch):
    payload = [
        {
            "symbol": "AAPL",
            "companyName": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "exchangeShortName": "NASDAQ",
            "assetType": "Equity",
            "isEtf": False,
        }
    ]

    captured_urls = []

    def fake_get(url, params, timeout):
        captured_urls.append(url)
        return _FakeResponse(payload)

    monkeypatch.setattr(data_service, "get_fmp_api_key", lambda: "test-fmp-key")
    monkeypatch.setattr(data_service.httpx, "get", fake_get)

    metadata = data_service.get_market_metadata(["AAPL"])

    assert metadata["AAPL"]["sector"] == "Technology"
    assert metadata["AAPL"]["industry"] == "Consumer Electronics"
    assert "/profile/AAPL" in captured_urls[0]


def test_get_market_liquidity_uses_historical_volume(monkeypatch):
    payload = {
        "historical": [
            {"date": "2024-01-05", "adjClose": 104.0, "volume": 1000},
            {"date": "2024-01-04", "adjClose": 103.0, "volume": 1200},
            {"date": "2024-01-03", "adjClose": 101.0, "volume": 1100},
            {"date": "2024-01-02", "adjClose": 100.0, "volume": 900},
        ]
    }

    monkeypatch.setattr(data_service, "get_fmp_api_key", lambda: "test-fmp-key")
    monkeypatch.setattr(data_service.httpx, "get", lambda url, params, timeout: _FakeResponse(payload))

    liquidity = data_service.get_market_liquidity(["AAPL"], period_months=1)

    assert "AAPL" in liquidity
    assert liquidity["AAPL"] > 0


def test_get_market_data_aligns_dates_and_drops_sparse_series(monkeypatch):
    payloads = {
        "AAPL": {
            "historical": [
                {"date": "2024-01-05", "adjClose": 104.0},
                {"date": "2024-01-04", "adjClose": 103.0},
                {"date": "2024-01-03", "adjClose": 102.0},
                {"date": "2024-01-02", "adjClose": 100.0},
            ]
        },
        "MSFT": {
            "historical": [
                {"date": "2024-01-05", "adjClose": 205.0},
                {"date": "2024-01-04", "adjClose": 203.0},
                {"date": "2024-01-03", "adjClose": 200.0},
            ]
        },
        "SPY": {
            "historical": [
                {"date": "2024-01-05", "adjClose": 300.0},
            ]
        },
    }
    captured = {}

    def fake_get(url, params, timeout):
        ticker = url.rsplit("/", 1)[-1]
        return _FakeResponse(payloads[ticker])

    def fake_estimate(prices_df, api_key=None, return_estimator="sample", covariance_estimator="sample", mean_shrinkage=0.0, covariance_shrinkage=0.0):
        captured["prices_df"] = prices_df.copy()
        returns_df = prices_df.pct_change().dropna()
        return SimpleNamespace(
            returns_df=returns_df,
            mu=returns_df.mean().to_numpy() * 252,
            sigma_matrix=returns_df.cov().to_numpy() * 252,
        )

    monkeypatch.setattr(data_service, "get_fmp_api_key", lambda: "test-fmp-key")
    monkeypatch.setattr(data_service.httpx, "get", fake_get)
    monkeypatch.setattr(data_service, "estimate_market_inputs", fake_estimate)

    prices_df, returns_df, mu, sigma = data_service.get_market_data(["AAPL", "MSFT", "SPY"], period_months=1)

    assert list(captured["prices_df"].columns) == ["AAPL", "MSFT"]
    assert len(captured["prices_df"]) == 3
    assert not captured["prices_df"].isna().any().any()
    assert list(prices_df.columns) == ["AAPL", "MSFT"]
    assert returns_df.shape[1] == 2
    assert mu.shape == (2,)
    assert sigma.shape == (2, 2)