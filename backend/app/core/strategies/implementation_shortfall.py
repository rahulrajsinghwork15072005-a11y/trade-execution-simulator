"""Implementation Shortfall: front-load trading to reduce timing (price) risk."""
from __future__ import annotations

import numpy as np

from ..market import MarketContext
from ..order import ParentOrder
from .base import ExecutionStrategy


class ImplementationShortfall(ExecutionStrategy):
    """Exponentially front-loaded schedule.

    Trades a larger share early to cut exposure to adverse price drift between the
    decision (arrival) price and completion. ``urgency`` controls front-loading:
    ``urgency = 0`` reduces to TWAP (uniform); larger values trade earlier.
    """

    name = "IS"

    def __init__(self, urgency: float = 2.0) -> None:
        if urgency < 0:
            raise ValueError("urgency must be >= 0")
        self.urgency = urgency

    def trajectory(self, order: ParentOrder, context: MarketContext) -> np.ndarray:
        n = int(order.n_intervals)
        j = np.arange(n, dtype=float)
        denom = max(n - 1, 1)
        weights = np.exp(-self.urgency * j / denom)
        return self._finalize(weights, order.total_qty)
