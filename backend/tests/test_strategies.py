import numpy as np
import pytest

from app.core.market import make_market
from app.core.order import ParentOrder
from app.core.strategies import POV, TWAP, VWAP, AlmgrenChriss


def order():
    return ParentOrder("X", "buy", 100_000.0, 30, 100.0)


def ctx():
    return make_market(n=30, arrival=100.0, sigma=0.05, seed=1)


def test_twap_equal_slices():
    x = TWAP().trajectory(order(), ctx())
    assert np.allclose(x, 100_000 / 30)
    assert x.sum() == pytest.approx(100_000)


def test_vwap_matches_volume_profile():
    c = ctx()
    x = VWAP().trajectory(order(), c)
    np.testing.assert_allclose(x / x.sum(), c.volume / c.volume.sum())
    assert x.sum() == pytest.approx(100_000)


def test_pov_sums_to_qty():
    x = POV(0.2).trajectory(order(), ctx())
    assert x.sum() == pytest.approx(100_000)
    assert (x >= 0).all()


def test_ac_sums_to_qty():
    x = AlmgrenChriss(risk_aversion=2e-6, eta=1e-5).trajectory(order(), ctx())
    assert x.sum() == pytest.approx(100_000)


def test_ac_riskneutral_is_twap():
    x = AlmgrenChriss(risk_aversion=0.0, eta=1e-5).trajectory(order(), ctx())
    assert np.allclose(x, 100_000 / 30)


def test_ac_riskaverse_frontloads():
    x = AlmgrenChriss(risk_aversion=1e-3, eta=1e-5).trajectory(order(), ctx())
    assert x[0] > x[-1]
    assert x.sum() == pytest.approx(100_000)
