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
    monkeypatch.setattr(data_service, "estimate_market_inputs", lambda prices_df, api_key=None: fake_estimated)

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

    monkeypatch.setattr(data_service, "_fetch_fmp_market_data", lambda tickers, period_months: (_ for _ in ()).throw(RuntimeError("upstream fmp error")))
    monkeypatch.setattr(data_service, "_generate_synthetic_data", lambda tickers, n_days: expected)

    actual = data_service.get_market_data(["AAPL", "MSFT"], period_months=1)

    assert actual[0].equals(expected[0])
    assert actual[1].equals(expected[1])
    assert np.allclose(actual[2], expected[2])
    assert np.allclose(actual[3], expected[3])