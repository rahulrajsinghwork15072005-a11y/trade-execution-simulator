import numpy as np

from app.core.market import make_market
from app.core.order import ImpactParams, ParentOrder
from app.core.simulator import simulate
from app.core.strategies import VWAP, AlmgrenChriss
from app.core.tca import ac_frontier, cost_risk, implementation_shortfall


def test_reconciliation_is_exact():
    o = ParentOrder("X", "buy", 100_000.0, 30, 100.0)
    ctx = make_market(n=30, arrival=100.0, sigma=0.05, seed=2)
    res = simulate(o, VWAP().trajectory(o, ctx), ctx, ImpactParams())
    tca = implementation_shortfall(res)
    assert abs(tca["reconciliation_error_bps"]) < 1e-6


def test_cost_risk_tradeoff():
    o = ParentOrder("X", "buy", 100_000.0, 30, 100.0)
    ctx = make_market(n=30, arrival=100.0, sigma=0.05, seed=2)
    imp = ImpactParams()
    x_slow = AlmgrenChriss(risk_aversion=0.0, eta=1e-5).trajectory(o, ctx)
    x_fast = AlmgrenChriss(risk_aversion=1e-3, eta=1e-5).trajectory(o, ctx)
    e_slow, v_slow = cost_risk(x_slow, imp, ctx.sigma)
    e_fast, v_fast = cost_risk(x_fast, imp, ctx.sigma)
    assert v_fast < v_slow   # front-loading reduces timing risk
    assert e_fast > e_slow   # ... at a higher expected impact cost


def test_frontier_monotonic():
    o = ParentOrder("X", "buy", 100_000.0, 30, 100.0)
    ctx = make_market(n=30, arrival=100.0, sigma=0.05, seed=2)
    pts = ac_frontier(o, ctx, ImpactParams(), list(np.logspace(-8, -4, 10)))
    expected = [p["expected_cost"] for p in pts]
    variance = [p["variance"] for p in pts]
    assert expected[-1] >= expected[0]
    assert variance[-1] <= variance[0]
