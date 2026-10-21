import pytest

from app.core.benchmarks import compute_benchmarks
from app.core.slippage import slippage_bps


def test_benchmarks_basic():
    b = compute_benchmarks([100, 101, 102, 103], [1, 1, 1, 1])
    assert b["arrival"] == 100
    assert b["close"] == 103
    assert b["twap"] == pytest.approx(101.5)
    assert b["vwap"] == pytest.approx(101.5)


def test_vwap_is_volume_weighted():
    b = compute_benchmarks([100, 200], [3, 1])
    assert b["vwap"] == pytest.approx((100 * 3 + 200 * 1) / 4)


def test_slippage_signs():
    assert slippage_bps(101, 100, "buy") == pytest.approx(100.0)
    assert slippage_bps(99, 100, "sell") == pytest.approx(100.0)
    assert slippage_bps(99, 100, "buy") == pytest.approx(-100.0)
