"""Micro-benchmarks for the execution-cost engine.

Times the simulator across all strategies and the Almgren-Chriss frontier, and
contrasts realised cost under linear vs square-root temporary impact. Runs
entirely offline on the pure ``app.core`` engine.

    python scripts/bench.py            # from backend/
    python scripts/bench.py --repeats 7

Numbers are wall-clock and machine-dependent; treat them as relative signals.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Make ``app`` importable when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.market import make_market  # noqa: E402
from app.core.order import ImpactParams, ParentOrder  # noqa: E402
from app.core.simulator import simulate  # noqa: E402
from app.core.tca import ac_frontier, implementation_shortfall  # noqa: E402
from app.demo import STRATEGY_NAMES, make_strategy  # noqa: E402


def _best(fn, repeats: int) -> float:
    best = float("inf")
    for _ in range(max(1, repeats)):
        start = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - start)
    return best


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark the execution engine.")
    parser.add_argument("--intervals", type=int, default=500)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args(argv)

    n = args.intervals
    order = ParentOrder("ACME", "buy", 1_000_000.0, n, 100.0)
    ctx = make_market(n=n, arrival=100.0, sigma=0.05, seed=1)
    impact = ImpactParams()  # psi = 1.0 (linear)

    print(f"\nExecution simulator benchmarks  (intervals={n})")
    print("-" * 58)
    print(f"  {'strategy':16} {'ms / sim':>10} {'sims / sec':>14}")
    for name in STRATEGY_NAMES:
        strat = make_strategy(name)

        def run(strategy=strat) -> None:
            traj = strategy.trajectory(order, ctx)
            res = simulate(order, traj, ctx, impact)
            implementation_shortfall(res)

        secs = _best(run, args.repeats)
        print(f"  {name:16} {secs * 1e3:>10.3f} {1.0 / secs:>14,.0f}")

    lams = [10.0**k for k in range(-8, 2)] * 3
    fr = _best(lambda: ac_frontier(order, ctx, impact, lams), max(1, args.repeats // 2))
    print(f"\n  AC frontier ({len(lams)} pts) {fr * 1e3:>10.3f} ms")

    # Linear vs square-root impact: realised implementation shortfall.
    traj = make_strategy("VWAP").trajectory(order, ctx)
    is_lin = implementation_shortfall(simulate(order, traj, ctx, ImpactParams(psi=1.0)))
    is_sqrt = implementation_shortfall(simulate(order, traj, ctx, ImpactParams(psi=0.5)))
    print("\n  Realised IS (VWAP), temporary-impact regime:")
    print(f"    linear (psi=1.0):       {is_lin['implementation_shortfall_bps']:8.2f} bps")
    print(f"    square-root (psi=0.5):  {is_sqrt['implementation_shortfall_bps']:8.2f} bps")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
