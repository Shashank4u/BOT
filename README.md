# AI Trading Assistant

A production-quality **single-user** AI Trading Assistant that connects to MetaTrader 5 (XM broker), executes **your** strategies, manages risk, records every trade, and uses AI to explain and improve performance over time.

> **No login required** — built for personal use. Optional API key for VPS deployments.
>
> **Important:** This application does **not** predict markets or guarantee profits. It defaults to **DEMO mode**.

**Progress tracker:** [docs/PROGRESS.md](docs/PROGRESS.md) — what's done and what's remaining.

---

## Quick Start

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
mkdir -p data logs
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

```bash
cd backend && pytest
```

---

## Current Capabilities (Steps 1–10)

- Full REST API backend (market, strategies, risk, orders, AI, backtest, scanner, news, analytics)
- React Native mobile app (`frontend/`) — see [frontend/README.md](frontend/README.md)
- MT5 market data (mock + real), 15 indicators, 23 patterns, 8 strategies
- Risk management, order execution, trade journal, AI assistant
- Backtesting, market scanner, economic calendar, Telegram notifications

See [docs/PROGRESS.md](docs/PROGRESS.md) for the full roadmap.

---

## Safety Rules

1. **DEMO mode by default**
2. **No market predictions**
3. **You control all strategies**
4. **Live trading requires** `POST /api/v1/risk/confirm-live`
5. **Every order is logged** to the database
