# Trade Execution Simulator

Simulates how a large parent order is worked into the market over time using
**TWAP**, **VWAP**, **POV**, and **Almgren–Chriss** optimal execution. It applies
a temporary/permanent **market-impact** model to each fill, measures **slippage**
and **implementation shortfall**, and produces a full **TCA** with benchmark
comparison and a cost-vs-risk **efficient frontier**.

See [PLAN.md](PLAN.md) for the full design and math, and
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the system architecture (the pure
cost engine, the impact model, the execution algorithms, and the API layers).

## What's implemented

| Layer | Status |
|-------|--------|
| Core (`app/core`) | parent order, impact params (linear **and square-root** temporary impact via `psi`), market context + U-shaped volume, strategies (TWAP/VWAP/POV/AC/IS/AdaptivePOV), simulator, benchmarks, slippage, TCA + frontier |
| API (`app/main.py`) | FastAPI REST + OpenAPI docs |
| Dashboard (`app/static`) | Plotly dashboard (schedule, fills, IS waterfall, frontier, Monte-Carlo, compare) |
| Tests (`tests/`) | 53 unit + API tests (strategy identities, exact IS reconciliation for linear & square-root impact, frontier monotonicity) |

## Run it

```powershell
# from trade-execution-simulator/backend/
& ..\.venv\Scripts\python.exe -m pip install -r requirements.txt
& ..\.venv\Scripts\python.exe -m pytest -q
& ..\.venv\Scripts\python.exe scripts\bench.py        # engine throughput + linear vs sqrt impact
& ..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8004
```

- Dashboard: http://127.0.0.1:8004/
- Swagger docs: http://127.0.0.1:8004/docs

## Key endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/strategies` | available strategies |
| POST | `/api/simulate` | run a custom order + strategy + market |
| GET | `/api/demo/schedule` | trajectories of all strategies + volume curve |
| GET | `/api/demo/simulate` | fills + benchmarks + TCA for one strategy |
| GET | `/api/demo/compare` | ranked TCA table across strategies |
| GET | `/api/demo/frontier` | Almgren–Chriss cost-vs-risk frontier |
| GET | `/api/demo/montecarlo` | cost distribution over random price paths |

## Live data (optional)

Run a strategy over real intraday bars (yfinance) with an offline fallback:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/live/simulate?ticker=AAPL&strategy=VWAP` | execute on real bars (or synthetic) |

## React frontend (Vite)

```powershell
cd frontend
npm install
npm run dev        # http://localhost:5184 (dev proxy /api -> :8004)
npm run build      # production build to dist/
```

## Docker

```powershell
docker compose up --build
# frontend: http://localhost:8084  |  API: http://localhost:8004
```

## Production & operations

- Observability: `GET /api/version`, `GET /api/ready`, `GET /metrics` (Prometheus text format).
- Middleware: CORS, GZip, request-id + security headers, structured request logs, optional rate limiting.
- Env config: `CORS_ORIGINS`, `LOG_LEVEL`, `RATE_LIMIT_PER_SEC`.

## Execution-cost risk

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/demo/risk` | IS-distribution **VaR / CVaR** + square-root-impact reference |

## Known limitations & roadmap

**Limitations**
- Market-impact is a stylised permanent/temporary model (linear or empirical
  **square-root law** via `psi`); there is no explicit queue-position or
  maker/taker-fee model.
- Intraday data is optional (yfinance) with a synthetic fallback.

**Roadmap**
- Queue-position / adverse-selection fill model.
- A bundled intraday sample and HTML/CSV/JSON TCA report export.
  (Implementation-Shortfall and adaptive-POV strategies are implemented — 6 algos
  now: TWAP, VWAP, POV, Almgren–Chriss, IS, AdaptivePOV.)
