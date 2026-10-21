"""Percentage-of-Volume: trade a fixed share of each interval's volume."""
from __future__ import annotations

import numpy as np

from ..market import MarketContext
from ..order import ParentOrder
from .base import ExecutionStrategy


class POV(ExecutionStrategy):
    name = "POV"

    def __init__(self, participation: float = 0.2) -> None:
        if not 0 < participation <= 1:
            raise ValueError("participation must be in (0, 1]")
        self.participation = participation

    def trajectory(self, order: ParentOrder, context: MarketContext) -> np.ndarray:
        raw = self.participation * context.volume
        cum = np.cumsum(raw)
        qty = order.total_qty
        x = raw.copy()

        over = cum > qty
        if over.any():
            idx = int(np.argmax(over))
            prior = cum[idx] - raw[idx]
            x[idx] = max(qty - prior, 0.0)
            x[idx + 1:] = 0.0
        else:
            # under-fills at this participation: complete in the last interval
            x[-1] += qty - x.sum()
        return x
