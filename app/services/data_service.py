import numpy as np
import pandas as pd
from typing import List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

DEFAULT_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META",
    "TSLA", "JPM", "JNJ", "PG", "KO",
    "SPY", "QQQ", "IEF", "GLD", "VNQ"
]


def _generate_synthetic_data(tickers: List[str], n_days: int = 756) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray]:
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

    dates = pd.bdate_range(end=pd.Timestamp.today(), periods=n_days + 1)
    prices_df = pd.DataFrame(prices, index=dates, columns=tickers)
    returns_df = prices_df.pct_change().dropna()

    mu = returns_df.mean().values * 252
    sigma_matrix = returns_df.cov().values * 252

    return prices_df, returns_df, mu, sigma_matrix


def get_market_data(
    tickers: Optional[List[str]] = None,
    period_months: int = 36
) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray]:
    """
    Fetch market data from yfinance, falling back to synthetic data on failure.
    Returns (prices_df, returns_df, mu, sigma_matrix) where mu and sigma_matrix are annualized.
    """
    if tickers is None:
        tickers = DEFAULT_TICKERS

    tickers = [t.upper().strip() for t in tickers]

    try:
        import yfinance as yf
        period_str = f"{period_months}mo"
        data = yf.download(tickers, period=period_str, auto_adjust=True, progress=False)

        if data.empty:
            raise ValueError("yfinance returned empty data")

        # Handle single vs multi-ticker
        if len(tickers) == 1:
            prices_df = data[["Close"]].copy()
            prices_df.columns = tickers
        else:
            if "Close" in data.columns.get_level_values(0):
                prices_df = data["Close"].copy()
            else:
                prices_df = data.copy()

        # Drop tickers with insufficient data
        prices_df = prices_df.dropna(axis=1, thresh=int(0.8 * len(prices_df)))
        prices_df = prices_df.ffill().dropna()

        if prices_df.empty or len(prices_df.columns) < 2:
            raise ValueError("Insufficient price data after cleaning")

        returns_df = prices_df.pct_change().dropna()
        mu = returns_df.mean().values * 252
        sigma_matrix = returns_df.cov().values * 252

        # Ensure positive definiteness
        eigvals = np.linalg.eigvalsh(sigma_matrix)
        if eigvals.min() < 1e-8:
            sigma_matrix += (abs(eigvals.min()) + 1e-6) * np.eye(len(sigma_matrix))

        logger.info(f"Successfully fetched data for {list(prices_df.columns)} over {len(prices_df)} days")
        return prices_df, returns_df, mu, sigma_matrix

    except Exception as e:
        logger.warning(f"yfinance failed ({e}), using synthetic data for tickers: {tickers}")
        n_days = max(252 * 2, period_months * 21)
        return _generate_synthetic_data(tickers, n_days=n_days)
