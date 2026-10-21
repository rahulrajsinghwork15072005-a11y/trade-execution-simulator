"""Alternative (non-linear) market-impact models."""
from __future__ import annotations

import math


def square_root_impact_bps(participation_rate: float, sigma: float, coefficient: float = 1.0) -> float:
    """Empirical square-root impact law: ``Y * sigma * sqrt(participation)`` in bps.

    ``participation_rate`` is order size as a fraction of market volume (Q/V) and
    ``sigma`` is the (fractional) volatility over the horizon.
    """
    if participation_rate < 0:
        raise ValueError("participation_rate must be non-negative")
    return float(coefficient * sigma * math.sqrt(participation_rate) * 1e4)
