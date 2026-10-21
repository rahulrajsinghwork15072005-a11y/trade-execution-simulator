"""Live execution simulation over real intraday bars."""
from __future__ import annotations

from .core.order import ParentOrder
from .data.market_data import fetch_market
from .demo import default_impact, make_strategy, run


def live_simulate(
    ticker: str,
    strategy: str = "VWAP",
    qty: float = 100_000.0,
    side: str = "buy",
    allow_network: bool = True,
) -> dict:
    context, source, arrival = fetch_market(ticker, allow_network=allow_network)
    n = len(context.prices)
    order = ParentOrder(ticker, side, qty, n, arrival)
    result = run(order, default_impact(), context, make_strategy(strategy))
    return {"ticker": ticker, "source": source, "n_intervals": n, "arrival": arrival, **result}
