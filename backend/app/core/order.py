"""Parent order and market-impact parameter types."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParentOrder:
    symbol: str
    side: str            # "buy" | "sell"
    total_qty: float
    n_intervals: int
    arrival_price: float

    def __post_init__(self) -> None:
        if self.side not in ("buy", "sell"):
            raise ValueError("side must be 'buy' or 'sell'")
        if self.total_qty <= 0:
            raise ValueError("total_qty must be positive")
        if self.n_intervals < 1:
            raise ValueError("n_intervals must be >= 1")
        if self.arrival_price <= 0:
            raise ValueError("arrival_price must be positive")

    @property
    def sign(self) -> float:
        return 1.0 if self.side == "buy" else -1.0


@dataclass(frozen=True)
class ImpactParams:
    """Almgren-Chriss style impact with a configurable temporary-impact power.

    ``gamma`` permanent impact per share, ``eta`` temporary impact per unit
    trading rate, ``epsilon`` fixed half-spread cost per share, and ``psi`` the
    temporary-impact power: ``1.0`` is the classic linear model, while ``0.5``
    reproduces the empirical **square-root law** (temporary cost grows like the
    square root of the trading rate, so large slices are penalised concavely).
    """

    gamma: float = 1e-6
    eta: float = 1e-5
    epsilon: float = 0.01
    psi: float = 1.0
