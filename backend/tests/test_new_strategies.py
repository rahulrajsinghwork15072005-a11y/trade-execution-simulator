"""Tests for the Implementation-Shortfall and Adaptive-POV execution strategies."""
from __future__ import annotations

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.core.market import MarketContext, make_market
from app.core.order import ParentOrder
from app.core.strategies import AdaptivePOV, ImplementationShortfall, POV
from app.main import app

client = TestClient(app)


def _order(qty: float = 100_000.0, n: int = 30) -> ParentOrder:
    return ParentOrder("ACME", "buy", qty, n, 100.0)


def test_is_sums_to_qty_and_front_loads():
    ctx = make_market(n=10, arrival=100.0, sigma=0.05, seed=1)
    traj = ImplementationShortfall(urgency=3.0).trajectory(_order(1000.0, 10), ctx)
    assert traj.sum() == pytest.approx(1000.0)
    assert traj[0] > traj[-1]


def test_is_zero_urgency_is_uniform():
    ctx = make_market(n=10, arrival=100.0, sigma=0.05, seed=1)
    traj = ImplementationShortfall(urgency=0.0).trajectory(_order(1000.0, 10), ctx)
    assert np.allclose(traj, traj[0])


def test_is_rejects_negative_urgency():
    with pytest.raises(ValueError):
        ImplementationShortfall(urgency=-1.0)


def test_adaptive_pov_concentrates_in_high_volume():
    vol = np.array([1.0, 1.0, 1.0, 10.0, 1.0, 1.0])
    ctx = MarketContext(prices=np.full(vol.size, 100.0), volume=vol, sigma=0.05)
    order = _order(1000.0, vol.size)  # large qty => no early cap (under-fill path)
    pov = POV(0.1).trajectory(order, ctx)
    adp = AdaptivePOV(0.1, aggressiveness=1.0).trajectory(order, ctx)
    spike = 3
    assert adp[spike] > pov[spike]
    assert adp.sum() == pytest.approx(1000.0)
    assert pov.sum() == pytest.approx(1000.0)


def test_adaptive_pov_zero_aggressiveness_matches_pov():
    ctx = make_market(n=20, arrival=100.0, sigma=0.05, seed=2)
    order = _order(50_000.0, 20)
    pov = POV(0.2).trajectory(order, ctx)
    adp = AdaptivePOV(0.2, aggressiveness=0.0).trajectory(order, ctx)
    assert np.allclose(pov, adp)


def test_adaptive_pov_rejects_bad_params():
    with pytest.raises(ValueError):
        AdaptivePOV(participation=0.0)
    with pytest.raises(ValueError):
        AdaptivePOV(aggressiveness=-1.0)


def test_new_strategies_listed_and_runnable():
    listed = client.get("/api/strategies").json()["strategies"]
    assert "IS" in listed and "AdaptivePOV" in listed
    for strat in ("IS", "AdaptivePOV"):
        resp = client.get(f"/api/demo/simulate?strategy={strat}")
        assert resp.status_code == 200
        assert resp.json()["strategy"] == strat
