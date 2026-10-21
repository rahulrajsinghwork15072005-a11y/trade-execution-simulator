"""Demo orchestration for the trade execution simulator."""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from .core.benchmarks import compute_benchmarks
from .core.impact_models import square_root_impact_bps
from .core.market import MarketContext, make_market
from .core.order import ImpactParams, ParentOrder
from .core.risk import cost_cvar, cost_var
from .core.simulator import simulate
from .core.slippage import all_slippages
from .core.strategies import (
    AdaptivePOV,
    AlmgrenChriss,
    ExecutionStrategy,
    ImplementationShortfall,
    POV,
    TWAP,
    VWAP,
)
from .core.tca import ac_frontier, implementation_shortfall

STRATEGY_NAMES = ["TWAP", "VWAP", "POV", "AlmgrenChriss", "IS", "AdaptivePOV"]


def default_order() -> ParentOrder:
    return ParentOrder("ACME", "buy", 100_000.0, 30, 100.0)


def default_impact() -> ImpactParams:
    return ImpactParams(gamma=1e-6, eta=1e-5, epsilon=0.01)


def make_strategy(
    name: str,
    participation: float = 0.2,
    risk_aversion: float = 2e-6,
    eta: float = 1e-5,
    urgency: float = 2.0,
    aggressiveness: float = 1.0,
) -> ExecutionStrategy:
    if name == "TWAP":
        return TWAP()
    if name == "VWAP":
        return VWAP()
    if name == "POV":
        return POV(participation)
    if name == "AlmgrenChriss":
        return AlmgrenChriss(risk_aversion=risk_aversion, eta=eta)
    if name == "IS":
        return ImplementationShortfall(urgency=urgency)
    if name == "AdaptivePOV":
        return AdaptivePOV(participation, aggressiveness=aggressiveness)
    raise KeyError(f"unknown strategy '{name}'")


@lru_cache(maxsize=1)
def _market() -> MarketContext:
    return make_market(n=30, arrival=100.0, sigma=0.05, seed=1)


def run(
    order: ParentOrder,
    impact: ImpactParams,
    context: MarketContext,
    strategy: ExecutionStrategy,
) -> dict:
    trajectory = strategy.trajectory(order, context)
    result = simulate(order, trajectory, context, impact)
    benchmarks = compute_benchmarks(result.base_prices, result.volume)
    return {
        "strategy": strategy.name,
        "avg_price": result.avg_price,
        "trajectory": np.asarray(trajectory, dtype=float).tolist(),
        "base_prices": result.base_prices,
        "exec_prices": [f.exec_price for f in result.fills],
        "benchmarks": benchmarks,
        "slippage": all_slippages(result.avg_price, benchmarks, result.side),
        "tca": implementation_shortfall(result),
    }


def demo_schedule() -> dict:
    order = default_order()
    ctx = _market()
    return {
        "intervals": list(range(order.n_intervals)),
        "volume": np.asarray(ctx.volume, dtype=float).tolist(),
        "strategies": {
            name: make_strategy(name).trajectory(order, ctx).tolist() for name in STRATEGY_NAMES
        },
    }


def demo_simulate(strategy: str = "VWAP") -> dict:
    return run(default_order(), default_impact(), _market(), make_strategy(strategy))


def demo_compare() -> dict:
    order, impact, ctx = default_order(), default_impact(), _market()
    rows = []
    for name in STRATEGY_NAMES:
        res = run(order, impact, ctx, make_strategy(name))
        rows.append(
            {
                "strategy": name,
                "avg_price": res["avg_price"],
                "is_bps": res["tca"]["implementation_shortfall_bps"],
                "vwap_slippage_bps": res["slippage"]["vwap"],
                "arrival_slippage_bps": res["slippage"]["arrival"],
            }
        )
    return {"rows": rows}


def demo_frontier() -> dict:
    order, impact, ctx = default_order(), default_impact(), _market()
    lambdas = np.logspace(-8, -4, 15)
    return {"points": ac_frontier(order, ctx, impact, lambdas.tolist())}


def demo_montecarlo(strategy: str = "VWAP", n_paths: int = 300) -> dict:
    order, impact = default_order(), default_impact()
    strat = make_strategy(strategy)
    samples = []
    for s in range(n_paths):
        ctx = make_market(n=30, arrival=100.0, sigma=0.05, seed=1000 + s)
        result = simulate(order, strat.trajectory(order, ctx), ctx, impact)
        samples.append(implementation_shortfall(result)["implementation_shortfall_bps"])
    arr = np.asarray(samples, dtype=float)
    return {
        "strategy": strategy,
        "n_paths": n_paths,
        "mean": float(arr.mean()),
        "p5": float(np.percentile(arr, 5)),
        "p95": float(np.percentile(arr, 95)),
        "samples": samples,
    }


def demo_risk(strategy: str = "VWAP", n_paths: int = 400, alpha: float = 0.95) -> dict:
    """Execution-cost risk: VaR / CVaR of the IS distribution + a sqrt-impact reference."""
    order = default_order()
    ctx = _market()
    mc = demo_montecarlo(strategy, n_paths)
    samples = mc["samples"]
    participation = order.total_qty / float(np.sum(ctx.volume))
    sigma_frac = ctx.sigma / order.arrival_price
    return {
        "strategy": strategy,
        "n_paths": n_paths,
        "alpha": alpha,
        "mean_bps": mc["mean"],
        "std_bps": float(np.std(samples)),
        "var_bps": cost_var(samples, alpha),
        "cvar_bps": cost_cvar(samples, alpha),
        "participation": participation,
        "sqrt_impact_model_bps": square_root_impact_bps(participation, sigma_frac, coefficient=10.0),
    }

