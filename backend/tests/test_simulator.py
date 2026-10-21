import numpy as np
import pytest

from app.core.market import MarketContext
from app.core.order import ImpactParams, ParentOrder
from app.core.simulator import simulate
from app.core.strategies import TWAP
from app.core.tca import implementation_shortfall


def flat_ctx(n=10, price=100.0):
    return MarketContext(prices=np.full(n, price), volume=np.ones(n), sigma=0.0)


def run(side, impact):
    o = ParentOrder("X", side, 1000.0, 10, 100.0)
    c = flat_ctx()
    return o, simulate(o, TWAP().trajectory(o, c), c, impact)


def test_zero_impact_flat_prices_no_cost():
    _, res = run("buy", ImpactParams(gamma=0, eta=0, epsilon=0))
    assert res.avg_price == pytest.approx(100.0)
    assert implementation_shortfall(res)["implementation_shortfall_bps"] == pytest.approx(0.0, abs=1e-9)


def test_spread_only_cost():
    _, res = run("buy", ImpactParams(gamma=0, eta=0, epsilon=0.05))
    tca = implementation_shortfall(res)
    assert tca["spread_cost_bps"] == pytest.approx(5.0)  # 1e4 * 0.05 / 100
    assert tca["implementation_shortfall_bps"] == pytest.approx(5.0)


def test_permanent_impact_moves_price():
    _, res = run("buy", ImpactParams(gamma=1e-3, eta=0, epsilon=0))
    assert res.fills[-1].exec_price > res.fills[0].exec_price


def test_sell_side_executes_below_arrival():
    _, res = run("sell", ImpactParams(gamma=0, eta=0, epsilon=0.05))
    assert res.avg_price < 100.0
    assert implementation_shortfall(res)["spread_cost_bps"] == pytest.approx(5.0)
