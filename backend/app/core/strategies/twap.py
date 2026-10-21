"""Time-Weighted Average Price: equal slices across time."""
from __future__ import annotations

import numpy as np

from ..market import MarketContext
from ..order import ParentOrder
from .base import ExecutionStrategy


class TWAP(ExecutionStrategy):
    name = "TWAP"

    def trajectory(self, order: ParentOrder, context: MarketContext) -> np.ndarray:
        n = order.n_intervals
        return np.full(n, order.total_qty / n)
