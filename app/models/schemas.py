from pydantic import BaseModel, field_validator, Field
from typing import Dict, List, Optional, Union


class OptimizeRequest(BaseModel):
    total_amount: float = Field(..., gt=0, description="Total investment amount in dollars")
    risk_tolerance: Union[float, str] = Field(..., description='0-10 float or "low"/"medium"/"high"')
    investment_horizon: Union[int, str] = Field(..., description='Months as int or "short"/"medium"/"long"')
    tickers: Optional[List[str]] = Field(None, description="Custom tickers list; defaults to diversified set")
    risk_free_rate: Optional[float] = Field(0.04, description="Annual risk-free rate (default 4%)")
    return_estimator: Optional[str] = Field("sample", description="Return estimator: sample or shrunk_mean")
    covariance_estimator: Optional[str] = Field("sample", description="Covariance estimator: sample or diagonal_shrinkage")
    mean_shrinkage: Optional[float] = Field(0.0, ge=0.0, le=1.0, description="Shrinkage intensity for shrunk_mean return estimation")
    covariance_shrinkage: Optional[float] = Field(0.0, ge=0.0, le=1.0, description="Shrinkage intensity for diagonal covariance shrinkage")
    max_gross_exposure: Optional[float] = Field(1.5, ge=1.0, description="Maximum gross exposure for long-short portfolios")
    max_short_exposure: Optional[float] = Field(0.5, ge=0.0, description="Maximum absolute short exposure per asset")
    max_cash_borrow: Optional[float] = Field(0.25, ge=0.0, description="Maximum borrowable cash sleeve as a fraction of portfolio value")
    max_turnover: Optional[float] = Field(0.25, ge=0.0, description="Maximum total turnover relative to the starting portfolio")
    current_weights: Optional[Dict[str, float]] = Field(None, description="Current portfolio weights keyed by ticker for turnover-aware optimization")
    transaction_cost_model: Optional[str] = Field("interactive_brokers_fixed", description="Execution-cost baseline: interactive_brokers_fixed, default, or custom")
    transaction_cost_rate: Optional[float] = Field(0.001, ge=0.0, description="One-way proportional transaction cost rate")
    per_asset_transaction_costs: Optional[Dict[str, float]] = Field(None, description="Optional per-asset one-way transaction cost rates keyed by ticker")
    market_impact_coefficient: Optional[float] = Field(0.025, ge=0.0, description="Linear market-impact coefficient applied to traded notional versus liquidity")
    per_asset_market_impact_coefficients: Optional[Dict[str, float]] = Field(None, description="Optional per-asset market-impact coefficients keyed by ticker")
    impact_adv_floor: Optional[float] = Field(5_000_000.0, gt=0.0, description="Minimum average daily dollar volume used when scaling market impact")
    max_positions: Optional[int] = Field(None, ge=1, description="Maximum number of open positions for cardinality-constrained optimization")
    min_position_weight: Optional[float] = Field(None, ge=0.0, description="Minimum portfolio weight for a newly opened position")
    sector_max_weights: Optional[Dict[str, float]] = Field(None, description="Optional maximum sector weights keyed by normalized sector name")
    factor_exposures: Optional[Dict[str, Dict[str, float]]] = Field(None, description="Optional factor exposures keyed by ticker then factor name")
    factor_covariance: Optional[Dict[str, Dict[str, float]]] = Field(None, description="Optional factor covariance keyed by factor name")
    specific_risk: Optional[Dict[str, float]] = Field(None, description="Optional annualized specific variance keyed by ticker")
    lot_sizes: Optional[Dict[str, int]] = Field(None, description="Optional lot size or minimum tradable unit keyed by ticker")

    @field_validator("risk_tolerance", mode="before")
    @classmethod
    def validate_risk_tolerance(cls, v):
        if isinstance(v, str):
            mapping = {"low": 2.0, "medium": 5.0, "high": 8.0}
            if v.lower() not in mapping:
                raise ValueError('risk_tolerance string must be "low", "medium", or "high"')
            return mapping[v.lower()]
        if not (0 <= float(v) <= 10):
            raise ValueError("risk_tolerance float must be between 0 and 10")
        return float(v)

    @field_validator("investment_horizon", mode="before")
    @classmethod
    def validate_investment_horizon(cls, v):
        if isinstance(v, str):
            mapping = {"short": 6, "medium": 24, "long": 60}
            if v.lower() not in mapping:
                raise ValueError('investment_horizon string must be "short", "medium", or "long"')
            return mapping[v.lower()]
        if int(v) <= 0:
            raise ValueError("investment_horizon months must be positive")
        return int(v)

    @field_validator("return_estimator", mode="before")
    @classmethod
    def validate_return_estimator(cls, v):
        if v is None:
            return "sample"
        value = str(v).strip().lower()
        allowed = {"sample", "shrunk_mean"}
        if value not in allowed:
            raise ValueError(f"return_estimator must be one of {sorted(allowed)}")
        return value

    @field_validator("covariance_estimator", mode="before")
    @classmethod
    def validate_covariance_estimator(cls, v):
        if v is None:
            return "sample"
        value = str(v).strip().lower()
        allowed = {"sample", "diagonal_shrinkage"}
        if value not in allowed:
            raise ValueError(f"covariance_estimator must be one of {sorted(allowed)}")
        return value

    @field_validator("transaction_cost_model", mode="before")
    @classmethod
    def validate_transaction_cost_model(cls, v):
        if v is None:
            return "interactive_brokers_fixed"
        value = str(v).strip().lower()
        allowed = {"interactive_brokers_fixed", "default", "custom"}
        if value not in allowed:
            raise ValueError(f"transaction_cost_model must be one of {sorted(allowed)}")
        return value

    @field_validator("per_asset_transaction_costs", "per_asset_market_impact_coefficients")
    @classmethod
    def validate_non_negative_rate_maps(cls, v):
        if v is None:
            return v
        normalized = {}
        for ticker, rate in v.items():
            numeric_rate = float(rate)
            if numeric_rate < 0.0:
                raise ValueError("per-asset execution-cost inputs must be non-negative")
            normalized[str(ticker).upper().strip()] = numeric_rate
        return normalized

    @field_validator("lot_sizes")
    @classmethod
    def validate_lot_sizes(cls, v):
        if v is None:
            return v
        normalized = {}
        for ticker, lot_size in v.items():
            integer_lot_size = int(lot_size)
            if integer_lot_size <= 0:
                raise ValueError("lot_sizes must contain positive integers")
            normalized[str(ticker).upper().strip()] = integer_lot_size
        return normalized


class PortfolioResult(BaseModel):
    rank: int
    model_name: str
    model_description: str
    weights: Dict[str, float]
    expected_annual_return: float
    expected_annual_risk: float
    sharpe_ratio: float
    allocation: Dict[str, float]
    applicability_score: float
    reasoning: str


class FrontierPoint(BaseModel):
    target_return: float
    expected_return: float
    expected_risk: float
    sharpe_ratio: float


class OptimizeResponse(BaseModel):
    total_amount: float
    risk_tolerance_normalized: float
    investment_horizon_months: int
    portfolios: List[PortfolioResult]
    efficient_frontier: List[FrontierPoint]
    data_period_used: str
    optimization_status: str
