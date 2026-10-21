"""Volume-Weighted Average Price: slice in proportion to the volume curve."""
from __future__ import annotations

import numpy as np

from ..market import MarketContext
from ..order import ParentOrder
from .base import ExecutionStrategy


class VWAP(ExecutionStrategy):
    name = "VWAP"

    def trajectory(self, order: ParentOrder, context: MarketContext) -> np.ndarray:
        return order.total_qty * context.volume_profile
