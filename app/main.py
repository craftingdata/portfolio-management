from fastapi import FastAPI, HTTPException
from app.models.schemas import FrontierPoint, OptimizeRequest, OptimizeResponse
from app.services.data_service import get_market_data, get_market_liquidity, get_market_metadata
from app.services.optimization import generate_efficient_frontier, run_all_models
from app.services.ranking import rank_portfolios

app = FastAPI(title="Portfolio Management API", version="1.0.0")

MODEL_DESCRIPTIONS = {
    "MinimumVariance": "Minimizes portfolio variance (risk) subject to full investment constraint. Best for conservative investors.",
    "MaximumReturn": "Maximizes expected return subject to a risk budget. Best for aggressive investors.",
    "UtilityMaximization": "Maximizes expected utility using explicit risk aversion. Best for balanced investors.",
    "LeverageShortSelling": "Long-short portfolio with explicit gross leverage and short exposure limits.",
    "LeverageBorrowing": "Portfolio that can borrow cash through an explicit cash sleeve.",
    "TurnoverConstrained": "Mean-variance optimization with turnover limits from the current portfolio.",
    "MaxSharpeRatio": "Maximizes risk-adjusted return (Sharpe ratio). Best for balanced risk/return.",
    "MeanVariance": "Classic Markowitz mean-variance optimization with target return. Best for moderate investors.",
    "EqualWeight": "Simple equal allocation to all assets. Robust baseline with no optimization.",
    "RiskParity": "Equalizes risk contributions from each asset. Good for risk-balanced diversification.",
    "FactorUtilityMaximization": "Utility maximization on a market-factor-implied covariance matrix.",
    "FactorVarianceConstraint": "Mean-variance optimization using a market-factor-implied covariance matrix.",
    "SectorAllocation": "Mean-variance optimization with sector concentration limits.",
    "TransactionCostRebalancing": "Rebalancing model with explicit proportional trading costs.",
    "CardinalityMinBuyIn": "Cardinality-constrained mean-variance optimization with minimum buy-in limits.",
    "RoundLotAllocation": "Integer lot-based allocation using latest prices and a cash remainder.",
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
            return_estimator=request.return_estimator,
            covariance_estimator=request.covariance_estimator,
            mean_shrinkage=request.mean_shrinkage,
            covariance_shrinkage=request.covariance_shrinkage,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data fetch error: {str(e)}")

    tickers = list(prices_df.columns)
    latest_prices = prices_df.iloc[-1].to_numpy(dtype=float)
    lot_sizes = None
    if request.lot_sizes:
        lot_sizes = [float(request.lot_sizes.get(ticker, 1)) for ticker in tickers]
    period_used = f"{len(prices_df)} trading days"

    sector_metadata = None
    average_daily_dollar_volume = None
    if request.sector_max_weights:
        try:
            sector_metadata = get_market_metadata(tickers)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Metadata fetch error: {str(exc)}")

    has_market_impact_input = (
        (request.market_impact_coefficient is not None and request.market_impact_coefficient > 0.0)
        or bool(request.per_asset_market_impact_coefficients)
    )
    if request.current_weights is not None and has_market_impact_input:
        try:
            average_daily_dollar_volume = get_market_liquidity(tickers=tickers, period_months=period_months)
        except Exception:
            average_daily_dollar_volume = None

    # Run optimization models
    try:
        portfolio_results = run_all_models(
            mu=mu,
            sigma=sigma,
            tickers=tickers,
            returns_df=returns_df,
            risk_tolerance_normalized=request.risk_tolerance,
            risk_free_rate=request.risk_free_rate,
            max_gross_exposure=request.max_gross_exposure,
            max_short_exposure=request.max_short_exposure,
            max_cash_borrow=request.max_cash_borrow,
            max_turnover=request.max_turnover,
            current_weights=request.current_weights,
            latest_prices=latest_prices,
            sector_metadata=sector_metadata,
            sector_max_weights=request.sector_max_weights,
            transaction_cost_model=request.transaction_cost_model,
            transaction_cost_rate=request.transaction_cost_rate,
            per_asset_transaction_costs=request.per_asset_transaction_costs,
            average_daily_dollar_volume=average_daily_dollar_volume,
            market_impact_coefficient=request.market_impact_coefficient,
            per_asset_market_impact_coefficients=request.per_asset_market_impact_coefficients,
            impact_adv_floor=request.impact_adv_floor,
            total_amount=request.total_amount,
            max_positions=request.max_positions,
            min_position_weight=request.min_position_weight,
            factor_exposures=request.factor_exposures,
            factor_covariance=request.factor_covariance,
            specific_risk=request.specific_risk,
            lot_sizes=lot_sizes,
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
