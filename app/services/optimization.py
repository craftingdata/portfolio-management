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
    return np.maximum(result.x, 0)


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
            weights = np.array([model.getVal(x[i]) for i in range(n)])
            weights = np.maximum(weights, 0)
            weights = weights / weights.sum()
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
            weights = np.array([model.getVal(x[i]) for i in range(n)])
            weights = np.maximum(weights, 0)
            s = weights.sum()
            if s > 1e-8:
                weights = weights / s
            else:
                raise ValueError("Zero weights from SCIP")
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
        weights = np.maximum(result.x, 0)
        s = weights.sum()
        if s > 1e-8:
            weights = weights / s
        else:
            weights = np.ones(n) / n

    expected_return, expected_risk, sharpe_ratio = compute_metrics(weights, mu, sigma, risk_free_rate)
    return {
        "model_name": "MaximumReturn",
        "weights": weights,
        "expected_return": expected_return,
        "expected_risk": expected_risk,
        "sharpe_ratio": sharpe_ratio,
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
            weights = np.array([model.getVal(x[i]) for i in range(n)])
            weights = np.maximum(weights, 0)
            s = weights.sum()
            if s > 1e-8:
                weights = weights / s
            else:
                raise ValueError("Zero weights")
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
        weights = np.maximum(result.x, 0)
        s = weights.sum()
        if s > 1e-8:
            weights = weights / s
        else:
            weights = np.ones(n) / n

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
    weights = np.maximum(result.x, 0)
    s = weights.sum()
    if s > 1e-8:
        weights = weights / s
    else:
        weights = np.ones(n) / n

    expected_return, expected_risk, sharpe_ratio = compute_metrics(weights, mu, sigma, risk_free_rate)
    return {
        "model_name": "RiskParity",
        "weights": weights,
        "expected_return": expected_return,
        "expected_risk": expected_risk,
        "sharpe_ratio": sharpe_ratio,
    }


def run_all_models(
    mu: np.ndarray,
    sigma: np.ndarray,
    tickers: List[str],
    risk_tolerance_normalized: float = 5.0,
    risk_free_rate: float = 0.04,
) -> dict:
    """
    Run all 6 portfolio optimization models.
    Returns dict mapping model_name -> result dict with keys:
      weights (np.ndarray), expected_return, expected_risk, sharpe_ratio
    """
    risk_level = risk_tolerance_normalized / 10.0  # 0 to 1

    results = {}

    _canonical_names = {
        minimum_variance: "MinimumVariance",
        maximum_return: "MaximumReturn",
        max_sharpe_ratio: "MaxSharpeRatio",
        mean_variance: "MeanVariance",
        equal_weight: "EqualWeight",
        risk_parity: "RiskParity",
    }

    for model_fn, kwargs in [
        (minimum_variance, {"mu": mu, "sigma": sigma, "risk_free_rate": risk_free_rate}),
        (maximum_return, {"mu": mu, "sigma": sigma, "risk_level": risk_level, "risk_free_rate": risk_free_rate}),
        (max_sharpe_ratio, {"mu": mu, "sigma": sigma, "risk_free_rate": risk_free_rate}),
        (mean_variance, {"mu": mu, "sigma": sigma, "risk_level": risk_level, "risk_free_rate": risk_free_rate}),
        (equal_weight, {"mu": mu, "sigma": sigma, "risk_free_rate": risk_free_rate}),
        (risk_parity, {"mu": mu, "sigma": sigma, "risk_free_rate": risk_free_rate}),
    ]:
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
