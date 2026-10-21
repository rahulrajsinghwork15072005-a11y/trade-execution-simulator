"""Tests for the configurable non-linear (square-root law) temporary impact.

``psi`` is the temporary-impact power: ``1.0`` is the existing linear model and
``0.5`` reproduces the empirical square-root law. These tests confirm psi=1
reproduces the linear model exactly, that the implementation-shortfall
decomposition still reconciles for any psi, and that square-root impact is
concave (cheaper per slice at high trading rates).
"""
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.core.market import MarketContext
from app.core.order import ImpactParams, ParentOrder
from app.core.simulator import simulate
from app.core.strategies import TWAP
from app.core.tca import cost_risk, implementation_shortfall
from app.main import app

client = TestClient(app)


def _flat_ctx(n: int = 10, price: float = 100.0) -> MarketContext:
    return MarketContext(prices=np.full(n, price), volume=np.ones(n), sigma=0.0)


def _run(side: str, impact: ImpactParams, qty: float = 1000.0, n: int = 10):
    order = ParentOrder("X", side, qty, n, 100.0)
    ctx = _flat_ctx(n)
    return simulate(order, TWAP().trajectory(order, ctx), ctx, impact)


def test_psi_one_matches_linear():
    """psi=1.0 is the existing linear model: temporary impact = eta * rate."""
    res = _run("buy", ImpactParams(gamma=0, eta=1e-3, epsilon=0, psi=1.0))
    for f in res.fills:
        assert f.exec_price == pytest.approx(100.0 + 1e-3 * f.rate)


def test_sqrt_law_reconciles_exactly():
    res = _run("buy", ImpactParams(gamma=2e-4, eta=1e-3, epsilon=0.01, psi=0.5))
    tca = implementation_shortfall(res)
    assert tca["reconciliation_error_bps"] == pytest.approx(0.0, abs=1e-9)
    components = (
        tca["spread_cost_bps"]
        + tca["temporary_impact_bps"]
        + tca["permanent_impact_bps"]
        + tca["timing_bps"]
    )
    assert components == pytest.approx(tca["implementation_shortfall_bps"], abs=1e-9)


def test_sqrt_law_is_concave_cheaper_at_high_rates():
    """For trading rates > 1, square-root impact costs less than linear."""
    eta = 1e-3
    linear = implementation_shortfall(_run("buy", ImpactParams(gamma=0, eta=eta, epsilon=0)))
    sqrt = implementation_shortfall(
        _run("buy", ImpactParams(gamma=0, eta=eta, epsilon=0, psi=0.5))
    )
    assert sqrt["temporary_impact_bps"] < linear["temporary_impact_bps"]
    # rate=100 each slice, so sqrt term = eta*10 vs linear eta*100 (10x smaller).
    assert sqrt["temporary_impact_bps"] == pytest.approx(
        linear["temporary_impact_bps"] / 10.0, rel=1e-6
    )


def test_cost_risk_uses_psi():
    x = np.array([100.0, 100.0, 100.0])
    cost_lin, _ = cost_risk(x, ImpactParams(gamma=0, eta=1e-3, epsilon=0, psi=1.0), sigma=0.0)
    cost_sqrt, _ = cost_risk(x, ImpactParams(gamma=0, eta=1e-3, epsilon=0, psi=0.5), sigma=0.0)
    assert cost_lin == pytest.approx(1e-3 * np.sum(x**2))
    assert cost_sqrt == pytest.approx(1e-3 * np.sum(x**1.5))
    assert cost_sqrt < cost_lin


def test_api_simulate_accepts_psi():
    body = {
        "strategy": "TWAP",
        "order": {"side": "buy", "total_qty": 100000, "n_intervals": 20, "arrival_price": 100},
        "impact": {"gamma": 1e-6, "eta": 1e-5, "epsilon": 0.01, "psi": 0.5},
    }
    resp = client.post("/api/simulate", json=body)
    assert resp.status_code == 200
    assert "tca" in resp.json()


def test_api_rejects_out_of_range_psi():
    resp = client.post("/api/simulate", json={"impact": {"psi": 1.5}})
    assert resp.status_code == 422
