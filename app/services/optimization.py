import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


def compute_metrics(weights: np.ndarray, mu: np.ndarray, sigma: np.ndarray, risk_free_rate: float = 0.04):
    weights = np.array(weights)
    expected_return = float(weights @ mu)
    variance = float(weights @ sigma @ weights)
    expected_risk = float(np.sqrt(max(variance, 1e-10)))
    sharpe_ratio = float((expected_return - risk_free_rate) / expected_risk) if expected_risk > 1e-10 else 0.0
    return expected_return, expected_risk, sharpe_ratio


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
    risk_tolerance_normalized: float = 5.0,
    risk_free_rate: float = 0.04,
    max_gross_exposure: float = 1.5,
    max_short_exposure: float = 0.5,
    max_cash_borrow: float = 0.25,
    max_turnover: float = 0.25,
    current_weights: Optional[Dict[str, float]] = None,
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
