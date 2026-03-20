import numpy as np
from typing import Dict, List
from app.models.schemas import PortfolioResult

MODEL_DESCRIPTIONS_DEFAULT = {
    "MinimumVariance": "Minimizes portfolio variance (risk) subject to full investment constraint. Best for conservative investors.",
    "MaximumReturn": "Maximizes expected return subject to a risk budget. Best for aggressive investors.",
    "MaxSharpeRatio": "Maximizes risk-adjusted return (Sharpe ratio). Best for balanced risk/return.",
    "MeanVariance": "Classic Markowitz mean-variance optimization with target return. Best for moderate investors.",
    "EqualWeight": "Simple equal allocation to all assets. Robust baseline with no optimization.",
    "RiskParity": "Equalizes risk contributions from each asset. Good for risk-balanced diversification.",
}

BASE_ORDER = {
    "low": ["MinimumVariance", "EqualWeight", "RiskParity", "MeanVariance", "MaxSharpeRatio", "MaximumReturn"],
    "medium": ["MaxSharpeRatio", "MeanVariance", "RiskParity", "MinimumVariance", "EqualWeight", "MaximumReturn"],
    "high": ["MaximumReturn", "MaxSharpeRatio", "MeanVariance", "RiskParity", "EqualWeight", "MinimumVariance"],
}

BASE_SCORES = [100, 85, 70, 55, 40, 25]

HORIZON_ADJUSTMENTS = {
    "MinimumVariance": {"short": +15, "long": -10},
    "EqualWeight": {"short": +10, "long": 0},
    "MaximumReturn": {"short": -15, "long": +15},
    "MaxSharpeRatio": {"short": -5, "long": +10},
    "MeanVariance": {"short": 0, "long": 0},
    "RiskParity": {"short": 0, "long": 0},
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
}


def rank_portfolios(
    portfolio_results: dict,
    tickers: List[str],
    total_amount: float,
    risk_tolerance: float,
    investment_horizon_months: int,
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

    # Compute scores
    model_scores = {}
    for idx, model_name in enumerate(order):
        base_score = BASE_SCORES[idx]
        adj = HORIZON_ADJUSTMENTS.get(model_name, {}).get(horizon_cat, 0)
        score = min(100, max(0, base_score + adj))
        model_scores[model_name] = score

    # Sort by score descending
    sorted_models = sorted(model_scores.keys(), key=lambda m: model_scores[m], reverse=True)

    ranked = []
    for rank_idx, model_name in enumerate(sorted_models, start=1):
        if model_name not in portfolio_results:
            continue
        result = portfolio_results[model_name]
        weights_arr = result["weights"]

        weights_dict = {tickers[i]: float(weights_arr[i]) for i in range(len(tickers))}
        allocation_dict = {t: float(w * total_amount) for t, w in weights_dict.items()}

        rt_display = round(risk_tolerance, 1)
        reasoning = REASONING_TEMPLATES.get(model_name, "Portfolio optimization model.").format(
            rt=rt_display, h=investment_horizon_months
        )

        description = model_descriptions.get(model_name, MODEL_DESCRIPTIONS_DEFAULT.get(model_name, ""))

        ranked.append(
            PortfolioResult(
                rank=rank_idx,
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
