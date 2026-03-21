from pydantic import BaseModel, field_validator, Field
from typing import Dict, List, Optional, Union


class OptimizeRequest(BaseModel):
    total_amount: float = Field(..., gt=0, description="Total investment amount in dollars")
    risk_tolerance: Union[float, str] = Field(..., description='0-10 float or "low"/"medium"/"high"')
    investment_horizon: Union[int, str] = Field(..., description='Months as int or "short"/"medium"/"long"')
    tickers: Optional[List[str]] = Field(None, description="Custom tickers list; defaults to diversified set")
    risk_free_rate: Optional[float] = Field(0.04, description="Annual risk-free rate (default 4%)")

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
