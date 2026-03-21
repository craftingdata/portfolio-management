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


def _exponential_weights(n_observations: int, decay: float) -> np.ndarray:
    if n_observations <= 0:
        raise ValueError("n_observations must be positive")
    clipped_decay = float(min(max(decay, 1e-6), 0.9999))
    powers = np.arange(n_observations - 1, -1, -1, dtype=float)
    weights = (1.0 - clipped_decay) * np.power(clipped_decay, powers)
    return weights / float(np.sum(weights))


def _estimate_expected_returns(
    returns_df: pd.DataFrame,
    method: str,
    mean_shrinkage: float,
    estimator_decay: float,
) -> np.ndarray:
    sample_mean = returns_df.mean().to_numpy(dtype=float) * 252
    if method == "sample":
        return sample_mean
    if method == "shrunk_mean":
        grand_mean = float(np.mean(sample_mean))
        return (1.0 - mean_shrinkage) * sample_mean + mean_shrinkage * grand_mean
    if method == "ewma_mean":
        weights = _exponential_weights(len(returns_df), estimator_decay)
        return np.average(returns_df.to_numpy(dtype=float), axis=0, weights=weights) * 252
    raise ValueError(f"Unsupported return estimator: {method}")


def _estimate_covariance_matrix(
    returns_df: pd.DataFrame,
    method: str,
    covariance_shrinkage: float,
    estimator_decay: float,
) -> np.ndarray:
    sample_covariance = returns_df.cov().to_numpy(dtype=float) * 252
    if method == "sample":
        return sample_covariance
    if method == "diagonal_shrinkage":
        diagonal_target = np.diag(np.diag(sample_covariance))
        return (1.0 - covariance_shrinkage) * sample_covariance + covariance_shrinkage * diagonal_target
    if method == "ewma":
        observations = returns_df.to_numpy(dtype=float)
        weights = _exponential_weights(len(returns_df), estimator_decay)
        weighted_mean = np.average(observations, axis=0, weights=weights)
        centered = observations - weighted_mean
        normalization = float(max(1e-8, 1.0 - np.sum(weights**2)))
        weighted_covariance = (centered * weights[:, None]).T @ centered / normalization
        return weighted_covariance * 252
    raise ValueError(f"Unsupported covariance estimator: {method}")


def get_toolkit_class() -> Type:
    from financetoolkit import Toolkit

    return Toolkit


def estimate_market_inputs(
    prices_df: pd.DataFrame,
    api_key: str | None = None,
    return_estimator: str = "sample",
    covariance_estimator: str = "sample",
    mean_shrinkage: float = 0.0,
    covariance_shrinkage: float = 0.0,
    estimator_decay: float = 0.94,
) -> EstimatedMarketData:
    """Estimate annualized return and covariance from prices and collect FinanceToolkit risk diagnostics when an API key is available."""
    if prices_df.shape[0] < 3:
        raise ValueError("At least three price observations are required to estimate market inputs")

    returns_df = prices_df.pct_change().dropna()
    if returns_df.shape[0] < 2:
        raise ValueError("At least two return observations are required to estimate market inputs")

    mu = _estimate_expected_returns(
        returns_df,
        method=return_estimator,
        mean_shrinkage=float(mean_shrinkage),
        estimator_decay=float(estimator_decay),
    )
    sigma_matrix = _estimate_covariance_matrix(
        returns_df,
        method=covariance_estimator,
        covariance_shrinkage=float(covariance_shrinkage),
        estimator_decay=float(estimator_decay),
    )
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