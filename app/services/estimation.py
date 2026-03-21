import logging
from dataclasses import dataclass, field
from typing import Dict, Type

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class EstimatedMarketData:
    returns_df: pd.DataFrame
    mu: np.ndarray
    sigma_matrix: np.ndarray
    toolkit_risk_metrics: Dict[str, pd.Series] = field(default_factory=dict)


def _ensure_positive_definite(matrix: np.ndarray) -> np.ndarray:
    eigvals = np.linalg.eigvalsh(matrix)
    if eigvals.min() < 1e-8:
        matrix = matrix + (abs(eigvals.min()) + 1e-6) * np.eye(len(matrix))
    return matrix


def _extract_latest_metric_series(metric_output: pd.DataFrame | pd.Series) -> pd.Series:
    if isinstance(metric_output, pd.Series):
        return metric_output
    if metric_output.empty:
        return pd.Series(dtype=float)
    return metric_output.iloc[-1]


def get_toolkit_class() -> Type:
    from financetoolkit import Toolkit

    return Toolkit


def estimate_market_inputs(
    prices_df: pd.DataFrame,
    api_key: str | None = None,
) -> EstimatedMarketData:
    """Estimate annualized return and covariance from prices and collect FinanceToolkit risk diagnostics when an API key is available."""
    returns_df = prices_df.pct_change().dropna()
    mu = returns_df.mean().to_numpy() * 252
    sigma_matrix = returns_df.cov().to_numpy() * 252
    sigma_matrix = _ensure_positive_definite(sigma_matrix)

    toolkit_risk_metrics: Dict[str, pd.Series] = {}

    if api_key:
        try:
            toolkit_class = get_toolkit_class()
            toolkit = toolkit_class(
                tickers=list(prices_df.columns),
                benchmark_ticker=None,
                start_date=prices_df.index.min().strftime("%Y-%m-%d"),
                end_date=prices_df.index.max().strftime("%Y-%m-%d"),
                sleep_timer=False,
                api_key=api_key,
            )

            toolkit_risk_metrics["daily_value_at_risk"] = _extract_latest_metric_series(
                toolkit.risk.get_value_at_risk(period="daily")
            )
            toolkit_risk_metrics["daily_maximum_drawdown"] = _extract_latest_metric_series(
                toolkit.risk.get_maximum_drawdown(period="daily")
            )
        except Exception as exc:
            logger.warning("FinanceToolkit risk diagnostics unavailable: %s", exc)

    return EstimatedMarketData(
        returns_df=returns_df,
        mu=mu,
        sigma_matrix=sigma_matrix,
        toolkit_risk_metrics=toolkit_risk_metrics,
    )