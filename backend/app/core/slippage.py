"""Slippage versus benchmarks (in basis points, sign-adjusted by side)."""
from __future__ import annotations


def slippage_bps(avg_price: float, benchmark: float, side: str) -> float:
    """Positive = unfavorable (paid above benchmark on a buy / below on a sell)."""
    sign = 1.0 if side == "buy" else -1.0
    if benchmark <= 0:
        return float("nan")
    return 1e4 * sign * (avg_price - benchmark) / benchmark


def all_slippages(avg_price: float, benchmarks: dict[str, float], side: str) -> dict[str, float]:
    return {name: slippage_bps(avg_price, value, side) for name, value in benchmarks.items()}
