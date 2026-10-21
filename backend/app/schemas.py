"""Pydantic schemas for the execution simulator API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class OrderModel(BaseModel):
    symbol: str = "ACME"
    side: str = Field("buy", pattern="^(buy|sell)$")
    total_qty: float = Field(100_000.0, gt=0)
    n_intervals: int = Field(30, ge=1, le=500)
    arrival_price: float = Field(100.0, gt=0)


class ImpactModel(BaseModel):
    gamma: float = Field(1e-6, ge=0)
    eta: float = Field(1e-5, gt=0)
    epsilon: float = Field(0.01, ge=0)
    psi: float = Field(
        1.0, gt=0, le=1.0, description="Temporary-impact power: 1=linear, 0.5=square-root law"
    )


class MarketModel(BaseModel):
    sigma: float = Field(0.05, ge=0)
    drift: float = 0.0
    seed: int = 1
    total_volume: float = Field(1_000_000.0, gt=0)


class SimulateRequest(BaseModel):
    strategy: str = Field("VWAP", pattern="^(TWAP|VWAP|POV|AlmgrenChriss|IS|AdaptivePOV)$")
    order: OrderModel = OrderModel()
    impact: ImpactModel = ImpactModel()
    market: MarketModel = MarketModel()
    participation: float = Field(0.2, gt=0, le=1)
    risk_aversion: float = Field(2e-6, ge=0)
