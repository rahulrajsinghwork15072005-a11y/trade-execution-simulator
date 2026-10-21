"""Strategy interface."""
from __future__ import annotations

import numpy as np

from ..market import MarketContext
from ..order import ParentOrder


class ExecutionStrategy:
    """Maps a parent order + market context to a child-order trajectory.

    A trajectory is an array of shares to trade in each interval, summing to the
    parent order quantity.
    """

    name: str = "base"

    def trajectory(self, order: ParentOrder, context: MarketContext) -> np.ndarray:
        raise NotImplementedError

    @staticmethod
    def _finalize(x: np.ndarray, total_qty: float) -> np.ndarray:
        """Clip negatives and rescale so the trajectory sums exactly to ``total_qty``."""
        x = np.clip(np.asarray(x, dtype=float), 0.0, None)
        s = x.sum()
        if s <= 0:
            return np.full(x.size, total_qty / x.size)
        return x * (total_qty / s)
