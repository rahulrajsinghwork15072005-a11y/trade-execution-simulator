"""Execution-cost risk metrics: Value-at-Risk and Conditional VaR."""
from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike


def cost_var(samples: ArrayLike, alpha: float = 0.95) -> float:
    """Value-at-Risk: the ``alpha`` quantile of the cost distribution (bps).

    Costs are oriented so that larger = worse, so VaR is an upper quantile.
    """
    arr = np.asarray(samples, dtype=float)
    if arr.size == 0:
        return 0.0
    return float(np.percentile(arr, alpha * 100.0))


def cost_cvar(samples: ArrayLike, alpha: float = 0.95) -> float:
    """Conditional VaR (expected shortfall): mean cost in the worst tail."""
    arr = np.asarray(samples, dtype=float)
    if arr.size == 0:
        return 0.0
    var = np.percentile(arr, alpha * 100.0)
    tail = arr[arr >= var]
    return float(tail.mean()) if tail.size else float(var)
