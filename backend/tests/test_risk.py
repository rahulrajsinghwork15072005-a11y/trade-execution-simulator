import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.core.impact_models import square_root_impact_bps
from app.core.risk import cost_cvar, cost_var
from app.main import app

client = TestClient(app)


def test_var_is_quantile():
    assert cost_var(list(range(101)), 0.95) == pytest.approx(95.0, abs=1.0)


def test_cvar_at_least_var():
    rng = np.random.default_rng(0)
    samples = rng.normal(10, 5, 5000)
    assert cost_cvar(samples, 0.95) >= cost_var(samples, 0.95)


def test_empty_samples():
    assert cost_var([]) == 0.0
    assert cost_cvar([]) == 0.0


def test_sqrt_impact_scaling():
    i1 = square_root_impact_bps(0.01, 0.02, 1.0)
    i4 = square_root_impact_bps(0.04, 0.02, 1.0)
    assert i4 == pytest.approx(2.0 * i1)  # sqrt(4) = 2


def test_sqrt_impact_negative_raises():
    with pytest.raises(ValueError):
        square_root_impact_bps(-0.1, 0.02)


def test_risk_endpoint():
    body = client.get("/api/demo/risk", params={"strategy": "TWAP", "n_paths": 100}).json()
    assert "var_bps" in body
    assert "cvar_bps" in body
    assert body["cvar_bps"] >= body["var_bps"]
    assert "sqrt_impact_model_bps" in body
