import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

DEFAULT_TRANSACTION_COST_MODEL = "interactive_brokers_fixed"
DEFAULT_TRANSACTION_COST_RATE = 0.001
DEFAULT_MARKET_IMPACT_COEFFICIENT = 0.025
DEFAULT_IMPACT_ADV_FLOOR = 5_000_000.0
SECTOR_ALIAS_MAP = {
    "basic_materials": "materials",
    "communication": "communication_services",
    "communications": "communication_services",
    "communications_services": "communication_services",
    "consumer_cyclical": "consumer_discretionary",
    "consumer_defensive": "consumer_staples",
    "financial_services": "financials",
    "healthcare": "health_care",
    "information_technology": "technology",
    "realestate": "real_estate",
    "real_estate_services": "real_estate",
    "telecom": "communication_services",
    "telecommunication_services": "communication_services",
}


@dataclass
class FactorModelData:
    factor_names: List[str]
    exposure_matrix: np.ndarray
    factor_covariance: np.ndarray
    specific_variance: np.ndarray
    implied_covariance: np.ndarray


def compute_metrics(weights: np.ndarray, mu: np.ndarray, sigma: np.ndarray, risk_free_rate: float = 0.04):
    weights = np.array(weights)
    expected_return = float(weights @ mu)
    variance = float(weights @ sigma @ weights)
    expected_risk = float(np.sqrt(max(variance, 1e-10)))
    sharpe_ratio = float((expected_return - risk_free_rate) / expected_risk) if expected_risk > 1e-10 else 0.0
    return expected_return, expected_risk, sharpe_ratio


def _ensure_positive_semidefinite(matrix: np.ndarray) -> np.ndarray:
    eigvals = np.linalg.eigvalsh(matrix)
    if eigvals.min() < 1e-8:
        matrix = matrix + (abs(eigvals.min()) + 1e-6) * np.eye(len(matrix))
    return matrix


def _normalize_weights(weights: np.ndarray) -> np.ndarray:
    weights = np.maximum(np.array(weights, dtype=float), 0.0)
    total = float(weights.sum())
    if total > 1e-8:
        return weights / total
    return np.ones(len(weights)) / len(weights)


def _normalize_affine_weights(weights: np.ndarray) -> np.ndarray:
    weights = np.array(weights, dtype=float)
    total = float(weights.sum())
    if abs(total) > 1e-8:
        return weights / total
    return weights


def _vector_from_current_weights(current_weights: Optional[Dict[str, float]], tickers: List[str]) -> np.ndarray:
    if not current_weights:
        return np.ones(len(tickers)) / len(tickers)

    weights = np.array([float(current_weights.get(ticker, 0.0)) for ticker in tickers], dtype=float)
    if np.allclose(weights.sum(), 0.0):
        return np.ones(len(tickers)) / len(tickers)
    return _normalize_weights(weights)


def _resolve_execution_penalties(
    tickers: List[str],
    transaction_cost_model: str,
    transaction_cost_rate: Optional[float],
    per_asset_transaction_costs: Optional[Dict[str, float]],
    market_impact_coefficient: Optional[float],
    per_asset_market_impact_coefficients: Optional[Dict[str, float]],
    average_daily_dollar_volume: Optional[Dict[str, float]],
    total_amount: float,
    impact_adv_floor: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if transaction_cost_model in {"interactive_brokers_fixed", "default"}:
        base_transaction_cost_rate = DEFAULT_TRANSACTION_COST_RATE if transaction_cost_rate is None else float(max(transaction_cost_rate, 0.0))
    else:
        base_transaction_cost_rate = float(max(transaction_cost_rate or 0.0, 0.0))

    transaction_cost_rates = np.full(len(tickers), base_transaction_cost_rate, dtype=float)
    if per_asset_transaction_costs:
        for index, ticker in enumerate(tickers):
            if ticker in per_asset_transaction_costs:
                transaction_cost_rates[index] = float(max(per_asset_transaction_costs[ticker], 0.0))

    base_market_impact = DEFAULT_MARKET_IMPACT_COEFFICIENT if market_impact_coefficient is None else float(max(market_impact_coefficient, 0.0))
    market_impact_rates = np.full(len(tickers), base_market_impact, dtype=float)
    if per_asset_market_impact_coefficients:
        for index, ticker in enumerate(tickers):
            if ticker in per_asset_market_impact_coefficients:
                market_impact_rates[index] = float(max(per_asset_market_impact_coefficients[ticker], 0.0))

    impact_penalties = np.zeros(len(tickers), dtype=float)
    if average_daily_dollar_volume:
        adv_floor = float(max(impact_adv_floor, 1.0))
        for index, ticker in enumerate(tickers):
            adv = float(max(float(average_daily_dollar_volume.get(ticker, adv_floor)), adv_floor))
            impact_penalties[index] = market_impact_rates[index] * (float(max(total_amount, 1e-8)) / adv)

    return transaction_cost_rates, market_impact_rates, transaction_cost_rates + impact_penalties


def _normalized_metadata_token(value: Optional[str]) -> str:
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


def _parse_boolish(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y"}


def _resolve_sector_from_industry(industry: Optional[str]) -> Optional[str]:
    normalized = _normalized_metadata_token(industry)
    if not normalized:
        return None

    keyword_to_sector = {
        "aerospace": "industrials",
        "asset_management": "financials",
        "bank": "financials",
        "biotech": "health_care",
        "capital_markets": "financials",
        "consumer_electronics": "technology",
        "drug": "health_care",
        "insurance": "financials",
        "internet": "communication_services",
        "media": "communication_services",
        "oil": "energy",
        "pharmaceutical": "health_care",
        "reit": "real_estate",
        "semiconductor": "technology",
        "software": "technology",
        "telecom": "communication_services",
    }
    for keyword, sector in keyword_to_sector.items():
        if keyword in normalized:
            return sector
    return None


def _metadata_indicates_etf(metadata: Optional[Dict[str, str]]) -> bool:
    if not metadata:
        return False

    if _parse_boolish(metadata.get("isEtf")):
        return True

    for key in ("assetType", "industry", "companyName", "sector"):
        normalized = _normalized_metadata_token(metadata.get(key))
        if normalized in {"etf", "exchange_traded_fund", "exchange_traded_product", "fund"}:
            return True
        if "exchange_traded_fund" in normalized:
            return True
    return False


def _normalized_sector_name(value: Optional[str]) -> str:
    normalized = _normalized_metadata_token(value)
    if not normalized or normalized in {"unknown", "none", "null", "n_a", "na", "other", "unclassified"}:
        return "unknown"
    return SECTOR_ALIAS_MAP.get(normalized, SECTOR_ALIAS_MAP.get(normalized.replace("_", ""), normalized))


def _resolve_sector_bucket(metadata: Optional[Dict[str, str]]) -> Optional[str]:
    if _metadata_indicates_etf(metadata):
        return None

    sector = _normalized_sector_name(metadata.get("sector") if metadata else None)
    if sector not in {"unknown", "etf"}:
        return sector

    inferred_sector = _resolve_sector_from_industry(metadata.get("industry") if metadata else None)
    if inferred_sector:
        return inferred_sector
    return None


def _scipy_min_variance(mu: np.ndarray, sigma: np.ndarray) -> np.ndarray:
    from scipy.optimize import minimize
    n = len(mu)
    x0 = np.ones(n) / n
    constraints = [{"type": "eq", "fun": lambda x: np.sum(x) - 1.0}]
    bounds = [(0.0, 1.0)] * n
    result = minimize(
        lambda x: float(x @ sigma @ x),
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"ftol": 1e-9, "maxiter": 1000},
    )
    return _normalize_weights(result.x)


def _scipy_utility_maximization(
    mu: np.ndarray,
    sigma: np.ndarray,
    risk_aversion: float,
    risk_free_rate: float,
) -> np.ndarray:
    from scipy.optimize import minimize

    n = len(mu)
    x0 = np.ones(n) / n

    def neg_utility(x):
        x = np.array(x)
        expected_return = float(mu @ x)
        variance = float(x @ sigma @ x)
        utility = expected_return - 0.5 * risk_aversion * variance
        return -utility

    constraints = [{"type": "eq", "fun": lambda x: np.sum(x) - 1.0}]
    bounds = [(0.0, 1.0)] * n
    result = minimize(
        neg_utility,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"ftol": 1e-9, "maxiter": 1000},
    )
    return _normalize_weights(result.x)


def minimum_variance(mu: np.ndarray, sigma: np.ndarray, risk_free_rate: float = 0.04) -> dict:
    n = len(mu)
    weights = None

    try:
        from pyscipopt import Model, quicksum
        model = Model()
        model.hideOutput()
        x = [model.addVar(lb=0.0, ub=1.0, vtype="C", name=f"x_{i}") for i in range(n)]
        # Quadratic objective: minimize x^T Sigma x
        obj = quicksum(sigma[i, j] * x[i] * x[j] for i in range(n) for j in range(n))
        model.setObjective(obj, "minimize")
        model.addCons(quicksum(x[i] for i in range(n)) == 1.0)
        model.optimize()
        if model.getStatus() == "optimal":
            weights = np.array([model.getVal(x[i]) for i in range(n)], dtype=float)
        else:
            raise ValueError(f"SCIP status: {model.getStatus()}")
    except Exception as e:
        logger.warning(f"MinimumVariance SCIP failed ({e}), falling back to scipy")
        weights = _scipy_min_variance(mu, sigma)

    expected_return, expected_risk, sharpe_ratio = compute_metrics(weights, mu, sigma, risk_free_rate)
    return {
        "model_name": "MinimumVariance",
        "weights": weights,
        "expected_return": expected_return,
        "expected_risk": expected_risk,
        "sharpe_ratio": sharpe_ratio,
    }


def maximum_return(mu: np.ndarray, sigma: np.ndarray, risk_level: float = 0.5, risk_free_rate: float = 0.04) -> dict:
    n = len(mu)
    asset_vols = np.sqrt(np.diag(sigma))
    avg_vol = np.mean(asset_vols)
    factor = 1.5 + risk_level * 0.5  # 1.5 to 2.0
    max_risk = avg_vol * factor
    max_risk_sq = max_risk ** 2

    weights = None

    try:
        from pyscipopt import Model, quicksum
        model = Model()
        model.hideOutput()
        x = [model.addVar(lb=0.0, ub=1.0, vtype="C", name=f"x_{i}") for i in range(n)]
        model.setObjective(quicksum(-mu[i] * x[i] for i in range(n)), "minimize")
        model.addCons(quicksum(x[i] for i in range(n)) == 1.0)
        quad_risk = quicksum(sigma[i, j] * x[i] * x[j] for i in range(n) for j in range(n))
        model.addCons(quad_risk <= max_risk_sq)
        model.optimize()
        if model.getStatus() == "optimal":
            weights = _normalize_weights([model.getVal(x[i]) for i in range(n)])
        else:
            raise ValueError(f"SCIP status: {model.getStatus()}")
    except Exception as e:
        logger.warning(f"MaximumReturn SCIP failed ({e}), falling back to scipy")
        from scipy.optimize import minimize
        x0 = np.ones(n) / n
        constraints = [
            {"type": "eq", "fun": lambda x: np.sum(x) - 1.0},
            {"type": "ineq", "fun": lambda x: max_risk_sq - float(x @ sigma @ x)},
        ]
        bounds = [(0.0, 1.0)] * n
        result = minimize(
            lambda x: -float(mu @ x),
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"ftol": 1e-9, "maxiter": 1000},
        )
        weights = _normalize_weights(result.x)

    expected_return, expected_risk, sharpe_ratio = compute_metrics(weights, mu, sigma, risk_free_rate)
    return {
        "model_name": "MaximumReturn",
        "weights": weights,
        "expected_return": expected_return,
        "expected_risk": expected_risk,
        "sharpe_ratio": sharpe_ratio,
    }


def utility_maximization(
    mu: np.ndarray,
    sigma: np.ndarray,
    risk_aversion: float = 1.0,
    risk_free_rate: float = 0.04,
) -> dict:
    n = len(mu)
    risk_aversion = float(max(risk_aversion, 1e-6))
    weights = None

    try:
        from pyscipopt import Model, quicksum

        model = Model()
        model.hideOutput()
        x = [model.addVar(lb=0.0, ub=1.0, vtype="C", name=f"x_{i}") for i in range(n)]
        utility = quicksum(mu[i] * x[i] for i in range(n)) - 0.5 * risk_aversion * quicksum(
            sigma[i, j] * x[i] * x[j] for i in range(n) for j in range(n)
        )
        model.setObjective(utility, "maximize")
        model.addCons(quicksum(x[i] for i in range(n)) == 1.0)
        model.optimize()
        if model.getStatus() == "optimal":
            weights = _normalize_weights([model.getVal(x[i]) for i in range(n)])
        else:
            raise ValueError(f"SCIP status: {model.getStatus()}")
    except Exception as e:
        logger.warning(f"UtilityMaximization SCIP failed ({e}), falling back to scipy")
        weights = _scipy_utility_maximization(mu, sigma, risk_aversion, risk_free_rate)

    expected_return, expected_risk, sharpe_ratio = compute_metrics(weights, mu, sigma, risk_free_rate)
    return {
        "model_name": "UtilityMaximization",
        "weights": weights,
        "expected_return": expected_return,
        "expected_risk": expected_risk,
        "sharpe_ratio": sharpe_ratio,
    }


def _scipy_short_selling(
    mu: np.ndarray,
    sigma: np.ndarray,
    risk_aversion: float,
    max_gross_exposure: float,
    max_short_exposure: float,
) -> np.ndarray:
    from scipy.optimize import minimize

    n = len(mu)
    x0 = np.ones(n) / n

    def neg_utility(x):
        x = np.array(x)
        expected_return = float(mu @ x)
        variance = float(x @ sigma @ x)
        return -(expected_return - 0.5 * risk_aversion * variance)

    constraints = [
        {"type": "eq", "fun": lambda x: np.sum(x) - 1.0},
        {"type": "ineq", "fun": lambda x: max_gross_exposure - float(np.sum(np.abs(x)))},
    ]
    bounds = [(-max_short_exposure, max_gross_exposure)] * n
    result = minimize(
        neg_utility,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"ftol": 1e-9, "maxiter": 2000},
    )
    return _normalize_affine_weights(result.x)


def leverage_short_selling(
    mu: np.ndarray,
    sigma: np.ndarray,
    risk_level: float = 0.5,
    max_gross_exposure: float = 1.5,
    max_short_exposure: float = 0.5,
    risk_free_rate: float = 0.04,
) -> dict:
    n = len(mu)
    max_gross_exposure = float(max(max_gross_exposure, 1.0))
    max_short_exposure = float(max(max_short_exposure, 0.0))
    risk_aversion = _risk_aversion_from_risk_level(risk_level)
    weights = None

    try:
        from pyscipopt import Model, quicksum

        model = Model()
        model.hideOutput()
        long_vars = [model.addVar(lb=0.0, ub=max_gross_exposure, vtype="C", name=f"long_{i}") for i in range(n)]
        short_vars = [model.addVar(lb=0.0, ub=max_short_exposure, vtype="C", name=f"short_{i}") for i in range(n)]

        gross_positions = quicksum(long_vars[i] + short_vars[i] for i in range(n))
        net_positions = quicksum(long_vars[i] - short_vars[i] for i in range(n))
        utility = quicksum(mu[i] * (long_vars[i] - short_vars[i]) for i in range(n)) - 0.5 * risk_aversion * quicksum(
            sigma[i, j] * (long_vars[i] - short_vars[i]) * (long_vars[j] - short_vars[j])
            for i in range(n)
            for j in range(n)
        )

        model.setObjective(utility, "maximize")
        model.addCons(net_positions == 1.0)
        model.addCons(gross_positions <= max_gross_exposure)
        model.optimize()

        if model.getStatus() == "optimal":
            weights = np.array([model.getVal(long_vars[i]) - model.getVal(short_vars[i]) for i in range(n)], dtype=float)
        else:
            raise ValueError(f"SCIP status: {model.getStatus()}")
    except Exception as e:
        logger.warning(f"LeverageShortSelling SCIP failed ({e}), falling back to scipy")
        weights = _scipy_short_selling(mu, sigma, risk_aversion, max_gross_exposure, max_short_exposure)

    expected_return, expected_risk, sharpe_ratio = compute_metrics(weights, mu, sigma, risk_free_rate)
    return {
        "model_name": "LeverageShortSelling",
        "weights": weights,
        "expected_return": expected_return,
        "expected_risk": expected_risk,
        "sharpe_ratio": sharpe_ratio,
    }


def _scipy_borrowing_cash(
    mu: np.ndarray,
    sigma: np.ndarray,
    risk_aversion: float,
    max_cash_borrow: float,
    borrow_rate: float,
    risk_free_rate: float,
) -> tuple[np.ndarray, float]:
    from scipy.optimize import minimize

    n = len(mu)
    x0 = np.ones(n) / n

    def neg_utility(x):
        x = np.array(x)
        cash_weight = 1.0 - float(np.sum(x))
        cash_return = risk_free_rate if cash_weight >= 0 else -borrow_rate
        expected_return = float(mu @ x) + cash_weight * cash_return
        variance = float(x @ sigma @ x)
        return -(expected_return - 0.5 * risk_aversion * variance)

    constraints = [
        {"type": "ineq", "fun": lambda x: 1.0 + max_cash_borrow - float(np.sum(x))},
        {"type": "ineq", "fun": lambda x: float(np.sum(x)) - (1.0 - max_cash_borrow)},
    ]
    bounds = [(0.0, 1.0 + max_cash_borrow)] * n
    result = minimize(
        neg_utility,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"ftol": 1e-9, "maxiter": 2000},
    )
    asset_weights = np.maximum(result.x, 0.0)
    cash_weight = 1.0 - float(asset_weights.sum())
    return np.array(asset_weights, dtype=float), cash_weight


def leverage_borrowing(
    mu: np.ndarray,
    sigma: np.ndarray,
    risk_level: float = 0.5,
    max_cash_borrow: float = 0.25,
    borrow_rate: float = 0.06,
    risk_free_rate: float = 0.04,
) -> dict:
    n = len(mu)
    max_cash_borrow = float(max(max_cash_borrow, 0.0))
    borrow_rate = float(max(borrow_rate, risk_free_rate))
    risk_aversion = _risk_aversion_from_risk_level(risk_level)
    weights = None
    cash_weight = None

    try:
        from pyscipopt import Model, quicksum

        model = Model()
        model.hideOutput()
        x = [model.addVar(lb=0.0, ub=1.0 + max_cash_borrow, vtype="C", name=f"x_{i}") for i in range(n)]
        cash_lend = model.addVar(lb=0.0, ub=1.0, vtype="C", name="cash_lend")
        cash_borrow = model.addVar(lb=0.0, ub=max_cash_borrow, vtype="C", name="cash_borrow")

        utility = quicksum(mu[i] * x[i] for i in range(n)) + risk_free_rate * cash_lend - borrow_rate * cash_borrow - 0.5 * risk_aversion * quicksum(
            sigma[i, j] * x[i] * x[j] for i in range(n) for j in range(n)
        )

        model.setObjective(utility, "maximize")
        model.addCons(quicksum(x[i] for i in range(n)) + cash_lend - cash_borrow == 1.0)
        model.optimize()

        if model.getStatus() == "optimal":
            weights = _normalize_weights([model.getVal(x[i]) for i in range(n)])
            cash_weight = float(model.getVal(cash_lend) - model.getVal(cash_borrow))
        else:
            raise ValueError(f"SCIP status: {model.getStatus()}")
    except Exception as e:
        logger.warning(f"LeverageBorrowing SCIP failed ({e}), falling back to scipy")
        weights, cash_weight = _scipy_borrowing_cash(
            mu,
            sigma,
            risk_aversion,
            max_cash_borrow,
            borrow_rate,
            risk_free_rate,
        )

    expected_return, expected_risk, _ = compute_metrics(weights, mu, sigma, risk_free_rate)
    cash_return = cash_weight * (risk_free_rate if cash_weight >= 0 else -borrow_rate)
    expected_return = expected_return + cash_return
    sharpe_ratio = float((expected_return - risk_free_rate) / expected_risk) if expected_risk > 1e-10 else 0.0
    return {
        "model_name": "LeverageBorrowing",
        "weights": weights,
        "cash_weight": cash_weight,
        "expected_return": expected_return,
        "expected_risk": expected_risk,
        "sharpe_ratio": sharpe_ratio,
    }


def _scipy_turnover_constrained(
    mu: np.ndarray,
    sigma: np.ndarray,
    current_weights: np.ndarray,
    risk_level: float,
    max_turnover: float,
    risk_free_rate: float,
) -> np.ndarray:
    from scipy.optimize import minimize

    n = len(mu)
    x0 = np.array(current_weights, dtype=float)
    target_return = float(np.min(mu) + (np.max(mu) - np.min(mu)) * risk_level)

    constraints = [
        {"type": "eq", "fun": lambda x: np.sum(x) - 1.0},
        {"type": "ineq", "fun": lambda x: float(mu @ x) - target_return},
        {"type": "ineq", "fun": lambda x: max_turnover - float(np.sum(np.abs(x - current_weights)))},
    ]
    bounds = [(0.0, 1.0)] * n
    result = minimize(
        lambda x: float(x @ sigma @ x),
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"ftol": 1e-9, "maxiter": 2000},
    )
    return _normalize_weights(result.x)


def turnover_constrained_mean_variance(
    mu: np.ndarray,
    sigma: np.ndarray,
    current_weights: Optional[np.ndarray] = None,
    risk_level: float = 0.5,
    max_turnover: float = 0.25,
    risk_free_rate: float = 0.04,
) -> dict:
    n = len(mu)
    max_turnover = float(max(max_turnover, 0.0))
    current_vector = _normalize_weights(np.ones(n) / n if current_weights is None else np.array(current_weights, dtype=float))
    weights = None

    try:
        from pyscipopt import Model, quicksum

        target_return = float(np.min(mu) + (np.max(mu) - np.min(mu)) * risk_level)

        model = Model()
        model.hideOutput()
        x = [model.addVar(lb=0.0, ub=1.0, vtype="C", name=f"x_{i}") for i in range(n)]
        turnover = [model.addVar(lb=0.0, ub=1.0, vtype="C", name=f"turnover_{i}") for i in range(n)]

        model.setObjective(quicksum(sigma[i, j] * x[i] * x[j] for i in range(n) for j in range(n)), "minimize")
        model.addCons(quicksum(x[i] for i in range(n)) == 1.0)
        model.addCons(quicksum(mu[i] * x[i] for i in range(n)) >= target_return)
        model.addCons(quicksum(turnover[i] for i in range(n)) <= max_turnover)

        for i in range(n):
            model.addCons(turnover[i] >= x[i] - current_vector[i])
            model.addCons(turnover[i] >= current_vector[i] - x[i])

        model.optimize()
        if model.getStatus() == "optimal":
            weights = _normalize_weights([model.getVal(x[i]) for i in range(n)])
        else:
            raise ValueError(f"SCIP status: {model.getStatus()}")
    except Exception as e:
        logger.warning(f"TurnoverConstrained SCIP failed ({e}), falling back to scipy")
        weights = _scipy_turnover_constrained(mu, sigma, current_vector, risk_level, max_turnover, risk_free_rate)

    expected_return, expected_risk, sharpe_ratio = compute_metrics(weights, mu, sigma, risk_free_rate)
    turnover_amount = float(np.sum(np.abs(weights - current_vector)))
    return {
        "model_name": "TurnoverConstrained",
        "weights": weights,
        "expected_return": expected_return,
        "expected_risk": expected_risk,
        "sharpe_ratio": sharpe_ratio,
        "turnover": turnover_amount,
    }


def max_sharpe_ratio(mu: np.ndarray, sigma: np.ndarray, risk_free_rate: float = 0.04) -> dict:
    n = len(mu)

    min_var_weights = _scipy_min_variance(mu, sigma)
    min_risk = float(np.sqrt(min_var_weights @ sigma @ min_var_weights))
    max_risk = float(np.sqrt(np.diag(sigma)).max()) * 1.2

    best_weights = None
    best_sharpe = -np.inf

    try:
        from pyscipopt import Model, quicksum
        risk_targets = np.linspace(min_risk, max_risk, 20)
        for sigma_target in risk_targets:
            try:
                model = Model()
                model.hideOutput()
                x = [model.addVar(lb=0.0, ub=1.0, vtype="C", name=f"x_{i}") for i in range(n)]
                model.setObjective(quicksum(-mu[i] * x[i] for i in range(n)), "minimize")
                model.addCons(quicksum(x[i] for i in range(n)) == 1.0)
                quad_risk = quicksum(sigma[i, j] * x[i] * x[j] for i in range(n) for j in range(n))
                model.addCons(quad_risk <= sigma_target ** 2)
                model.optimize()
                if model.getStatus() == "optimal":
                    w = np.array([model.getVal(x[i]) for i in range(n)])
                    w = np.maximum(w, 0)
                    s = w.sum()
                    if s > 1e-8:
                        w = w / s
                        _, _, sr = compute_metrics(w, mu, sigma, risk_free_rate)
                        if sr > best_sharpe:
                            best_sharpe = sr
                            best_weights = w
            except Exception:
                continue
    except Exception as e:
        logger.warning(f"MaxSharpeRatio SCIP failed ({e})")

    # Also try scipy directly as fallback or to improve
    try:
        from scipy.optimize import minimize
        x0 = np.ones(n) / n

        def neg_sharpe(w):
            w = np.array(w)
            ret = float(w @ mu)
            var = float(w @ sigma @ w)
            risk = np.sqrt(max(var, 1e-10))
            return -(ret - risk_free_rate) / risk

        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
        bounds = [(0.0, 1.0)] * n
        result = minimize(
            neg_sharpe, x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"ftol": 1e-9, "maxiter": 1000},
        )
        w_scipy = np.maximum(result.x, 0)
        s = w_scipy.sum()
        if s > 1e-8:
            w_scipy = w_scipy / s
            _, _, sr_scipy = compute_metrics(w_scipy, mu, sigma, risk_free_rate)
            if sr_scipy > best_sharpe:
                best_sharpe = sr_scipy
                best_weights = w_scipy
    except Exception as e:
        logger.warning(f"MaxSharpeRatio scipy also failed: {e}")

    if best_weights is None:
        best_weights = np.ones(n) / n

    expected_return, expected_risk, sharpe_ratio = compute_metrics(best_weights, mu, sigma, risk_free_rate)
    return {
        "model_name": "MaxSharpeRatio",
        "weights": best_weights,
        "expected_return": expected_return,
        "expected_risk": expected_risk,
        "sharpe_ratio": sharpe_ratio,
    }


def mean_variance(mu: np.ndarray, sigma: np.ndarray, risk_level: float = 0.5, risk_free_rate: float = 0.04) -> dict:
    n = len(mu)
    target_return = float(np.min(mu) + (np.max(mu) - np.min(mu)) * risk_level)

    weights = None

    try:
        from pyscipopt import Model, quicksum
        model = Model()
        model.hideOutput()
        x = [model.addVar(lb=0.0, ub=1.0, vtype="C", name=f"x_{i}") for i in range(n)]
        obj = quicksum(sigma[i, j] * x[i] * x[j] for i in range(n) for j in range(n))
        model.setObjective(obj, "minimize")
        model.addCons(quicksum(x[i] for i in range(n)) == 1.0)
        model.addCons(quicksum(mu[i] * x[i] for i in range(n)) >= target_return)
        model.optimize()
        if model.getStatus() == "optimal":
            weights = _normalize_weights([model.getVal(x[i]) for i in range(n)])
        else:
            raise ValueError(f"SCIP status: {model.getStatus()}")
    except Exception as e:
        logger.warning(f"MeanVariance SCIP failed ({e}), falling back to scipy")
        from scipy.optimize import minimize
        x0 = np.ones(n) / n
        constraints = [
            {"type": "eq", "fun": lambda x: np.sum(x) - 1.0},
            {"type": "ineq", "fun": lambda x: float(mu @ x) - target_return},
        ]
        bounds = [(0.0, 1.0)] * n
        result = minimize(
            lambda x: float(x @ sigma @ x),
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"ftol": 1e-9, "maxiter": 1000},
        )
        weights = _normalize_weights(result.x)

    expected_return, expected_risk, sharpe_ratio = compute_metrics(weights, mu, sigma, risk_free_rate)
    return {
        "model_name": "MeanVariance",
        "weights": weights,
        "expected_return": expected_return,
        "expected_risk": expected_risk,
        "sharpe_ratio": sharpe_ratio,
    }


def equal_weight(mu: np.ndarray, sigma: np.ndarray, risk_free_rate: float = 0.04) -> dict:
    n = len(mu)
    weights = np.ones(n) / n
    expected_return, expected_risk, sharpe_ratio = compute_metrics(weights, mu, sigma, risk_free_rate)
    return {
        "model_name": "EqualWeight",
        "weights": weights,
        "expected_return": expected_return,
        "expected_risk": expected_risk,
        "sharpe_ratio": sharpe_ratio,
    }


def risk_parity(mu: np.ndarray, sigma: np.ndarray, risk_free_rate: float = 0.04) -> dict:
    from scipy.optimize import minimize
    n = len(mu)
    x0 = np.ones(n) / n

    def objective(x):
        x = np.array(x)
        portfolio_var = float(x @ sigma @ x)
        if portfolio_var < 1e-10:
            return 1e10
        marginal_contrib = sigma @ x
        risk_contrib = x * marginal_contrib
        target = portfolio_var / n
        return float(np.sum((risk_contrib - target) ** 2))

    constraints = [{"type": "eq", "fun": lambda x: np.sum(x) - 1.0}]
    bounds = [(0.001, 1.0)] * n

    result = minimize(
        objective,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 2000},
    )
    weights = _normalize_weights(result.x)

    expected_return, expected_risk, sharpe_ratio = compute_metrics(weights, mu, sigma, risk_free_rate)
    return {
        "model_name": "RiskParity",
        "weights": weights,
        "expected_return": expected_return,
        "expected_risk": expected_risk,
        "sharpe_ratio": sharpe_ratio,
    }


def _risk_aversion_from_risk_level(risk_level: float) -> float:
    return float(np.clip(2.5 - 2.0 * float(risk_level), 0.25, 3.0))


def generate_efficient_frontier(
    mu: np.ndarray,
    sigma: np.ndarray,
    n_points: int = 7,
    risk_free_rate: float = 0.04,
) -> List[dict]:
    if n_points < 2:
        raise ValueError("n_points must be at least 2")

    min_return = float(np.min(mu))
    max_return = float(np.max(mu))
    if abs(max_return - min_return) < 1e-12:
        target_returns = np.full(n_points, min_return)
    else:
        target_returns = np.linspace(min_return, max_return, n_points)

    frontier = []
    for target_return in target_returns:
        if abs(max_return - min_return) < 1e-12:
            risk_level = 0.5
        else:
            risk_level = float((target_return - min_return) / (max_return - min_return))
        result = mean_variance(mu, sigma, risk_level=risk_level, risk_free_rate=risk_free_rate)
        frontier.append(
            {
                "target_return": float(target_return),
                "weights": result["weights"],
                "expected_return": float(result["expected_return"]),
                "expected_risk": float(result["expected_risk"]),
                "sharpe_ratio": float(result["sharpe_ratio"]),
            }
        )

    frontier.sort(key=lambda point: point["expected_risk"])
    return frontier


def run_all_models(
    mu: np.ndarray,
    sigma: np.ndarray,
    tickers: List[str],
    returns_df: Optional[pd.DataFrame] = None,
    risk_tolerance_normalized: float = 5.0,
    risk_free_rate: float = 0.04,
    max_gross_exposure: float = 1.5,
    max_short_exposure: float = 0.5,
    max_cash_borrow: float = 0.25,
    max_turnover: float = 0.25,
    current_weights: Optional[Dict[str, float]] = None,
    latest_prices: Optional[np.ndarray] = None,
    sector_metadata: Optional[Dict[str, Dict[str, str]]] = None,
    sector_max_weights: Optional[Dict[str, float]] = None,
    transaction_cost_model: str = DEFAULT_TRANSACTION_COST_MODEL,
    transaction_cost_rate: Optional[float] = None,
    per_asset_transaction_costs: Optional[Dict[str, float]] = None,
    average_daily_dollar_volume: Optional[Dict[str, float]] = None,
    market_impact_coefficient: Optional[float] = None,
    per_asset_market_impact_coefficients: Optional[Dict[str, float]] = None,
    impact_adv_floor: float = DEFAULT_IMPACT_ADV_FLOOR,
    total_amount: float = 1.0,
    max_positions: Optional[int] = None,
    min_position_weight: Optional[float] = None,
    factor_exposures: Optional[Dict[str, Dict[str, float]]] = None,
    factor_covariance: Optional[Dict[str, Dict[str, float]]] = None,
    specific_risk: Optional[Dict[str, float]] = None,
    lot_sizes: Optional[np.ndarray] = None,
) -> dict:
    """
    Run all core portfolio optimization models.
    Returns dict mapping model_name -> result dict with keys:
      weights (np.ndarray), expected_return, expected_risk, sharpe_ratio
    """
    risk_level = risk_tolerance_normalized / 10.0  # 0 to 1

    results = {}

    _canonical_names = {
        minimum_variance: "MinimumVariance",
        maximum_return: "MaximumReturn",
        utility_maximization: "UtilityMaximization",
        leverage_short_selling: "LeverageShortSelling",
        leverage_borrowing: "LeverageBorrowing",
        turnover_constrained_mean_variance: "TurnoverConstrained",
        max_sharpe_ratio: "MaxSharpeRatio",
        mean_variance: "MeanVariance",
        equal_weight: "EqualWeight",
        risk_parity: "RiskParity",
        factor_utility_maximization: "FactorUtilityMaximization",
        factor_variance_constraint: "FactorVarianceConstraint",
        sector_allocation_mean_variance: "SectorAllocation",
        transaction_cost_rebalancing: "TransactionCostRebalancing",
        cardinality_min_buy_in: "CardinalityMinBuyIn",
        round_lot_allocation: "RoundLotAllocation",
    }

    current_weight_vector = None
    if current_weights is not None:
        current_weight_vector = _vector_from_current_weights(current_weights, tickers)

    model_specs = [
        (minimum_variance, {"mu": mu, "sigma": sigma, "risk_free_rate": risk_free_rate}),
        (maximum_return, {"mu": mu, "sigma": sigma, "risk_level": risk_level, "risk_free_rate": risk_free_rate}),
        (
            utility_maximization,
            {
                "mu": mu,
                "sigma": sigma,
                "risk_aversion": _risk_aversion_from_risk_level(risk_level),
                "risk_free_rate": risk_free_rate,
            },
        ),
        (
            leverage_short_selling,
            {
                "mu": mu,
                "sigma": sigma,
                "risk_level": risk_level,
                "max_gross_exposure": max_gross_exposure,
                "max_short_exposure": max_short_exposure,
                "risk_free_rate": risk_free_rate,
            },
        ),
        (
            leverage_borrowing,
            {
                "mu": mu,
                "sigma": sigma,
                "risk_level": risk_level,
                "max_cash_borrow": max_cash_borrow,
                "risk_free_rate": risk_free_rate,
            },
        ),
        (
            turnover_constrained_mean_variance,
            {
                "mu": mu,
                "sigma": sigma,
                "current_weights": current_weight_vector,
                "risk_level": risk_level,
                "max_turnover": max_turnover,
                "risk_free_rate": risk_free_rate,
            },
        ),
        (max_sharpe_ratio, {"mu": mu, "sigma": sigma, "risk_free_rate": risk_free_rate}),
        (mean_variance, {"mu": mu, "sigma": sigma, "risk_level": risk_level, "risk_free_rate": risk_free_rate}),
        (equal_weight, {"mu": mu, "sigma": sigma, "risk_free_rate": risk_free_rate}),
        (risk_parity, {"mu": mu, "sigma": sigma, "risk_free_rate": risk_free_rate}),
    ]

    if returns_df is not None or factor_exposures is not None:
        model_specs.extend([
            (factor_utility_maximization, {
                "mu": mu,
                "tickers": tickers,
                "returns_df": returns_df,
                "factor_exposures": factor_exposures,
                "factor_covariance": factor_covariance,
                "specific_risk": specific_risk,
                "risk_aversion": _risk_aversion_from_risk_level(risk_level),
                "risk_free_rate": risk_free_rate,
            }),
            (factor_variance_constraint, {
                "mu": mu,
                "tickers": tickers,
                "returns_df": returns_df,
                "factor_exposures": factor_exposures,
                "factor_covariance": factor_covariance,
                "specific_risk": specific_risk,
                "risk_level": risk_level,
                "risk_free_rate": risk_free_rate,
            }),
        ])

    if sector_metadata and sector_max_weights:
        model_specs.append((sector_allocation_mean_variance, {
            "mu": mu,
            "sigma": sigma,
            "tickers": tickers,
            "sector_metadata": sector_metadata,
            "sector_max_weights": sector_max_weights,
            "risk_level": risk_level,
            "risk_free_rate": risk_free_rate,
        }))

    if current_weight_vector is not None and transaction_cost_rate is not None:
        model_specs.append((transaction_cost_rebalancing, {
            "mu": mu,
            "sigma": sigma,
            "current_weights": current_weight_vector,
            "tickers": tickers,
            "risk_level": risk_level,
            "transaction_cost_rate": transaction_cost_rate,
            "transaction_cost_model": transaction_cost_model,
            "per_asset_transaction_costs": per_asset_transaction_costs,
            "market_impact_coefficient": float(max(market_impact_coefficient or 0.0, 0.0)),
            "per_asset_market_impact_coefficients": per_asset_market_impact_coefficients,
            "average_daily_dollar_volume": average_daily_dollar_volume,
            "impact_adv_floor": impact_adv_floor,
            "total_amount": total_amount,
            "risk_free_rate": risk_free_rate,
        }))

    if max_positions is not None:
        model_specs.append((cardinality_min_buy_in, {
            "mu": mu,
            "sigma": sigma,
            "max_positions": max_positions,
            "min_position_weight": float(min_position_weight or 0.0),
            "risk_level": risk_level,
            "risk_free_rate": risk_free_rate,
        }))

    if latest_prices is not None:
        model_specs.append((round_lot_allocation, {
            "mu": mu,
            "sigma": sigma,
            "latest_prices": latest_prices,
            "total_amount": total_amount,
            "risk_level": risk_level,
            "lot_sizes": lot_sizes,
            "risk_free_rate": risk_free_rate,
        }))

    for model_fn, kwargs in model_specs:
        try:
            result = model_fn(**kwargs)
            results[result["model_name"]] = result
        except Exception as e:
            logger.error(f"Model {model_fn.__name__} failed: {e}")
            w = np.ones(len(mu)) / len(mu)
            er, erk, sr = compute_metrics(w, mu, sigma, risk_free_rate)
            name = _canonical_names[model_fn]
            results[name] = {
                "model_name": name,
                "weights": w,
                "expected_return": er,
                "expected_risk": erk,
                "sharpe_ratio": sr,
            }

    return results


def _build_statistical_factor_components(returns_df: pd.DataFrame) -> FactorModelData:
    returns_df = returns_df.dropna(axis=0, how="any")
    if returns_df.empty or returns_df.shape[1] < 2:
        raise ValueError("Factor model requires at least two aligned return series")

    asset_returns = returns_df.to_numpy(dtype=float)
    centered_asset_returns = asset_returns - asset_returns.mean(axis=0, keepdims=True)

    factor_returns = returns_df.mean(axis=1).astype(float).to_numpy(dtype=float)
    centered_market_returns = factor_returns - float(factor_returns.mean())
    market_sample_variance = float(max(np.var(centered_market_returns, ddof=1), 1e-10))
    market_variance = float(max(market_sample_variance * 252.0, 1e-10))

    market_betas = (centered_asset_returns.T @ centered_market_returns) / max(len(centered_market_returns) - 1, 1)
    market_betas = market_betas / market_sample_variance
    residual_returns = centered_asset_returns - np.outer(centered_market_returns, market_betas)

    residual_covariance_daily = np.cov(residual_returns, rowvar=False, ddof=1)
    residual_covariance_daily = np.atleast_2d(_ensure_positive_semidefinite(np.array(residual_covariance_daily, dtype=float)))
    eigenvalues, eigenvectors = np.linalg.eigh(residual_covariance_daily)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]

    positive_indices = [index for index, value in enumerate(eigenvalues) if value > 1e-8]
    residual_factor_count = min(2, len(positive_indices))

    exposure_columns = [market_betas.reshape(-1, 1)]
    factor_variances = [market_variance]
    factor_names = ["market"]

    if residual_factor_count:
        residual_exposures = eigenvectors[:, :residual_factor_count]
        residual_variances = np.maximum(eigenvalues[:residual_factor_count] * 252.0, 1e-10)
        exposure_columns.append(residual_exposures)
        factor_variances.extend(residual_variances.tolist())
        factor_names.extend([f"statistical_{index + 1}" for index in range(residual_factor_count)])

    exposure_matrix = np.column_stack(exposure_columns)
    factor_covariance = np.diag(np.array(factor_variances, dtype=float))

    common_covariance = exposure_matrix @ factor_covariance @ exposure_matrix.T
    asset_covariance = returns_df.cov().to_numpy(dtype=float) * 252.0
    specific_variances = np.maximum(np.diag(asset_covariance - common_covariance), 1e-10)
    specific_matrix = np.diag(specific_variances)
    implied_covariance = common_covariance + specific_matrix
    implied_covariance = _ensure_positive_semidefinite(implied_covariance)
    return FactorModelData(
        factor_names=factor_names,
        exposure_matrix=exposure_matrix,
        factor_covariance=factor_covariance,
        specific_variance=specific_matrix,
        implied_covariance=implied_covariance,
    )


def _build_factor_model_from_contract(
    tickers: List[str],
    factor_exposures: Optional[Dict[str, Dict[str, float]]],
    factor_covariance: Optional[Dict[str, Dict[str, float]]],
    specific_risk: Optional[Dict[str, float]],
    returns_df: Optional[pd.DataFrame],
) -> FactorModelData:
    if factor_exposures is None and factor_covariance is None and specific_risk is None:
        if returns_df is None:
            raise ValueError("returns_df is required when explicit factor inputs are not provided")
        return _build_statistical_factor_components(returns_df)

    if factor_exposures is None or factor_covariance is None or specific_risk is None:
        raise ValueError("factor_exposures, factor_covariance, and specific_risk must be provided together")

    factor_names = list(factor_covariance.keys())
    if not factor_names:
        raise ValueError("factor_covariance must contain at least one factor")

    for factor_name in factor_names:
        row = factor_covariance.get(factor_name, {})
        if set(row.keys()) != set(factor_names):
            raise ValueError("factor_covariance must be a square matrix over a consistent factor set")

    exposure_rows = []
    specific_values = []
    for ticker in tickers:
        ticker_exposures = factor_exposures.get(ticker)
        if ticker_exposures is None:
            raise ValueError(f"Missing factor exposures for ticker {ticker}")
        if set(ticker_exposures.keys()) != set(factor_names):
            raise ValueError(f"Factor exposures for {ticker} must match factor_covariance keys")
        exposure_rows.append([float(ticker_exposures[factor_name]) for factor_name in factor_names])

        if ticker not in specific_risk:
            raise ValueError(f"Missing specific_risk entry for ticker {ticker}")
        specific_value = float(specific_risk[ticker])
        if specific_value < 0.0:
            raise ValueError("specific_risk values must be non-negative")
        specific_values.append(specific_value)

    exposure_matrix = np.array(exposure_rows, dtype=float)
    factor_covariance_matrix = np.array(
        [[float(factor_covariance[row_factor][column_factor]) for column_factor in factor_names] for row_factor in factor_names],
        dtype=float,
    )
    if factor_covariance_matrix.shape[0] != factor_covariance_matrix.shape[1]:
        raise ValueError("factor_covariance must be square")
    if not np.allclose(factor_covariance_matrix, factor_covariance_matrix.T, atol=1e-8):
        raise ValueError("factor_covariance must be symmetric")

    specific_matrix = np.diag(np.array(specific_values, dtype=float))
    implied_covariance = exposure_matrix @ factor_covariance_matrix @ exposure_matrix.T + specific_matrix
    implied_covariance = _ensure_positive_semidefinite(implied_covariance)
    return FactorModelData(
        factor_names=factor_names,
        exposure_matrix=exposure_matrix,
        factor_covariance=factor_covariance_matrix,
        specific_variance=specific_matrix,
        implied_covariance=implied_covariance,
    )


def factor_utility_maximization(
    mu: np.ndarray,
    tickers: List[str],
    returns_df: Optional[pd.DataFrame] = None,
    factor_exposures: Optional[Dict[str, Dict[str, float]]] = None,
    factor_covariance: Optional[Dict[str, Dict[str, float]]] = None,
    specific_risk: Optional[Dict[str, float]] = None,
    risk_aversion: float = 1.0,
    risk_free_rate: float = 0.04,
) -> dict:
    factor_model = _build_factor_model_from_contract(tickers, factor_exposures, factor_covariance, specific_risk, returns_df)
    result = utility_maximization(mu, factor_model.implied_covariance, risk_aversion=risk_aversion, risk_free_rate=risk_free_rate)
    result["model_name"] = "FactorUtilityMaximization"
    result["factor_names"] = factor_model.factor_names
    result["factor_exposures"] = factor_model.exposure_matrix
    result["factor_covariance"] = factor_model.factor_covariance
    result["specific_risk"] = factor_model.specific_variance
    return result


def factor_variance_constraint(
    mu: np.ndarray,
    tickers: List[str],
    returns_df: Optional[pd.DataFrame] = None,
    factor_exposures: Optional[Dict[str, Dict[str, float]]] = None,
    factor_covariance: Optional[Dict[str, Dict[str, float]]] = None,
    specific_risk: Optional[Dict[str, float]] = None,
    risk_level: float = 0.5,
    risk_free_rate: float = 0.04,
) -> dict:
    factor_model = _build_factor_model_from_contract(tickers, factor_exposures, factor_covariance, specific_risk, returns_df)
    result = mean_variance(mu, factor_model.implied_covariance, risk_level=risk_level, risk_free_rate=risk_free_rate)
    result["model_name"] = "FactorVarianceConstraint"
    result["factor_names"] = factor_model.factor_names
    result["factor_exposures"] = factor_model.exposure_matrix
    result["factor_covariance"] = factor_model.factor_covariance
    result["specific_risk"] = factor_model.specific_variance
    return result


def sector_allocation_mean_variance(
    mu: np.ndarray,
    sigma: np.ndarray,
    tickers: List[str],
    sector_metadata: Dict[str, Dict[str, str]],
    sector_max_weights: Dict[str, float],
    risk_level: float = 0.5,
    risk_free_rate: float = 0.04,
) -> dict:
    if not sector_metadata:
        raise ValueError("Sector metadata is required for sector-constrained optimization")
    if not sector_max_weights:
        raise ValueError("Sector limits are required for sector-constrained optimization")

    sector_limits = {_normalized_sector_name(sector): float(limit) for sector, limit in sector_max_weights.items()}
    sector_map = {ticker: _resolve_sector_bucket(sector_metadata.get(ticker, {})) for ticker in tickers}
    eligible_indices = [index for index, ticker in enumerate(tickers) if sector_map.get(ticker) is not None]
    excluded_tickers = [ticker for ticker in tickers if sector_map.get(ticker) is None]

    if not eligible_indices:
        raise ValueError("Sector-constrained optimization requires at least one non-ETF asset with stable sector metadata")

    eligible_mu = np.array(mu[eligible_indices], dtype=float)
    eligible_sigma = np.array(sigma[np.ix_(eligible_indices, eligible_indices)], dtype=float)
    eligible_tickers = [tickers[index] for index in eligible_indices]

    n = len(eligible_mu)
    target_return = float(np.min(eligible_mu) + (np.max(eligible_mu) - np.min(eligible_mu)) * risk_level)
    eligible_weights = None

    try:
        from pyscipopt import Model, quicksum

        model = Model()
        model.hideOutput()
        x = [model.addVar(lb=0.0, ub=1.0, vtype="C", name=f"x_{i}") for i in range(n)]
        model.setObjective(quicksum(eligible_sigma[i, j] * x[i] * x[j] for i in range(n) for j in range(n)), "minimize")
        model.addCons(quicksum(x[i] for i in range(n)) == 1.0)
        model.addCons(quicksum(eligible_mu[i] * x[i] for i in range(n)) >= target_return)

        for sector_name, limit in sector_limits.items():
            sector_indices = [index for index, ticker in enumerate(eligible_tickers) if sector_map.get(ticker) == sector_name]
            if sector_indices:
                model.addCons(quicksum(x[index] for index in sector_indices) <= limit)

        model.optimize()
        if model.getStatus() == "optimal":
            eligible_weights = _normalize_weights([model.getVal(x[i]) for i in range(n)])
        else:
            raise ValueError(f"SCIP status: {model.getStatus()}")
    except Exception as exc:
        logger.warning("SectorAllocation SCIP failed (%s), falling back to scipy", exc)
        from scipy.optimize import minimize

        x0 = np.ones(n) / n
        constraints = [
            {"type": "eq", "fun": lambda x: np.sum(x) - 1.0},
            {"type": "ineq", "fun": lambda x: float(eligible_mu @ x) - target_return},
        ]
        for sector_name, limit in sector_limits.items():
            sector_indices = [index for index, ticker in enumerate(eligible_tickers) if sector_map.get(ticker) == sector_name]
            if sector_indices:
                constraints.append({"type": "ineq", "fun": lambda x, indices=sector_indices, cap=limit: cap - float(np.sum(x[indices]))})

        bounds = [(0.0, 1.0)] * n
        result = minimize(
            lambda x: float(x @ eligible_sigma @ x),
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"ftol": 1e-9, "maxiter": 2000},
        )
        eligible_weights = _normalize_weights(result.x)

    weights = np.zeros(len(mu), dtype=float)
    weights[np.array(eligible_indices, dtype=int)] = eligible_weights

    expected_return, expected_risk, sharpe_ratio = compute_metrics(weights, mu, sigma, risk_free_rate)
    sector_weights = {}
    for ticker, weight in zip(tickers, weights):
        sector = sector_map.get(ticker)
        if sector is None:
            continue
        sector_weights[sector] = sector_weights.get(sector, 0.0) + float(weight)

    return {
        "model_name": "SectorAllocation",
        "weights": weights,
        "expected_return": expected_return,
        "expected_risk": expected_risk,
        "sharpe_ratio": sharpe_ratio,
        "sector_weights": sector_weights,
        "eligible_tickers": eligible_tickers,
        "excluded_tickers": excluded_tickers,
    }


def transaction_cost_rebalancing(
    mu: np.ndarray,
    sigma: np.ndarray,
    current_weights: np.ndarray,
    tickers: Optional[List[str]] = None,
    risk_level: float = 0.5,
    transaction_cost_model: str = DEFAULT_TRANSACTION_COST_MODEL,
    transaction_cost_rate: float = 0.001,
    per_asset_transaction_costs: Optional[Dict[str, float]] = None,
    market_impact_coefficient: float = 0.0,
    per_asset_market_impact_coefficients: Optional[Dict[str, float]] = None,
    average_daily_dollar_volume: Optional[Dict[str, float]] = None,
    impact_adv_floor: float = DEFAULT_IMPACT_ADV_FLOOR,
    total_amount: float = 1.0,
    risk_free_rate: float = 0.04,
) -> dict:
    n = len(mu)
    current_vector = _normalize_weights(np.array(current_weights, dtype=float))
    total_amount = float(max(total_amount, 1e-8))
    target_return = float(np.min(mu) + (np.max(mu) - np.min(mu)) * risk_level)
    ordered_tickers = tickers if tickers is not None else [str(index) for index in range(n)]
    transaction_cost_rates, market_impact_rates, penalties = _resolve_execution_penalties(
        tickers=ordered_tickers,
        transaction_cost_model=transaction_cost_model,
        transaction_cost_rate=transaction_cost_rate,
        per_asset_transaction_costs=per_asset_transaction_costs,
        market_impact_coefficient=market_impact_coefficient,
        per_asset_market_impact_coefficients=per_asset_market_impact_coefficients,
        average_daily_dollar_volume=average_daily_dollar_volume,
        total_amount=total_amount,
        impact_adv_floor=impact_adv_floor,
    )

    weights = None
    trade_cost = 0.0

    try:
        from pyscipopt import Model, quicksum

        model = Model()
        model.hideOutput()
        x = [model.addVar(lb=0.0, ub=1.0, vtype="C", name=f"x_{i}") for i in range(n)]
        buy = [model.addVar(lb=0.0, ub=1.0, vtype="C", name=f"buy_{i}") for i in range(n)]
        sell = [model.addVar(lb=0.0, ub=1.0, vtype="C", name=f"sell_{i}") for i in range(n)]

        utility = quicksum(mu[i] * x[i] for i in range(n)) - 0.5 * _risk_aversion_from_risk_level(risk_level) * quicksum(
            sigma[i, j] * x[i] * x[j] for i in range(n) for j in range(n)
        )
        model.setObjective(utility, "maximize")
        model.addCons(quicksum(mu[i] * x[i] for i in range(n)) >= target_return)

        for index in range(n):
            model.addCons(x[index] == current_vector[index] + buy[index] - sell[index])

        model.addCons(quicksum(x[index] for index in range(n)) + quicksum(penalties[index] * (buy[index] + sell[index]) for index in range(n)) <= 1.0)
        model.optimize()

        if model.getStatus() == "optimal":
            weights = _normalize_weights([model.getVal(x[index]) for index in range(n)])
            trade_cost = float(sum(penalties[index] * (model.getVal(buy[index]) + model.getVal(sell[index])) for index in range(n)))
        else:
            raise ValueError(f"SCIP status: {model.getStatus()}")
    except Exception as exc:
        logger.warning("TransactionCostRebalancing SCIP failed (%s), falling back to scipy", exc)
        from scipy.optimize import minimize

        x0 = np.array(current_vector, dtype=float)

        def objective(x: np.ndarray) -> float:
            x = np.array(x, dtype=float)
            turnover = np.sum(np.abs(x - current_vector))
            utility = float(mu @ x) - 0.5 * _risk_aversion_from_risk_level(risk_level) * float(x @ sigma @ x)
            return -(utility - float(np.mean(penalties)) * turnover)

        constraints = [
            {"type": "eq", "fun": lambda x: np.sum(x) - 1.0},
            {"type": "ineq", "fun": lambda x: float(mu @ x) - target_return},
        ]
        bounds = [(0.0, 1.0)] * n
        result = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"ftol": 1e-9, "maxiter": 2000},
        )
        weights = _normalize_weights(result.x)
        trade_cost = float(np.mean(penalties) * np.sum(np.abs(weights - current_vector)))

    expected_return, expected_risk, sharpe_ratio = compute_metrics(weights, mu, sigma, risk_free_rate)
    cash_weight = float(max(0.0, 1.0 - float(np.sum(weights))))
    realized_expected_return = float(expected_return + cash_weight * risk_free_rate - trade_cost)
    realized_sharpe = float((realized_expected_return - risk_free_rate) / expected_risk) if expected_risk > 1e-10 else 0.0

    return {
        "model_name": "TransactionCostRebalancing",
        "weights": weights,
        "cash_weight": cash_weight,
        "trade_cost": trade_cost,
        "transaction_cost_model": transaction_cost_model,
        "transaction_cost_rates": transaction_cost_rates,
        "market_impact_rates": market_impact_rates,
        "combined_penalty_rates": penalties,
        "impact_adv_floor": float(max(impact_adv_floor, 1.0)),
        "expected_return": realized_expected_return,
        "expected_risk": expected_risk,
        "sharpe_ratio": realized_sharpe,
    }


def cardinality_min_buy_in(
    mu: np.ndarray,
    sigma: np.ndarray,
    max_positions: int,
    min_position_weight: float = 0.0,
    risk_level: float = 0.5,
    risk_free_rate: float = 0.04,
) -> dict:
    n = len(mu)
    max_positions = int(max(max_positions, 1))
    min_position_weight = float(max(min_position_weight, 0.0))
    target_return = float(np.min(mu) + (np.max(mu) - np.min(mu)) * risk_level)
    weights = None

    try:
        from pyscipopt import Model, quicksum

        model = Model()
        model.hideOutput()
        x = [model.addVar(lb=0.0, ub=1.0, vtype="C", name=f"x_{i}") for i in range(n)]
        active = [model.addVar(lb=0.0, ub=1.0, vtype="B", name=f"active_{i}") for i in range(n)]

        model.setObjective(quicksum(sigma[i, j] * x[i] * x[j] for i in range(n) for j in range(n)), "minimize")
        model.addCons(quicksum(x[i] for i in range(n)) == 1.0)
        model.addCons(quicksum(mu[i] * x[i] for i in range(n)) >= target_return)
        model.addCons(quicksum(active[i] for i in range(n)) <= max_positions)

        for index in range(n):
            model.addCons(x[index] <= active[index])
            if min_position_weight > 0.0:
                model.addCons(x[index] >= min_position_weight * active[index])

        model.optimize()
        if model.getStatus() == "optimal":
            weights = _normalize_weights([model.getVal(x[index]) for index in range(n)])
        else:
            raise ValueError(f"SCIP status: {model.getStatus()}")
    except Exception as exc:
        logger.warning("CardinalityMinBuyIn SCIP failed (%s), falling back to scipy", exc)
        weights = mean_variance(mu, sigma, risk_level=risk_level, risk_free_rate=risk_free_rate)["weights"]
        largest_indices = np.argsort(weights)[::-1][:max_positions]
        constrained = np.zeros_like(weights)
        constrained[largest_indices] = weights[largest_indices]
        if min_position_weight > 0.0:
            constrained[constrained > 0.0] = np.maximum(constrained[constrained > 0.0], min_position_weight)
        weights = _normalize_weights(constrained)

    expected_return, expected_risk, sharpe_ratio = compute_metrics(weights, mu, sigma, risk_free_rate)
    return {
        "model_name": "CardinalityMinBuyIn",
        "weights": weights,
        "expected_return": expected_return,
        "expected_risk": expected_risk,
        "sharpe_ratio": sharpe_ratio,
        "open_positions": int(np.sum(weights > 1e-8)),
    }


def round_lot_allocation(
    mu: np.ndarray,
    sigma: np.ndarray,
    latest_prices: np.ndarray,
    total_amount: float,
    risk_level: float = 0.5,
    lot_sizes: Optional[np.ndarray] = None,
    risk_free_rate: float = 0.04,
) -> dict:
    n = len(mu)
    total_amount = float(max(total_amount, 1e-8))
    latest_prices = np.array(latest_prices, dtype=float)
    if latest_prices.shape[0] != n:
        raise ValueError("latest_prices must align with mu and sigma")
    if lot_sizes is None:
        lot_sizes = np.ones(n, dtype=float)
    else:
        lot_sizes = np.array(lot_sizes, dtype=float)
        if lot_sizes.shape[0] != n:
            raise ValueError("lot_sizes must align with mu and sigma")

    target_return = float(np.min(mu) + (np.max(mu) - np.min(mu)) * risk_level)
    weights = None
    lot_units = None

    try:
        from pyscipopt import Model, quicksum

        model = Model()
        model.hideOutput()
        units = [model.addVar(lb=0.0, ub=1e6, vtype="I", name=f"units_{i}") for i in range(n)]
        x = [model.addVar(lb=0.0, ub=1.0, vtype="C", name=f"x_{i}") for i in range(n)]

        model.setObjective(quicksum(sigma[i, j] * x[i] * x[j] for i in range(n) for j in range(n)), "minimize")
        model.addCons(quicksum(x[i] for i in range(n)) <= 1.0)
        model.addCons(quicksum(mu[i] * x[i] for i in range(n)) >= target_return)

        for index in range(n):
            model.addCons(x[index] == (latest_prices[index] * lot_sizes[index] * units[index]) / total_amount)

        model.addCons(quicksum(latest_prices[index] * lot_sizes[index] * units[index] for index in range(n)) <= total_amount)
        model.optimize()

        if model.getStatus() == "optimal":
            lot_units = np.array([model.getVal(units[index]) for index in range(n)], dtype=float)
            weights = np.array([model.getVal(x[index]) for index in range(n)], dtype=float)
        else:
            raise ValueError(f"SCIP status: {model.getStatus()}")
    except Exception as exc:
        logger.warning("RoundLotAllocation SCIP failed (%s), falling back to scipy", exc)
        continuous = mean_variance(mu, sigma, risk_level=risk_level, risk_free_rate=risk_free_rate)["weights"]
        notional = total_amount * continuous
        lot_units = np.floor(notional / np.maximum(latest_prices * lot_sizes, 1e-8))
        invested = lot_units * latest_prices * lot_sizes
        weights = invested / total_amount

    cash_weight = float(max(0.0, 1.0 - float(np.sum(weights))))
    shares = np.array(lot_units, dtype=float) * lot_sizes
    expected_return, expected_risk, sharpe_ratio = compute_metrics(weights, mu, sigma, risk_free_rate)
    return {
        "model_name": "RoundLotAllocation",
        "weights": weights,
        "cash_weight": cash_weight,
        "shares": shares,
        "lot_units": np.array(lot_units, dtype=float),
        "lot_sizes": np.array(lot_sizes, dtype=float),
        "expected_return": expected_return + cash_weight * risk_free_rate,
        "expected_risk": expected_risk,
        "sharpe_ratio": sharpe_ratio,
    }
