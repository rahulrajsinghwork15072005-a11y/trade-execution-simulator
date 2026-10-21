"""Execution benchmarks."""
from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike


def compute_benchmarks(prices: ArrayLike, volume: ArrayLike) -> dict[str, float]:
    """Arrival, interval-VWAP, TWAP, and close benchmarks for a window."""
    p = np.asarray(prices, dtype=float)
    v = np.asarray(volume, dtype=float)
    vol_sum = v.sum()
    return {
        "arrival": float(p[0]),
        "twap": float(p.mean()),
        "vwap": float((p * v).sum() / vol_sum) if vol_sum > 0 else float(p.mean()),
        "close": float(p[-1]),
    }
