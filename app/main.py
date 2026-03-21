from fastapi import FastAPI, HTTPException
from app.models.schemas import FrontierPoint, OptimizeRequest, OptimizeResponse
from app.services.data_service import get_market_data
from app.services.optimization import generate_efficient_frontier, run_all_models
from app.services.ranking import rank_portfolios

app = FastAPI(title="Portfolio Management API", version="1.0.0")

MODEL_DESCRIPTIONS = {
    "MinimumVariance": "Minimizes portfolio variance (risk) subject to full investment constraint. Best for conservative investors.",
    "MaximumReturn": "Maximizes expected return subject to a risk budget. Best for aggressive investors.",
    "UtilityMaximization": "Maximizes expected utility using explicit risk aversion. Best for balanced investors.",
    "MaxSharpeRatio": "Maximizes risk-adjusted return (Sharpe ratio). Best for balanced risk/return.",
    "MeanVariance": "Classic Markowitz mean-variance optimization with target return. Best for moderate investors.",
    "EqualWeight": "Simple equal allocation to all assets. Robust baseline with no optimization.",
    "RiskParity": "Equalizes risk contributions from each asset. Good for risk-balanced diversification.",
}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/models")
def list_models():
    return {"models": [{"name": k, "description": v} for k, v in MODEL_DESCRIPTIONS.items()]}


@app.post("/optimize", response_model=OptimizeResponse)
def optimize(request: OptimizeRequest):
    # request.risk_tolerance and request.investment_horizon are already normalized by validators
    period_months = max(36, request.investment_horizon * 2)

    # Fetch market data
    try:
        prices_df, returns_df, mu, sigma = get_market_data(
            tickers=request.tickers,
            period_months=period_months,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data fetch error: {str(e)}")

    tickers = list(prices_df.columns)
    period_used = f"{len(prices_df)} trading days"

    # Run optimization models
    try:
        portfolio_results = run_all_models(
            mu=mu,
            sigma=sigma,
            tickers=tickers,
            risk_tolerance_normalized=request.risk_tolerance,
            risk_free_rate=request.risk_free_rate,
        )
        efficient_frontier = generate_efficient_frontier(
            mu=mu,
            sigma=sigma,
            n_points=7,
            risk_free_rate=request.risk_free_rate,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization error: {str(e)}")

    # Rank portfolios
    ranked = rank_portfolios(
        portfolio_results=portfolio_results,
        tickers=tickers,
        total_amount=request.total_amount,
        risk_tolerance=request.risk_tolerance,
        investment_horizon_months=request.investment_horizon,
        efficient_frontier=efficient_frontier,
        model_descriptions=MODEL_DESCRIPTIONS,
    )

    frontier_response = [
        FrontierPoint(
            target_return=float(point["target_return"]),
            expected_return=float(point["expected_return"]),
            expected_risk=float(point["expected_risk"]),
            sharpe_ratio=float(point["sharpe_ratio"]),
        )
        for point in efficient_frontier
    ]

    return OptimizeResponse(
        total_amount=request.total_amount,
        risk_tolerance_normalized=request.risk_tolerance,
        investment_horizon_months=request.investment_horizon,
        portfolios=ranked,
        efficient_frontier=frontier_response,
        data_period_used=period_used,
        optimization_status="success",
    )
