"""Real intraday market data (yfinance) for execution, with synthetic fallback."""
from __future__ import annotations

import hashlib

import numpy as np

from ..core.market import MarketContext, make_market

try:  # optional dependency
    import yfinance as _yf

    _HAS_YF = True
except Exception:  # pragma: no cover - import guard
    _HAS_YF = False


def _stable_seed(text: str) -> int:
    return int.from_bytes(hashlib.md5(text.encode()).digest()[:4], "little") % 100_000


def fetch_market(
    ticker: str, period: str = "5d", interval: str = "30m", allow_network: bool = True
) -> tuple[MarketContext, str, float]:
    """Return ``(context, source, arrival_price)`` from real bars or synthetic data."""
    if allow_network and _HAS_YF:
        try:  # pragma: no cover - network path
            frame = _yf.Ticker(ticker).history(period=period, interval=interval)
            closes = frame["Close"].dropna()
            if len(closes) >= 10:
                prices = closes.to_numpy(dtype=float)
                volume = frame["Volume"].reindex(closes.index).fillna(0).to_numpy(dtype=float)
                volume = np.maximum(volume, 1.0)
                sigma = float(np.std(np.diff(prices))) or 0.05
                context = MarketContext(prices=prices, volume=volume, sigma=sigma)
                return context, "yfinance", float(prices[0])
        except Exception:  # pragma: no cover - network/parse failures
            pass
    context = make_market(n=30, arrival=100.0, sigma=0.05, seed=_stable_seed(ticker))
    return context, "synthetic", 100.0
