"""Almgren-Chriss optimal execution (closed-form linear-impact trajectory)."""
from __future__ import annotations

import numpy as np

from ..market import MarketContext
from ..order import ParentOrder
from .base import ExecutionStrategy


class AlmgrenChriss(ExecutionStrategy):
    name = "AlmgrenChriss"

    def __init__(self, risk_aversion: float = 1e-6, eta: float = 1e-5) -> None:
        if risk_aversion < 0 or eta <= 0:
            raise ValueError("require risk_aversion >= 0 and eta > 0")
        self.risk_aversion = risk_aversion
        self.eta = eta

    def kappa(self, sigma: float, n: int) -> float:
        sigma = sigma if sigma > 0 else 1.0
        k = float(np.sqrt(self.risk_aversion * sigma**2 / self.eta))
        # cap to keep sinh numerically stable
        return min(k, 50.0 / max(n, 1))

    def trajectory(self, order: ParentOrder, context: MarketContext) -> np.ndarray:
        n = order.n_intervals
        qty = order.total_qty
        k = self.kappa(context.sigma, n)
        if k < 1e-8:
            return np.full(n, qty / n)  # risk-neutral limit -> TWAP

        j = np.arange(0, n + 1)
        holdings = qty * np.sinh(k * (n - j)) / np.sinh(k * n)
        return -np.diff(holdings)  # shares traded each interval (positive)
