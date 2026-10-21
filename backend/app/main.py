"""FastAPI application: execution simulator REST API + dashboard."""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from . import demo as demo_service
from . import live as live_service
from .config import settings
from .core.market import make_market
from .core.order import ImpactParams, ParentOrder
from .observability import (
    ObservabilityMiddleware,
    RateLimiter,
    RateLimitMiddleware,
    metrics,
    uptime_seconds,
)
from .schemas import SimulateRequest

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

_STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="Trade Execution Simulator",
    version=settings.version,
    description="Simulate TWAP/VWAP/POV/Almgren-Chriss execution with impact, slippage, and TCA.",
)

app.add_middleware(GZipMiddleware, minimum_size=512)
if settings.rate_limit_per_sec > 0:
    app.add_middleware(RateLimitMiddleware, limiter=RateLimiter(settings.rate_limit_per_sec))
app.add_middleware(ObservabilityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"error": "internal_error", "detail": str(exc)})


if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    index = _STATIC_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="dashboard not found")
    return FileResponse(str(index))


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/version")
def version() -> dict:
    return {
        "name": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
    }


@app.get("/api/ready")
def ready() -> dict:
    return {"ready": True, "uptime_seconds": round(uptime_seconds(), 1)}


@app.get("/metrics", include_in_schema=False)
def prometheus_metrics() -> PlainTextResponse:
    return PlainTextResponse(metrics.render(), media_type="text/plain; version=0.0.4")


@app.get("/api/strategies")
def strategies() -> dict:
    return {"strategies": demo_service.STRATEGY_NAMES}


@app.post("/api/simulate")
def simulate(req: SimulateRequest) -> dict:
    try:
        order = ParentOrder(
            symbol=req.order.symbol,
            side=req.order.side,
            total_qty=req.order.total_qty,
            n_intervals=req.order.n_intervals,
            arrival_price=req.order.arrival_price,
        )
        impact = ImpactParams(
            gamma=req.impact.gamma,
            eta=req.impact.eta,
            epsilon=req.impact.epsilon,
            psi=req.impact.psi,
        )
        context = make_market(
            n=req.order.n_intervals,
            arrival=req.order.arrival_price,
            sigma=req.market.sigma,
            drift=req.market.drift,
            seed=req.market.seed,
            total_volume=req.market.total_volume,
        )
        strategy = demo_service.make_strategy(
            req.strategy, participation=req.participation,
            risk_aversion=req.risk_aversion, eta=req.impact.eta,
        )
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return demo_service.run(order, impact, context, strategy)


@app.get("/api/demo/schedule")
def demo_schedule() -> dict:
    return demo_service.demo_schedule()


@app.get("/api/demo/simulate")
def demo_simulate(strategy: str = "VWAP") -> dict:
    try:
        return demo_service.demo_simulate(strategy)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/demo/compare")
def demo_compare() -> dict:
    return demo_service.demo_compare()


@app.get("/api/demo/frontier")
def demo_frontier() -> dict:
    return demo_service.demo_frontier()


@app.get("/api/demo/montecarlo")
def demo_montecarlo(strategy: str = "VWAP", n_paths: int = 300) -> dict:
    try:
        return demo_service.demo_montecarlo(strategy, n_paths=min(max(n_paths, 10), 2000))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/demo/risk")
def demo_risk(strategy: str = "VWAP", n_paths: int = 400) -> dict:
    try:
        return demo_service.demo_risk(strategy, n_paths=min(max(n_paths, 10), 2000))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/live/simulate")
def live_simulate(
    ticker: str = "AAPL",
    strategy: str = "VWAP",
    qty: float = 100_000.0,
    side: str = "buy",
    allow_network: bool = True,
) -> dict:
    try:
        return live_service.live_simulate(
            ticker, strategy=strategy, qty=qty, side=side, allow_network=allow_network
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
