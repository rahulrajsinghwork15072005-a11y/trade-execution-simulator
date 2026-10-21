from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/api/health").json()["status"] == "ok"


def test_dashboard():
    r = client.get("/")
    assert r.status_code == 200
    assert "Execution" in r.text


def test_strategies():
    assert "AlmgrenChriss" in client.get("/api/strategies").json()["strategies"]


def test_demo_schedule():
    d = client.get("/api/demo/schedule").json()
    assert "TWAP" in d["strategies"]
    assert len(d["intervals"]) == 30


def test_demo_simulate():
    d = client.get("/api/demo/simulate?strategy=VWAP").json()
    assert "tca" in d
    assert "benchmarks" in d


def test_demo_compare():
    d = client.get("/api/demo/compare").json()
    assert len(d["rows"]) == 6


def test_demo_frontier():
    d = client.get("/api/demo/frontier").json()
    assert len(d["points"]) >= 10


def test_demo_montecarlo():
    d = client.get("/api/demo/montecarlo?strategy=TWAP&n_paths=50").json()
    assert d["n_paths"] == 50
    assert "mean" in d


def test_post_simulate():
    r = client.post("/api/simulate", json={"strategy": "AlmgrenChriss"})
    assert r.status_code == 200
    assert "tca" in r.json()


def test_post_invalid_strategy_rejected():
    r = client.post("/api/simulate", json={"strategy": "BOGUS"})
    assert r.status_code == 422
