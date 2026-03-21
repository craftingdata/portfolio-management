from typing import List, Optional

import numpy as np
from app.models.schemas import PortfolioResult

MODEL_DESCRIPTIONS_DEFAULT = {
    "MinimumVariance": "Minimizes portfolio variance (risk) subject to full investment constraint. Best for conservative investors.",
    "MaximumReturn": "Maximizes expected return subject to a risk budget. Best for aggressive investors.",
    "UtilityMaximization": "Maximizes expected utility using an explicit risk-aversion parameter. Best for balanced investors who want a single objective.",
    "LeverageShortSelling": "Long-short portfolio with explicit gross leverage and short exposure limits. Best when shorting is allowed.",
    "LeverageBorrowing": "Portfolio that can borrow cash to increase exposure while tracking a cash sleeve. Best when leverage is allowed.",
    "TurnoverConstrained": "Mean-variance portfolio with explicit turnover limits from the current holdings. Best for rebalancing decisions.",
    "MaxSharpeRatio": "Maximizes risk-adjusted return (Sharpe ratio). Best for balanced risk/return.",
    "MeanVariance": "Classic Markowitz mean-variance optimization with target return. Best for moderate investors.",
    "EqualWeight": "Simple equal allocation to all assets. Robust baseline with no optimization.",
    "RiskParity": "Equalizes risk contributions from each asset. Good for risk-balanced diversification.",
    "FactorUtilityMaximization": "Utility maximization using a factor-implied covariance matrix.",
    "FactorVarianceConstraint": "Mean-variance optimization using a factor-implied covariance matrix.",
    "SectorAllocation": "Mean-variance optimization with sector concentration caps.",
    "TransactionCostRebalancing": "Rebalancing model with explicit proportional trading costs.",
    "CardinalityMinBuyIn": "Cardinality-constrained mean-variance optimization with minimum buy-in rules.",
    "RoundLotAllocation": "Integer lot-based allocation using latest prices and a cash remainder.",
}

BASE_ORDER = {
    "low": ["MinimumVariance", "EqualWeight", "RiskParity", "RoundLotAllocation", "TransactionCostRebalancing", "CardinalityMinBuyIn", "SectorAllocation", "FactorVarianceConstraint", "FactorUtilityMaximization", "TurnoverConstrained", "UtilityMaximization", "MeanVariance", "MaxSharpeRatio", "LeverageBorrowing", "LeverageShortSelling", "MaximumReturn"],
    "medium": ["MaxSharpeRatio", "UtilityMaximization", "MeanVariance", "RiskParity", "RoundLotAllocation", "FactorVarianceConstraint", "FactorUtilityMaximization", "TransactionCostRebalancing", "SectorAllocation", "TurnoverConstrained", "MinimumVariance", "EqualWeight", "CardinalityMinBuyIn", "LeverageBorrowing", "LeverageShortSelling", "MaximumReturn"],
    "high": ["MaximumReturn", "LeverageBorrowing", "LeverageShortSelling", "UtilityMaximization", "MaxSharpeRatio", "MeanVariance", "FactorUtilityMaximization", "FactorVarianceConstraint", "TransactionCostRebalancing", "SectorAllocation", "RoundLotAllocation", "RiskParity", "TurnoverConstrained", "EqualWeight", "CardinalityMinBuyIn", "MinimumVariance"],
}

BASE_SCORES = [100, 95, 90, 85, 82, 78, 74, 70, 66, 62, 58, 54, 50, 40, 30, 20]

HORIZON_ADJUSTMENTS = {
    "MinimumVariance": {"short": +15, "long": -10},
    "EqualWeight": {"short": +10, "long": 0},
    "MaximumReturn": {"short": -15, "long": +15},
    "UtilityMaximization": {"short": -5, "long": +5},
    "LeverageShortSelling": {"short": -10, "long": +10},
    "LeverageBorrowing": {"short": -5, "long": +15},
    "TurnoverConstrained": {"short": +5, "long": +5},
    "MaxSharpeRatio": {"short": -5, "long": +10},
    "MeanVariance": {"short": 0, "long": 0},
    "RiskParity": {"short": 0, "long": 0},
    "FactorUtilityMaximization": {"short": -5, "long": +5},
    "FactorVarianceConstraint": {"short": 0, "long": +5},
    "SectorAllocation": {"short": 0, "long": +5},
    "TransactionCostRebalancing": {"short": +5, "long": +10},
    "CardinalityMinBuyIn": {"short": 0, "long": +5},
    "RoundLotAllocation": {"short": +5, "long": 0},
}

REASONING_TEMPLATES = {
    "MinimumVariance": (
        "Minimizes portfolio variance - ideal for risk tolerance {rt}/10 with {h}-month horizon. "
        "Focuses on capital preservation."
    ),
    "MaximumReturn": (
        "Maximizes expected return within risk constraints - suitable for high risk tolerance ({rt}/10) "
        "and long horizons ({h} months)."
    ),
    "UtilityMaximization": (
        "Maximizes expected utility with explicit risk aversion - adaptable for risk tolerance {rt}/10 "
        "and {h}-month horizon."
    ),
    "LeverageShortSelling": (
        "Uses long-short exposure with gross leverage controls - suitable when shorting is allowed and {h}-month horizon supports active positioning."
    ),
    "LeverageBorrowing": (
        "Uses an explicit cash sleeve to model borrowing and leveraged exposure - suited to {h}-month horizons where leverage is acceptable."
    ),
    "TurnoverConstrained": (
        "Rebalances from the current portfolio while limiting turnover - useful for {h}-month horizons and practical trading constraints."
    ),
    "MaxSharpeRatio": (
        "Optimizes risk-adjusted returns (Sharpe ratio) - versatile approach for medium risk tolerance "
        "({rt}/10) and {h}-month horizon."
    ),
    "MeanVariance": (
        "Classic Markowitz mean-variance optimization targeting returns commensurate with risk "
        "tolerance {rt}/10 and {h}-month investment horizon."
    ),
    "EqualWeight": (
        "Simple equal allocation providing naive diversification - low complexity, suitable as baseline "
        "for {rt}/10 risk tolerance."
    ),
    "RiskParity": (
        "Equalizes risk contributions across assets - suitable for medium risk tolerance ({rt}/10) "
        "and balanced exposure over {h} months."
    ),
    "FactorUtilityMaximization": (
        "Uses a factor-implied covariance structure with explicit utility maximization - useful when factor risk estimates are available."
    ),
    "FactorVarianceConstraint": (
        "Uses a factor-implied covariance structure under a variance constraint - helpful when factor risk modeling is preferred."
    ),
    "SectorAllocation": (
        "Applies sector concentration limits while preserving mean-variance discipline - good when diversification across sectors matters."
    ),
    "TransactionCostRebalancing": (
        "Rebalances from the current portfolio while explicitly penalizing trading costs - best when turnover and execution costs matter."
    ),
    "CardinalityMinBuyIn": (
        "Constrains the number of holdings and enforces minimum position sizes - useful when portfolio breadth must be limited."
    ),
    "RoundLotAllocation": (
        "Uses integer lot sizing with a cash remainder - best when discrete trading units are required."
    ),
}


def rank_portfolios(
    portfolio_results: dict,
    tickers: List[str],
    total_amount: float,
    risk_tolerance: float,
    investment_horizon_months: int,
    efficient_frontier: Optional[List[dict]] = None,
    model_descriptions: dict = None,
) -> List[PortfolioResult]:
    if model_descriptions is None:
        model_descriptions = MODEL_DESCRIPTIONS_DEFAULT

    # Determine risk category
    if risk_tolerance <= 3:
        risk_cat = "low"
    elif risk_tolerance <= 6:
        risk_cat = "medium"
    else:
        risk_cat = "high"

    # Determine horizon category
    if investment_horizon_months < 12:
        horizon_cat = "short"
    elif investment_horizon_months > 36:
        horizon_cat = "long"
    else:
        horizon_cat = "medium"

    order = BASE_ORDER[risk_cat]
    base_score_lookup = {model_name: BASE_SCORES[idx] for idx, model_name in enumerate(order)}

    model_metrics = []
    for model_name in order:
        if model_name not in portfolio_results:
            continue
        result = portfolio_results[model_name]
        model_metrics.append(
            {
                "model_name": model_name,
                "result": result,
                "expected_return": float(result["expected_return"]),
                "expected_risk": float(result["expected_risk"]),
                "sharpe_ratio": float(result["sharpe_ratio"]),
            }
        )

    if not model_metrics:
        return []

    returns = np.array([item["expected_return"] for item in model_metrics], dtype=float)
    risks = np.array([item["expected_risk"] for item in model_metrics], dtype=float)
    sharpes = np.array([item["sharpe_ratio"] for item in model_metrics], dtype=float)

    if efficient_frontier:
        frontier_sorted = sorted(efficient_frontier, key=lambda point: float(point["expected_risk"]))
        frontier_risks = np.array([float(point["expected_risk"]) for point in frontier_sorted], dtype=float)
        frontier_returns = np.array([float(point["expected_return"]) for point in frontier_sorted], dtype=float)
    else:
        frontier_risks = np.array([], dtype=float)
        frontier_returns = np.array([], dtype=float)

    risk_floor = float(risks.min())
    risk_ceiling = float(risks.max())
    risk_span = max(risk_ceiling - risk_floor, 1e-8)

    horizon_shift = {"short": -0.12, "medium": 0.0, "long": 0.10}[horizon_cat]
    target_risk_fraction = float(np.clip((risk_tolerance / 10.0) + horizon_shift, 0.0, 1.0))
    target_risk = risk_floor + target_risk_fraction * risk_span

    def _scale(value: float, lower: float, upper: float) -> float:
        if abs(upper - lower) < 1e-12:
            return 0.5
        return float(np.clip((value - lower) / (upper - lower), 0.0, 1.0))

    def _frontier_bonus(expected_risk: float, expected_return: float) -> float:
        if frontier_risks.size == 0:
            return 50.0
        frontier_return = float(
            np.interp(
                expected_risk,
                frontier_risks,
                frontier_returns,
                left=float(frontier_returns[0]),
                right=float(frontier_returns[-1]),
            )
        )
        gap = max(0.0, frontier_return - expected_return)
        scale = max(abs(frontier_return), abs(expected_return), 1e-8)
        return 100.0 * (1.0 - min(1.0, gap / scale))

    model_scores = {}
    for item in model_metrics:
        model_name = item["model_name"]
        base_score = base_score_lookup[model_name]
        adj = HORIZON_ADJUSTMENTS.get(model_name, {}).get(horizon_cat, 0)
        heuristic_score = float(np.clip(base_score + adj, 0.0, 100.0))

        return_score = _scale(item["expected_return"], float(returns.min()), float(returns.max()))
        sharpe_score = _scale(item["sharpe_ratio"], float(sharpes.min()), float(sharpes.max()))
        risk_fit_score = 100.0 * (1.0 - min(1.0, abs(item["expected_risk"] - target_risk) / risk_span))
        frontier_score = _frontier_bonus(item["expected_risk"], item["expected_return"])
        output_score = 100.0 * (
            0.35 * return_score
            + 0.30 * sharpe_score
            + 0.20 * (risk_fit_score / 100.0)
            + 0.15 * (frontier_score / 100.0)
        )
        model_scores[model_name] = float(np.clip(0.55 * heuristic_score + 0.45 * output_score, 0.0, 100.0))

    sorted_models = sorted(model_scores.keys(), key=lambda m: model_scores[m], reverse=True)

    ranked = []
    for model_name in sorted_models:
        result = portfolio_results[model_name]
        weights_arr = result["weights"]

        weights_dict = {tickers[i]: float(weights_arr[i]) for i in range(len(tickers))}
        cash_weight = result.get("cash_weight")
        if cash_weight is not None:
            weights_dict["CASH"] = float(cash_weight)
        allocation_dict = {t: float(w * total_amount) for t, w in weights_dict.items()}

        rt_display = round(risk_tolerance, 1)
        reasoning = REASONING_TEMPLATES.get(model_name, "Portfolio optimization model.").format(
            rt=rt_display, h=investment_horizon_months
        )

        description = model_descriptions.get(model_name, MODEL_DESCRIPTIONS_DEFAULT.get(model_name, ""))

        ranked.append(
            PortfolioResult(
                rank=len(ranked) + 1,
                model_name=model_name,
                model_description=description,
                weights=weights_dict,
                expected_annual_return=float(result["expected_return"]),
                expected_annual_risk=float(result["expected_risk"]),
                sharpe_ratio=float(result["sharpe_ratio"]),
                allocation=allocation_dict,
                applicability_score=float(model_scores[model_name]),
                reasoning=reasoning,
            )
        )

    return ranked
