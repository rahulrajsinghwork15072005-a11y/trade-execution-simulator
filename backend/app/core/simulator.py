"""Execute a trajectory against a market tape, applying the impact model."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .market import MarketContext
from .order import ImpactParams, ParentOrder


@dataclass(frozen=True)
class Fill:
    interval: int
    qty: float
    base_price: float
    exec_price: float
    cum_before: float
    rate: float


@dataclass
class ExecutionResult:
    fills: list[Fill]
    avg_price: float
    total_qty: float
    side: str
    arrival_price: float
    impact: ImpactParams
    sigma: float
    base_prices: list[float]
    volume: list[float]


def simulate(
    order: ParentOrder,
    trajectory: np.ndarray,
    context: MarketContext,
    impact: ImpactParams,
) -> ExecutionResult:
    """Run the schedule and produce per-interval fills.

    Permanent impact shifts the effective mid persistently; temporary impact
    (half-spread + rate term) is paid only on the executing slice.
    """
    sign = order.sign
    base = np.asarray(context.prices, dtype=float)
    n = len(trajectory)
    if base.size < n:
        raise ValueError("price path is shorter than the trajectory")

    fills: list[Fill] = []
    cum_before = 0.0
    for j in range(n):
        xj = float(trajectory[j])
        rate = xj  # interval length tau = 1
        perm_shift = impact.gamma * cum_before
        base_j = float(base[j])
        mid_eff = base_j + sign * perm_shift
        temp_impact = impact.eta * rate**impact.psi
        exec_price = mid_eff + sign * (impact.epsilon + temp_impact)
        fills.append(Fill(j, xj, base_j, exec_price, cum_before, rate))
        cum_before += xj

    qty = sum(f.qty for f in fills)
    avg = sum(f.qty * f.exec_price for f in fills) / qty if qty > 0 else float("nan")
    return ExecutionResult(
        fills=fills,
        avg_price=avg,
        total_qty=qty,
        side=order.side,
        arrival_price=order.arrival_price,
        impact=impact,
        sigma=context.sigma,
        base_prices=base[:n].tolist(),
        volume=np.asarray(context.volume, dtype=float)[:n].tolist(),
    )
