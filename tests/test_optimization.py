import numpy as np
import pandas as pd
import pytest
from app.services.optimization import (
    minimum_variance,
    maximum_return,
    utility_maximization,
    leverage_short_selling,
    leverage_borrowing,
    turnover_constrained_mean_variance,
    max_sharpe_ratio,
    mean_variance,
    equal_weight,
    risk_parity,
    generate_efficient_frontier,
    run_all_models,
    compute_metrics,
    factor_utility_maximization,
    factor_variance_constraint,
    sector_allocation_mean_variance,
    transaction_cost_rebalancing,
    cardinality_min_buy_in,
    round_lot_allocation,
)


@pytest.fixture
def synthetic_data():
    """Generate reproducible synthetic market data for testing."""
    np.random.seed(42)
    n = 5
    tickers = ["AAPL", "MSFT", "GOOGL", "JPM", "SPY"]
    mu = np.array([0.12, 0.11, 0.10, 0.09, 0.08])

    # Build a simple covariance matrix
    vols = np.array([0.25, 0.22, 0.23, 0.18, 0.15])
    corr = np.array([
        [1.00, 0.70, 0.65, 0.50, 0.60],
        [0.70, 1.00, 0.68, 0.52, 0.62],
        [0.65, 0.68, 1.00, 0.48, 0.58],
        [0.50, 0.52, 0.48, 1.00, 0.55],
        [0.60, 0.62, 0.58, 0.55, 1.00],
    ])
    sigma = np.outer(vols, vols) * corr
    return tickers, mu, sigma


@pytest.fixture
def price_frame_data():
    tickers = ["AAPL", "MSFT", "GOOGL", "JPM", "SPY"]
    np.random.seed(7)
    n_days = 80
    drift = np.array([0.0006, 0.0005, 0.0004, 0.0003, 0.0002])
    vol = np.array([0.012, 0.011, 0.010, 0.009, 0.008])
    prices = np.ones((n_days + 1, len(tickers))) * 100.0
    for index in range(n_days):
        returns = drift + vol * np.random.standard_normal(len(tickers))
        prices[index + 1] = prices[index] * (1.0 + returns)

    dates = pd.bdate_range("2024-01-01", periods=n_days + 1)
    prices_df = pd.DataFrame(prices, index=dates, columns=tickers)
    returns_df = prices_df.pct_change().dropna()
    mu = returns_df.mean().to_numpy() * 252
    sigma = returns_df.cov().to_numpy() * 252
    return tickers, prices_df, returns_df, mu, sigma


def assert_valid_portfolio(result, n):
    """Common assertions for all portfolio results."""
    weights = result["weights"]
    assert len(weights) == n, f"Expected {n} weights, got {len(weights)}"
    if "cash_weight" in result:
        assert abs(weights.sum() + float(result["cash_weight"]) - 1.0) < 1e-4, f"Weights + cash do not sum to 1"
    else:
        assert abs(weights.sum() - 1.0) < 1e-4, f"Weights sum {weights.sum()} != 1"
    if result["model_name"] not in {"LeverageShortSelling", "LeverageBorrowing"}:
        assert all(w >= -0.001 for w in weights), f"Negative weight found: {weights}"
    assert np.isfinite(result["expected_return"]), "expected_return is not finite"
    assert np.isfinite(result["expected_risk"]), "expected_risk is not finite"
    assert np.isfinite(result["sharpe_ratio"]), "sharpe_ratio is not finite"
    assert result["expected_risk"] >= 0, "expected_risk must be non-negative"


def test_minimum_variance(synthetic_data):
    tickers, mu, sigma = synthetic_data
    result = minimum_variance(mu, sigma)
    assert result["model_name"] == "MinimumVariance"
    assert_valid_portfolio(result, len(mu))


def test_maximum_return(synthetic_data):
    tickers, mu, sigma = synthetic_data
    result = maximum_return(mu, sigma, risk_level=0.5)
    assert result["model_name"] == "MaximumReturn"
    assert_valid_portfolio(result, len(mu))


def test_utility_maximization(synthetic_data):
    tickers, mu, sigma = synthetic_data
    result = utility_maximization(mu, sigma, risk_aversion=1.5)
    assert result["model_name"] == "UtilityMaximization"
    assert_valid_portfolio(result, len(mu))


def test_leverage_short_selling(synthetic_data):
    tickers, mu, sigma = synthetic_data
    result = leverage_short_selling(mu, sigma, risk_level=0.7, max_gross_exposure=1.4, max_short_exposure=0.3)
    assert result["model_name"] == "LeverageShortSelling"
    assert_valid_portfolio(result, len(mu))
    assert np.min(result["weights"]) < 0


def test_leverage_borrowing(synthetic_data):
    tickers, mu, sigma = synthetic_data
    result = leverage_borrowing(mu, sigma, risk_level=0.8, max_cash_borrow=0.2)
    assert result["model_name"] == "LeverageBorrowing"
    assert_valid_portfolio(result, len(mu))
    assert "cash_weight" in result


def test_turnover_constrained_mean_variance(synthetic_data):
    tickers, mu, sigma = synthetic_data
    current_weights = np.array([0.40, 0.25, 0.15, 0.10, 0.10])
    result = turnover_constrained_mean_variance(
        mu,
        sigma,
        current_weights=current_weights,
        risk_level=0.5,
        max_turnover=0.15,
    )
    assert result["model_name"] == "TurnoverConstrained"
    assert_valid_portfolio(result, len(mu))
    assert result["turnover"] <= 0.150001


def test_max_sharpe_ratio(synthetic_data):
    tickers, mu, sigma = synthetic_data
    result = max_sharpe_ratio(mu, sigma)
    assert result["model_name"] == "MaxSharpeRatio"
    assert_valid_portfolio(result, len(mu))


def test_mean_variance(synthetic_data):
    tickers, mu, sigma = synthetic_data
    result = mean_variance(mu, sigma, risk_level=0.5)
    assert result["model_name"] == "MeanVariance"
    assert_valid_portfolio(result, len(mu))


def test_equal_weight(synthetic_data):
    tickers, mu, sigma = synthetic_data
    result = equal_weight(mu, sigma)
    assert result["model_name"] == "EqualWeight"
    assert_valid_portfolio(result, len(mu))
    # All weights should be equal
    n = len(mu)
    expected_w = 1.0 / n
    assert all(abs(w - expected_w) < 1e-6 for w in result["weights"]), "Weights not equal"


def test_risk_parity(synthetic_data):
    tickers, mu, sigma = synthetic_data
    result = risk_parity(mu, sigma)
    assert result["model_name"] == "RiskParity"
    assert_valid_portfolio(result, len(mu))


def test_compute_metrics(synthetic_data):
    tickers, mu, sigma = synthetic_data
    n = len(mu)
    weights = np.ones(n) / n
    ret, risk, sharpe = compute_metrics(weights, mu, sigma, risk_free_rate=0.04)
    assert np.isfinite(ret)
    assert np.isfinite(risk)
    assert np.isfinite(sharpe)
    assert risk > 0


def test_generate_efficient_frontier(synthetic_data):
    tickers, mu, sigma = synthetic_data
    frontier = generate_efficient_frontier(mu, sigma, n_points=5)

    assert len(frontier) == 5
    risks = [point["expected_risk"] for point in frontier]
    returns = [point["expected_return"] for point in frontier]

    assert risks == sorted(risks)
    assert returns == sorted(returns)
    for point in frontier:
        assert np.isfinite(point["expected_return"])
        assert np.isfinite(point["expected_risk"])
        assert np.isfinite(point["sharpe_ratio"])
        assert abs(point["weights"].sum() - 1.0) < 1e-4


@pytest.mark.parametrize("risk_tol", [1.0, 5.0, 9.0])
def test_run_all_models(synthetic_data, risk_tol):
    tickers, mu, sigma = synthetic_data
    results = run_all_models(mu, sigma, tickers=tickers, risk_tolerance_normalized=risk_tol)

    expected_models = {
        "MinimumVariance",
        "MaximumReturn",
        "UtilityMaximization",
        "LeverageShortSelling",
        "LeverageBorrowing",
        "TurnoverConstrained",
        "MaxSharpeRatio",
        "MeanVariance",
        "EqualWeight",
        "RiskParity",
    }
    assert set(results.keys()) == expected_models, f"Missing models: {expected_models - set(results.keys())}"

    n = len(mu)
    for model_name, result in results.items():
        assert_valid_portfolio(result, n)


def test_factor_model_variants(price_frame_data):
    tickers, prices_df, returns_df, mu, sigma = price_frame_data

    utility_result = factor_utility_maximization(mu, tickers, returns_df=returns_df, risk_aversion=1.5)
    constraint_result = factor_variance_constraint(mu, tickers, returns_df=returns_df, risk_level=0.5)

    assert utility_result["model_name"] == "FactorUtilityMaximization"
    assert constraint_result["model_name"] == "FactorVarianceConstraint"
    assert utility_result["factor_names"][0] == "market"
    assert len(utility_result["factor_names"]) >= 2
    assert utility_result["factor_exposures"].shape[1] == len(utility_result["factor_names"])
    assert constraint_result["factor_covariance"].shape == (
        len(constraint_result["factor_names"]),
        len(constraint_result["factor_names"]),
    )
    assert_valid_portfolio(utility_result, len(mu))
    assert_valid_portfolio(constraint_result, len(mu))


def test_factor_model_variants_accept_explicit_factor_contract(price_frame_data):
    tickers, prices_df, returns_df, mu, sigma = price_frame_data
    factor_exposures = {
        ticker: {"market": 1.0 + (index * 0.05), "quality": 0.2 - (index * 0.03)}
        for index, ticker in enumerate(tickers)
    }
    factor_covariance = {
        "market": {"market": 0.045, "quality": 0.012},
        "quality": {"market": 0.012, "quality": 0.030},
    }
    specific_risk = {ticker: 0.020 + (index * 0.002) for index, ticker in enumerate(tickers)}

    result = factor_utility_maximization(
        mu,
        tickers,
        factor_exposures=factor_exposures,
        factor_covariance=factor_covariance,
        specific_risk=specific_risk,
        risk_aversion=1.2,
    )

    assert result["factor_names"] == ["market", "quality"]
    assert result["factor_exposures"].shape == (len(tickers), 2)
    assert result["factor_covariance"].shape == (2, 2)
    assert result["specific_risk"].shape == (len(tickers), len(tickers))
    assert_valid_portfolio(result, len(mu))


def test_factor_model_variants_reject_incomplete_factor_contract(price_frame_data):
    tickers, prices_df, returns_df, mu, sigma = price_frame_data

    with pytest.raises(ValueError, match="must be provided together"):
        factor_variance_constraint(
            mu,
            tickers,
            factor_exposures={ticker: {"market": 1.0} for ticker in tickers},
            risk_level=0.5,
        )


def test_sector_allocation_transaction_cost_and_integer_models(price_frame_data):
    tickers, prices_df, returns_df, mu, sigma = price_frame_data
    sector_metadata = {
        "AAPL": {"sector": "Technology"},
        "MSFT": {"sector": "Technology"},
        "GOOGL": {"sector": "Communication Services"},
        "JPM": {"sector": "Financials"},
        "SPY": {"sector": "ETF"},
    }
    sector_caps = {"technology": 0.6, "communication_services": 0.3, "financials": 0.4, "etf": 0.2}
    latest_prices = prices_df.iloc[-1].to_numpy(dtype=float)
    lot_sizes = np.array([5, 10, 1, 20, 25], dtype=float)

    sector_result = sector_allocation_mean_variance(
        mu,
        sigma,
        tickers,
        sector_metadata,
        sector_caps,
        risk_level=0.5,
    )
    transaction_result = transaction_cost_rebalancing(
        mu,
        sigma,
        current_weights=np.array([0.25, 0.25, 0.20, 0.15, 0.15]),
        tickers=tickers,
        risk_level=0.5,
        transaction_cost_rate=0.001,
        fixed_ticket_charge=1.0,
        market_impact_coefficient=0.025,
        average_daily_dollar_volume={ticker: 5_000_000.0 for ticker in tickers},
        total_amount=100000.0,
    )
    cardinality_result = cardinality_min_buy_in(mu, sigma, max_positions=3, min_position_weight=0.05)
    round_lot_result = round_lot_allocation(
        mu,
        sigma,
        latest_prices,
        total_amount=100000.0,
        risk_level=0.5,
        lot_sizes=lot_sizes,
    )

    assert sector_result["model_name"] == "SectorAllocation"
    assert transaction_result["model_name"] == "TransactionCostRebalancing"
    assert cardinality_result["model_name"] == "CardinalityMinBuyIn"
    assert round_lot_result["model_name"] == "RoundLotAllocation"

    assert_valid_portfolio(sector_result, len(mu))
    assert_valid_portfolio(transaction_result, len(mu))
    assert transaction_result["cash_weight"] >= 0.0
    assert cardinality_result["open_positions"] <= 3
    assert round_lot_result["cash_weight"] >= 0.0
    assert np.allclose(np.mod(round_lot_result["shares"], lot_sizes), 0.0)
    assert np.allclose(round_lot_result["shares"], round_lot_result["lot_units"] * lot_sizes)


def test_transaction_cost_rebalancing_supports_per_asset_calibration(price_frame_data):
    tickers, prices_df, returns_df, mu, sigma = price_frame_data
    result = transaction_cost_rebalancing(
        mu,
        sigma,
        current_weights=np.array([0.25, 0.20, 0.20, 0.20, 0.15]),
        tickers=tickers,
        risk_level=0.5,
        transaction_cost_model="interactive_brokers_fixed",
        transaction_cost_rate=0.001,
        fixed_ticket_charge=1.0,
        per_asset_transaction_costs={"AAPL": 0.0025, "SPY": 0.0005},
        per_asset_fixed_ticket_charges={"AAPL": 2.5, "SPY": 0.5},
        market_impact_model="piecewise_linear",
        market_impact_coefficient=0.025,
        per_asset_market_impact_coefficients={"AAPL": 0.04, "SPY": 0.01},
        average_daily_dollar_volume={
            "AAPL": 2_000_000.0,
            "MSFT": 7_000_000.0,
            "GOOGL": 8_000_000.0,
            "JPM": 6_000_000.0,
            "SPY": 20_000_000.0,
        },
        impact_adv_floor=5_000_000.0,
        total_amount=100000.0,
    )

    assert result["transaction_cost_model"] == "interactive_brokers_fixed"
    assert len(result["transaction_cost_rates"]) == len(tickers)
    assert len(result["fixed_ticket_charges"]) == len(tickers)
    assert len(result["market_impact_rates"]) == len(tickers)
    assert len(result["combined_penalty_rates"]) == len(tickers)
    assert result["impact_adv_floor"] == 5_000_000.0
    assert result["market_impact_model"] == "piecewise_linear"
    assert result["transaction_cost_rates"][0] > result["transaction_cost_rates"][-1]
    assert result["fixed_ticket_charges"][0] > result["fixed_ticket_charges"][-1]
    assert result["combined_penalty_rates"][0] > result["combined_penalty_rates"][-1]
    assert np.all(result["market_impact_excess_penalty_rates"] >= 0.0)
    assert_valid_portfolio(result, len(mu))


def test_transaction_cost_rebalancing_supports_minimum_commissions(price_frame_data):
    tickers, prices_df, returns_df, mu, sigma = price_frame_data
    result = transaction_cost_rebalancing(
        mu,
        sigma,
        current_weights=np.array([0.24, 0.22, 0.20, 0.19, 0.15]),
        tickers=tickers,
        risk_level=0.5,
        transaction_cost_model="interactive_brokers_tiered",
        transaction_cost_rate=0.0005,
        minimum_commission_charge=0.35,
        per_asset_minimum_commission_charges={"AAPL": 0.75, "SPY": 0.10},
        total_amount=100000.0,
    )

    assert result["transaction_cost_model"] == "interactive_brokers_tiered"
    assert len(result["minimum_commission_charges"]) == len(tickers)
    assert result["minimum_commission_charges"][0] > result["minimum_commission_charges"][-1]
    assert np.all(result["minimum_commission_charge_weights"] >= 0.0)
    assert_valid_portfolio(result, len(mu))


def test_round_lot_allocation_supports_lot_unit_bounds():
    mu = np.array([0.22, 0.08, 0.06])
    sigma = np.array([
        [0.06, 0.01, 0.01],
        [0.01, 0.04, 0.01],
        [0.01, 0.01, 0.03],
    ])
    latest_prices = np.array([10.0, 20.0, 25.0])
    lot_sizes = np.array([5.0, 2.0, 1.0])

    result = round_lot_allocation(
        mu,
        sigma,
        latest_prices,
        total_amount=1000.0,
        risk_level=0.8,
        lot_sizes=lot_sizes,
        minimum_lot_units=np.array([2.0, 0.0, 0.0]),
        maximum_lot_units=np.array([3.0, 4.0, 5.0]),
    )

    assert result["lot_units"][0] in {0.0, 2.0, 3.0}
    assert np.all(result["lot_units"] <= result["maximum_lot_units"] + 1e-8)
    assert result["lot_units"][1] <= 4.0
    assert result["shares"][0] == pytest.approx(result["lot_units"][0] * lot_sizes[0])
    assert_valid_portfolio(result, len(mu))


def test_sector_allocation_excludes_etfs_and_unclassified_assets(price_frame_data):
    tickers, prices_df, returns_df, mu, sigma = price_frame_data
    sector_metadata = {
        "AAPL": {"sector": "Information Technology", "industry": "Consumer Electronics", "assetType": "Equity", "isEtf": False},
        "MSFT": {"sector": "Technology", "industry": "Software - Infrastructure", "assetType": "Equity", "isEtf": False},
        "GOOGL": {"sector": "Communication Services", "industry": "Internet Content & Information", "assetType": "Equity", "isEtf": False},
        "JPM": {"sector": None, "industry": "Banks - Diversified", "assetType": "Equity", "isEtf": False},
        "SPY": {"sector": "Financial Services", "industry": "Exchange Traded Fund", "assetType": "ETF", "isEtf": True},
    }

    result = sector_allocation_mean_variance(
        mu,
        sigma,
        tickers,
        sector_metadata,
        {"technology": 0.7, "communication_services": 0.4, "financials": 0.4},
        risk_level=0.5,
    )

    assert_valid_portfolio(result, len(mu))
    assert result["eligible_tickers"] == ["AAPL", "MSFT", "GOOGL", "JPM"]
    assert result["excluded_tickers"] == ["SPY"]
    assert result["weights"][tickers.index("SPY")] == pytest.approx(0.0, abs=1e-8)
    assert "etf" not in result["sector_weights"]
    assert result["sector_weights"]["financials"] >= 0.0
