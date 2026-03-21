import logging
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx
import numpy as np
import pandas as pd
import yaml
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import KeyVaultSecret, SecretClient

from app.services.estimation import estimate_market_inputs

logger = logging.getLogger(__name__)

AZURE_KEYVAULT_NAME = os.getenv("AZURE_KEYVAULT_NAME", "rajesh-invest")
FMP_API_SECRET_NAME = os.getenv("FMP_API_SECRET_NAME", "fmpapi")
FMP_BASE_URL = os.getenv("FMP_BASE_URL", "https://financialmodelingprep.com/api/v3")
LOT_METADATA_PATH = Path(__file__).resolve().parents[1] / "config" / "lot_metadata.yml"

_fmp_secret_cache: Optional[KeyVaultSecret] = None
_lot_metadata_cache: Optional[dict] = None


class MissingFMPAPIKeyError(RuntimeError):
    """Raised when the FMP API key cannot be retrieved from Azure Key Vault."""


@dataclass(frozen=True)
class FMPProviderConfig:
    api_key: str
    base_url: str = FMP_BASE_URL
    timeout: float = 30.0

DEFAULT_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META",
    "TSLA", "JPM", "JNJ", "PG", "KO",
    "SPY", "QQQ", "IEF", "GLD", "VNQ"
]


class FMPMarketDataProvider:
    """Lightweight provider wrapper for FMP-backed price, metadata, and liquidity fetches."""

    def __init__(self, config: FMPProviderConfig):
        self.config = config

    def _get(self, path: str, params: Dict[str, object]) -> dict | list:
        response = httpx.get(
            f"{self.config.base_url}{path}",
            params={**params, "apikey": self.config.api_key},
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()

    def fetch_history(self, ticker: str, start_date: date, end_date: date) -> pd.DataFrame:
        payload = self._get(
            f"/historical-price-full/{ticker}",
            {"from": start_date.isoformat(), "to": end_date.isoformat()},
        )
        history = payload.get("historical", [])
        if not history:
            raise ValueError(f"FMP returned no historical data for {ticker}")

        history_df = pd.DataFrame(history)
        if "date" not in history_df.columns:
            raise ValueError(f"FMP payload missing date field for {ticker}")

        price_column = "adjClose" if "adjClose" in history_df.columns else "close"
        if price_column not in history_df.columns:
            raise ValueError(f"FMP payload missing price field for {ticker}")

        history_df = history_df.copy()
        history_df["date"] = pd.to_datetime(history_df["date"])
        return history_df.sort_values("date")

    def fetch_price_series(self, ticker: str, start_date: date, end_date: date) -> pd.Series:
        history_df = self.fetch_history(ticker, start_date=start_date, end_date=end_date)
        price_column = "adjClose" if "adjClose" in history_df.columns else "close"
        series = history_df[["date", price_column]].copy()
        series = series.set_index("date")[price_column].astype(float)
        series.name = ticker
        return series

    def fetch_metadata(self, ticker: str) -> Dict[str, str]:
        payload = self._get(f"/profile/{ticker}", {})
        profile = payload[0] if isinstance(payload, list) and payload else payload.get("profile", [{}])[0] if isinstance(payload, dict) and "profile" in payload else payload
        if isinstance(profile, list) and profile:
            profile = profile[0]
        return {
            "symbol": str(profile.get("symbol", ticker)),
            "companyName": str(profile.get("companyName", ticker)),
            "sector": str(profile.get("sector", "Unknown")),
            "industry": str(profile.get("industry", "Unknown")),
            "exchange": str(profile.get("exchangeShortName", profile.get("exchange", ""))),
            "assetType": str(profile.get("assetType", profile.get("type", "Equity"))),
            "isEtf": str(profile.get("isEtf", False)),
        }

    def fetch_average_daily_dollar_volume(self, ticker: str, start_date: date, end_date: date) -> float:
        history_df = self.fetch_history(ticker, start_date=start_date, end_date=end_date)
        price_column = "adjClose" if "adjClose" in history_df.columns else "close"
        if "volume" not in history_df.columns:
            raise ValueError(f"FMP payload missing volume field for {ticker}")
        dollar_volume = history_df[price_column].astype(float) * history_df["volume"].astype(float)
        return float(max(dollar_volume.mean(), 0.0))


def _build_fmp_provider(api_key: str) -> FMPMarketDataProvider:
    return FMPMarketDataProvider(FMPProviderConfig(api_key=api_key))


def _normalize_lot_metadata_token(value: Optional[object]) -> str:
    if value is None:
        return ""

    cleaned = []
    previous_was_separator = False
    for character in str(value).strip().lower():
        if character.isalnum():
            cleaned.append(character)
            previous_was_separator = False
        elif not previous_was_separator:
            cleaned.append("_")
            previous_was_separator = True
    return "_".join(part for part in "".join(cleaned).split("_") if part)


def _load_lot_metadata_config() -> dict:
    global _lot_metadata_cache

    if _lot_metadata_cache is not None:
        return _lot_metadata_cache

    default_config = {
        "defaults": {
            "fallback": {"lot_size": 1},
            "asset_types": {},
        },
        "tickers": {},
    }

    try:
        with LOT_METADATA_PATH.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        if not isinstance(payload, dict):
            payload = {}
    except FileNotFoundError:
        logger.warning("Lot metadata file not found at %s; using in-code defaults", LOT_METADATA_PATH)
        payload = {}

    defaults = payload.get("defaults", {}) if isinstance(payload.get("defaults", {}), dict) else {}
    tickers = payload.get("tickers", {}) if isinstance(payload.get("tickers", {}), dict) else {}
    _lot_metadata_cache = {
        "defaults": {
            "fallback": defaults.get("fallback", default_config["defaults"]["fallback"]),
            "asset_types": defaults.get("asset_types", default_config["defaults"]["asset_types"]),
        },
        "tickers": {str(ticker).upper().strip(): values for ticker, values in tickers.items() if isinstance(values, dict)},
    }
    return _lot_metadata_cache


def _resolve_asset_type_bucket(metadata: Optional[Dict[str, object]]) -> str:
    if not metadata:
        return ""
    if str(metadata.get("isEtf", "")).strip().lower() in {"1", "true", "t", "yes", "y"}:
        return "etf"
    return _normalize_lot_metadata_token(metadata.get("assetType"))


def resolve_lot_configuration(
    tickers: List[str],
    market_metadata: Optional[Dict[str, Dict[str, object]]] = None,
    requested_lot_sizes: Optional[Dict[str, int]] = None,
    requested_minimum_lot_units: Optional[Dict[str, int]] = None,
    requested_maximum_lot_units: Optional[Dict[str, int]] = None,
) -> Dict[str, Dict[str, int]]:
    config = _load_lot_metadata_config()
    fallback_defaults = config["defaults"].get("fallback", {})
    asset_type_defaults = config["defaults"].get("asset_types", {})
    ticker_defaults = config.get("tickers", {})

    normalized_requested_lot_sizes = {str(ticker).upper().strip(): int(value) for ticker, value in (requested_lot_sizes or {}).items()}
    normalized_requested_minimums = {str(ticker).upper().strip(): int(value) for ticker, value in (requested_minimum_lot_units or {}).items()}
    normalized_requested_maximums = {str(ticker).upper().strip(): int(value) for ticker, value in (requested_maximum_lot_units or {}).items()}

    resolved_lot_sizes: Dict[str, int] = {}
    resolved_minimums: Dict[str, int] = {}
    resolved_maximums: Dict[str, int] = {}

    for raw_ticker in tickers:
        ticker = str(raw_ticker).upper().strip()
        metadata = (market_metadata or {}).get(ticker, {})
        asset_type_bucket = _resolve_asset_type_bucket(metadata)

        resolved_defaults = dict(fallback_defaults)
        resolved_defaults.update(asset_type_defaults.get(asset_type_bucket, {}))
        resolved_defaults.update(ticker_defaults.get(ticker, {}))

        lot_size = normalized_requested_lot_sizes.get(ticker, resolved_defaults.get("lot_size", 1))
        resolved_lot_sizes[ticker] = max(int(lot_size), 1)

        minimum_lot_units = normalized_requested_minimums.get(ticker, resolved_defaults.get("minimum_lot_units"))
        if minimum_lot_units is not None and int(minimum_lot_units) > 0:
            resolved_minimums[ticker] = int(minimum_lot_units)

        maximum_lot_units = normalized_requested_maximums.get(ticker, resolved_defaults.get("maximum_lot_units"))
        if maximum_lot_units is not None and int(maximum_lot_units) > 0:
            resolved_maximums[ticker] = int(maximum_lot_units)

    return {
        "lot_sizes": resolved_lot_sizes,
        "minimum_lot_units": resolved_minimums,
        "maximum_lot_units": resolved_maximums,
    }


def _align_and_clean_prices(price_series: List[pd.Series]) -> pd.DataFrame:
    prices_df = pd.concat(price_series, axis=1)
    prices_df = prices_df.dropna(axis=1, thresh=max(2, int(0.8 * len(prices_df))))
    prices_df = prices_df.sort_index().ffill().dropna()
    if prices_df.empty or len(prices_df.columns) < 2:
        raise ValueError("Insufficient FMP price data after cleaning")
    return prices_df


def get_fmp_api_secret() -> Optional[KeyVaultSecret]:
    """Retrieve the FMP API secret from Azure Key Vault with in-process caching."""
    global _fmp_secret_cache

    if _fmp_secret_cache is not None:
        logger.info("Using cached FMP API secret")
        return _fmp_secret_cache

    try:
        credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
        vault_url = f"https://{AZURE_KEYVAULT_NAME}.vault.azure.net"
        client = SecretClient(vault_url=vault_url, credential=credential)
        secret = client.get_secret(FMP_API_SECRET_NAME)
        _fmp_secret_cache = secret
        logger.info("Retrieved FMP API secret from Azure Key Vault")
        return secret
    except Exception as exc:
        logger.error("Failed to retrieve FMP API secret: %s", exc)
        return None


def get_fmp_api_key() -> Optional[str]:
    """Return the FMP API key value from Azure Key Vault if available."""
    secret = get_fmp_api_secret()
    if secret is None:
        return None
    return secret.value


def _fetch_fmp_prices(
    ticker: str,
    start_date: date,
    end_date: date,
    api_key: str,
) -> pd.Series:
    """Fetch adjusted close prices for a single ticker from FMP."""
    provider = _build_fmp_provider(api_key)
    return provider.fetch_price_series(ticker, start_date=start_date, end_date=end_date)


def _fetch_fmp_history(
    ticker: str,
    start_date: date,
    end_date: date,
    api_key: str,
) -> pd.DataFrame:
    provider = _build_fmp_provider(api_key)
    return provider.fetch_history(ticker, start_date=start_date, end_date=end_date)


def _fetch_fmp_average_daily_dollar_volume(
    ticker: str,
    start_date: date,
    end_date: date,
    api_key: str,
) -> float:
    provider = _build_fmp_provider(api_key)
    return provider.fetch_average_daily_dollar_volume(ticker, start_date=start_date, end_date=end_date)


def _fetch_fmp_market_data(
    tickers: List[str],
    period_months: int,
    return_estimator: str = "sample",
    covariance_estimator: str = "sample",
    mean_shrinkage: float = 0.0,
    covariance_shrinkage: float = 0.0,
    estimator_decay: float = 0.94,
) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray]:
    """Fetch aligned historical prices from FMP and derive annualized returns and covariance."""
    api_key = get_fmp_api_key()
    if not api_key:
        raise MissingFMPAPIKeyError(
            "FMP API key is unavailable. Azure Key Vault secret retrieval must succeed before market data can be fetched."
        )

    provider = _build_fmp_provider(api_key)

    end_date = pd.Timestamp.today().date()
    start_date = (pd.Timestamp.today() - pd.DateOffset(months=period_months)).date()

    price_series = []
    for ticker in tickers:
        price_series.append(provider.fetch_price_series(ticker, start_date=start_date, end_date=end_date))

    prices_df = _align_and_clean_prices(price_series)

    estimated = estimate_market_inputs(
        prices_df,
        api_key=api_key,
        return_estimator=return_estimator,
        covariance_estimator=covariance_estimator,
        mean_shrinkage=mean_shrinkage,
        covariance_shrinkage=covariance_shrinkage,
        estimator_decay=estimator_decay,
    )

    logger.info("Successfully fetched FMP data for %s over %s days", list(prices_df.columns), len(prices_df))
    return prices_df, estimated.returns_df, estimated.mu, estimated.sigma_matrix


def get_market_metadata(
    tickers: Optional[List[str]] = None,
) -> Dict[str, Dict[str, str]]:
    """Fetch company profile metadata for tickers from FMP."""
    if tickers is None:
        tickers = DEFAULT_TICKERS

    tickers = [t.upper().strip() for t in tickers]
    api_key = get_fmp_api_key()
    if not api_key:
        raise MissingFMPAPIKeyError(
            "FMP API key is unavailable. Azure Key Vault secret retrieval must succeed before metadata can be fetched."
        )

    provider = _build_fmp_provider(api_key)

    metadata: Dict[str, Dict[str, str]] = {}
    for ticker in tickers:
        metadata[ticker] = provider.fetch_metadata(ticker)

    return metadata


def get_market_liquidity(
    tickers: Optional[List[str]] = None,
    period_months: int = 36,
) -> Dict[str, float]:
    """Fetch average daily dollar volume for each ticker using the historical FMP endpoint."""
    if tickers is None:
        tickers = DEFAULT_TICKERS

    tickers = [t.upper().strip() for t in tickers]
    api_key = get_fmp_api_key()
    if not api_key:
        raise MissingFMPAPIKeyError(
            "FMP API key is unavailable. Azure Key Vault secret retrieval must succeed before liquidity can be fetched."
        )

    provider = _build_fmp_provider(api_key)

    end_date = pd.Timestamp.today().date()
    start_date = (pd.Timestamp.today() - pd.DateOffset(months=period_months)).date()

    liquidity: Dict[str, float] = {}
    for ticker in tickers:
        liquidity[ticker] = provider.fetch_average_daily_dollar_volume(ticker, start_date=start_date, end_date=end_date)
    return liquidity


def _generate_synthetic_data(
    tickers: List[str],
    n_days: int = 756,
    return_estimator: str = "sample",
    covariance_estimator: str = "sample",
    mean_shrinkage: float = 0.0,
    covariance_shrinkage: float = 0.0,
    estimator_decay: float = 0.94,
) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray]:
    """Generate synthetic price data using geometric Brownian motion."""
    np.random.seed(42)
    n = len(tickers)

    # Realistic annual returns and volatilities per asset type
    annual_returns = []
    annual_vols = []
    for t in tickers:
        t_upper = t.upper()
        if t_upper in ["IEF", "TLT", "BND"]:
            annual_returns.append(np.random.uniform(0.02, 0.04))
            annual_vols.append(np.random.uniform(0.05, 0.08))
        elif t_upper in ["GLD", "SLV", "GDX"]:
            annual_returns.append(np.random.uniform(0.04, 0.07))
            annual_vols.append(np.random.uniform(0.12, 0.18))
        elif t_upper in ["SPY", "QQQ", "VTI", "IWM"]:
            annual_returns.append(np.random.uniform(0.07, 0.11))
            annual_vols.append(np.random.uniform(0.14, 0.20))
        elif t_upper in ["VNQ", "IYR"]:
            annual_returns.append(np.random.uniform(0.06, 0.10))
            annual_vols.append(np.random.uniform(0.16, 0.22))
        else:
            # Individual stocks
            annual_returns.append(np.random.uniform(0.08, 0.18))
            annual_vols.append(np.random.uniform(0.18, 0.35))

    annual_returns = np.array(annual_returns)
    annual_vols = np.array(annual_vols)

    # Daily params
    daily_returns = annual_returns / 252
    daily_vols = annual_vols / np.sqrt(252)

    # Build a realistic correlation matrix
    corr = np.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            ti, tj = tickers[i].upper(), tickers[j].upper()
            bond_like = {"IEF", "TLT", "BND"}
            gold_like = {"GLD", "SLV", "GDX"}
            if ti in bond_like or tj in bond_like:
                c = np.random.uniform(-0.1, 0.2)
            elif ti in gold_like or tj in gold_like:
                c = np.random.uniform(0.0, 0.2)
            else:
                c = np.random.uniform(0.3, 0.75)
            corr[i, j] = c
            corr[j, i] = c

    # Make positive definite
    eigvals = np.linalg.eigvalsh(corr)
    if eigvals.min() < 1e-8:
        corr += (abs(eigvals.min()) + 1e-6) * np.eye(n)
        d = np.sqrt(np.diag(corr))
        corr = corr / np.outer(d, d)

    daily_cov = np.outer(daily_vols, daily_vols) * corr

    # Cholesky decomposition for correlated returns
    try:
        L = np.linalg.cholesky(daily_cov)
    except np.linalg.LinAlgError:
        daily_cov += 1e-8 * np.eye(n)
        L = np.linalg.cholesky(daily_cov)

    # Generate price paths
    z = np.random.standard_normal((n_days, n))
    correlated_z = z @ L.T
    daily_log_returns = daily_returns - 0.5 * daily_vols**2 + correlated_z

    # Build price DataFrame starting at 100
    prices = np.ones((n_days + 1, n)) * 100.0
    for t in range(n_days):
        prices[t + 1] = prices[t] * np.exp(daily_log_returns[t])

    start_date = pd.Timestamp.today().normalize() - pd.offsets.BDay(n_days)
    dates = pd.bdate_range(start=start_date, periods=n_days + 1)
    prices_df = pd.DataFrame(prices, index=dates, columns=tickers)
    estimated = estimate_market_inputs(
        prices_df,
        return_estimator=return_estimator,
        covariance_estimator=covariance_estimator,
        mean_shrinkage=mean_shrinkage,
        covariance_shrinkage=covariance_shrinkage,
        estimator_decay=estimator_decay,
    )

    return prices_df, estimated.returns_df, estimated.mu, estimated.sigma_matrix


def get_market_data(
    tickers: Optional[List[str]] = None,
    period_months: int = 36,
    return_estimator: str = "sample",
    covariance_estimator: str = "sample",
    mean_shrinkage: float = 0.0,
    covariance_shrinkage: float = 0.0,
    estimator_decay: float = 0.94,
) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray]:
    """
    Fetch market data from FMP using an Azure Key Vault-backed API key,
    raising loudly if the API key is unavailable and falling back to synthetic data
    only for non-authentication fetch failures.
    Returns (prices_df, returns_df, mu, sigma_matrix) where mu and sigma_matrix are annualized.
    """
    if tickers is None:
        tickers = DEFAULT_TICKERS

    tickers = [t.upper().strip() for t in tickers]

    try:
        return _fetch_fmp_market_data(
            tickers=tickers,
            period_months=period_months,
            return_estimator=return_estimator,
            covariance_estimator=covariance_estimator,
            mean_shrinkage=mean_shrinkage,
            covariance_shrinkage=covariance_shrinkage,
            estimator_decay=estimator_decay,
        )
    except MissingFMPAPIKeyError:
        raise
    except Exception as e:
        logger.warning(f"FMP fetch failed ({e}), using synthetic data for tickers: {tickers}")
        n_days = max(252 * 2, period_months * 21)
        return _generate_synthetic_data(
            tickers,
            n_days=n_days,
            return_estimator=return_estimator,
            covariance_estimator=covariance_estimator,
            mean_shrinkage=mean_shrinkage,
            covariance_shrinkage=covariance_shrinkage,
            estimator_decay=estimator_decay,
        )
