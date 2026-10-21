from app.data.market_data import fetch_market
from app.live import live_simulate


def test_fetch_market_offline_synthetic():
    ctx, source, arrival = fetch_market("AAPL", allow_network=False)
    assert source == "synthetic"
    assert arrival == 100.0
    assert len(ctx.prices) == 30


def test_live_simulate_offline_runs():
    out = live_simulate("AAPL", strategy="VWAP", allow_network=False)
    assert out["source"] == "synthetic"
    assert "tca" in out
    assert "benchmarks" in out


def test_live_simulate_almgren():
    out = live_simulate("MSFT", strategy="AlmgrenChriss", allow_network=False)
    assert out["strategy"] == "AlmgrenChriss"
