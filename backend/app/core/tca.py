"""Transaction-cost analysis: implementation-shortfall decomposition + frontier."""
from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from .order import ImpactParams, ParentOrder
from .market import MarketContext
from .simulator import ExecutionResult


def implementation_shortfall(result: ExecutionResult) -> dict[str, float]:
    """Decompose implementation shortfall (bps of arrival) into cost sources.

    The components (spread, temporary impact, permanent impact, timing) sum to
    the total implementation shortfall by construction.
    """
    qty = result.total_qty
    arrival = result.arrival_price
    sign = 1.0 if result.side == "buy" else -1.0
    if qty <= 0:
        return {
            "implementation_shortfall_bps": 0.0,
            "spread_cost_bps": 0.0,
            "temporary_impact_bps": 0.0,
            "permanent_impact_bps": 0.0,
            "timing_bps": 0.0,
            "reconciliation_error_bps": 0.0,
        }

    avg_exec = result.avg_price
    avg_base = sum(f.qty * f.base_price for f in result.fills) / qty
    avg_cum = sum(f.qty * f.cum_before for f in result.fills) / qty
    imp = result.impact
    # Quantity-weighted average of the (possibly non-linear) temporary-impact term
    # so the decomposition reconciles exactly for any psi (psi=1 -> linear rate).
    avg_temp_term = sum(f.qty * f.rate**imp.psi for f in result.fills) / qty

    def to_bps(x: float) -> float:
        return 1e4 * x / arrival

    spread = to_bps(imp.epsilon)
    temporary = to_bps(imp.eta * avg_temp_term)
    permanent = to_bps(imp.gamma * avg_cum)
    timing = to_bps(sign * (avg_base - arrival))
    total = to_bps(sign * (avg_exec - arrival))

    return {
        "implementation_shortfall_bps": total,
        "spread_cost_bps": spread,
        "temporary_impact_bps": temporary,
        "permanent_impact_bps": permanent,
        "timing_bps": timing,
        "reconciliation_error_bps": total - (spread + temporary + permanent + timing),
    }


def cost_risk(trajectory: ArrayLike, impact: ImpactParams, sigma: float) -> tuple[float, float]:
    """Almgren-Chriss expected cost and variance of cost for a trajectory."""
    x = np.asarray(trajectory, dtype=float)
    qty = float(x.sum())
    holdings = np.concatenate([[qty], qty - np.cumsum(x)])  # X_0 .. X_n
    expected_cost = (
        0.5 * impact.gamma * qty**2
        + impact.epsilon * np.sum(np.abs(x))
        + impact.eta * np.sum(np.abs(x) ** (impact.psi + 1.0))
    )
    variance = sigma**2 * float(np.sum(holdings[1:] ** 2))
    return float(expected_cost), variance


def ac_frontier(
    order: ParentOrder,
    context: MarketContext,
    impact: ImpactParams,
    risk_aversions: list[float],
) -> list[dict[str, float]]:
    """Trace the Almgren-Chriss efficient frontier over a risk-aversion grid."""
    from .strategies import AlmgrenChriss

    points: list[dict[str, float]] = []
    for lam in risk_aversions:
        x = AlmgrenChriss(risk_aversion=lam, eta=impact.eta).trajectory(order, context)
        expected, variance = cost_risk(x, impact, context.sigma)
        points.append(
            {
                "risk_aversion": float(lam),
                "expected_cost": expected,
                "variance": variance,
                "std": variance**0.5,
            }
        )
    return points
