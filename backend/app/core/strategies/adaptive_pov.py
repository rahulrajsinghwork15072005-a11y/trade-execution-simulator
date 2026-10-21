"""Adaptive (liquidity-seeking) Percentage-of-Volume execution."""
from __future__ import annotations

import numpy as np

from ..market import MarketContext
from ..order import ParentOrder
from .base import ExecutionStrategy


class AdaptivePOV(ExecutionStrategy):
    """POV that trades proportionally *more* in high-volume intervals.

    ``aggressiveness = 0`` recovers vanilla POV (linear in volume); larger values
    concentrate trading where liquidity is deepest. The cumulative cap and final
    completion match :class:`POV`.
    """

    name = "AdaptivePOV"

    def __init__(self, participation: float = 0.2, aggressiveness: float = 1.0) -> None:
        if not 0 < participation <= 1:
            raise ValueError("participation must be in (0, 1]")
        if aggressiveness < 0:
            raise ValueError("aggressiveness must be >= 0")
        self.participation = participation
        self.aggressiveness = aggressiveness

    def trajectory(self, order: ParentOrder, context: MarketContext) -> np.ndarray:
        vol = np.asarray(context.volume, dtype=float)
        mean = vol.mean() if vol.size and vol.mean() > 0 else 1.0
        weight = (vol / mean) ** self.aggressiveness
        raw = self.participation * vol * weight
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
            x[-1] += qty - x.sum()
        return x
