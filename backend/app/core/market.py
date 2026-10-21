"""Market context: price path + volume profile over the execution window."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MarketContext:
    prices: np.ndarray      # unaffected mid price per interval (length n)
    volume: np.ndarray      # market volume per interval (length n)
    sigma: float            # per-interval price volatility (price units)

    @property
    def volume_profile(self) -> np.ndarray:
        total = self.volume.sum()
        return self.volume / total if total > 0 else np.full_like(self.volume, 1.0 / self.volume.size)


def u_shape_volume(n: int, total: float = 1_000_000.0, depth: float = 3.0) -> np.ndarray:
    """Classic U-shaped intraday volume profile (heavy at open/close)."""
    x = np.linspace(0.0, 1.0, n)
    weights = 1.0 + depth * (2.0 * x - 1.0) ** 2
    weights /= weights.sum()
    return weights * total


def make_market(
    n: int = 30,
    arrival: float = 100.0,
    sigma: float = 0.05,
    drift: float = 0.0,
    seed: int = 0,
    total_volume: float = 1_000_000.0,
) -> MarketContext:
    """Synthetic market: a random-walk price path and a U-shaped volume curve."""
    rng = np.random.default_rng(seed)
    innovations = rng.normal(0.0, sigma, n)
    prices = arrival + np.cumsum(innovations) + drift * np.arange(n)
    prices = np.maximum(prices, 0.01)
    volume = u_shape_volume(n, total=total_volume)
    return MarketContext(prices=prices, volume=volume, sigma=sigma)
