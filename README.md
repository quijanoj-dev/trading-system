# Trading System

ICT-SMC PO3-AMD intraday futures trading system — ES/NQ on 1m execution, Silver Bullet V1.
A+ setups only. 6-gate decision framework. Built for Apex Trader Funding evaluation and scaling.

**Primary decision doc:** `04_Current_System_and_Indicators/Current_System_Map.md`

## System Summary

| Attribute | Value |
|-----------|-------|
| Markets | ES, NQ (1m execution) |
| Session | London or New York only |
| Framework | ICT-SMC PO3-AMD — 6-gate A+ checklist |
| Entry window | New York Silver Bullet: 10:00–11:00 ET |
| Signals required | All 4: stop hunt + confirmed SMT + iFVG/FVG + CHoCH/MSS |
| Risk:Reward | ≥ 1:3 (no exceptions) |
| Max account risk | ≤ 10% total exposure |
| Stop | Low/high of candle immediately after sweep candle |

## Platform Stack

| Layer | Tool |
|-------|------|
| Charting + signals | TradingView (Pine Script v6) |
| Execution | NinjaTrader |
| Journaling + validation | TradeZella |
| Prop firm | Apex Trader Funding |
| Market data | OpenBB, UnusualWhales |
| Prediction markets | Polymarket CLOB |

## Repository Structure

```
08_TradingView_Indicators/
  mmt/
    MMT_Companion.pine       # Session ranges, FVGs, order blocks, liquidity pools
    CVD_Divergence.pine      # Cumulative Volume Delta divergence + alerts
    OI_Analysis.pine         # Open Interest regime classification
execution/
  backtester.py              # OHLCV backtesting engine (slippage, commission, metrics)
  risk_manager.py            # Position sizing + circuit breakers (daily loss, max drawdown)
  silver_bullet/             # Silver Bullet V1 signal + backtest pipeline
  ml_signals/                # LSTM signal (walk-forward, requires 500+ bars)
  market_data/               # Alpaca + Pyth feed, CandleStore
  broker_automation/         # Alpaca live execution (symbol-validated, env-only keys)
  agents/                    # Research orchestrator + 5 researchers (TradingAgents wired)
  polymarket/
    connector.py             # Polymarket CLOB API wrapper (dry-run by default)
    strategy.py              # ResolutionAmbiguity + LiquidityMispricing strategies
    bot.py                   # Autonomous market scanner + executor
  tests/
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install openbb py-clob-client
```

## Testing

```bash
pytest execution/tests/
```

## TradingView Indicators

Pine Script v6. Five active indicators, each mapped to a decision gate.

| Indicator | Gate(s) | Purpose |
|-----------|---------|---------|
| Market Session Lines | 1 | Session time markers |
| Premarket Levels | 2, 5 | Multi-TF OHLC reference + TP targets |
| OTE-OR-HTF-PO3 | 2, 3, 4 | OTE Fibonacci + Opening Range + HTF PO3 |
| SMC-FVG-ICT-DOB-SH | 3, 4 | BOS/CHoCH + FVG + OB + Stop Hunt |
| SMT-CD Divergence | 3, 4 | Confirmed SMT inter-market divergence |

## Silver Bullet V1 Backtest

```bash
cd "Trading System"
python -m execution.silver_bullet.run_backtest --source alpaca --start 2024-01-01 --atr-stop 2.0 --save
```
Results auto-saved to `06_Backtesting_and_Validation/Backtest_Results.md`.

## Environment Variables

```bash
ALPACA_API_KEY=...            # Alpaca market data + live execution
ALPACA_SECRET_KEY=...
POLYMARKET_API_KEY=...        # Polymarket CLOB trading
POLYMARKET_SECRET=...
UNUSUAL_WHALES_API_KEY=...    # Options flow + dark pool (paid subscription required)
```

## Knowledge Base

- `Framework_Master_Index.md` — index of all framework docs, gate-to-doc mapping
- `Framework_Working_Principles.md` — decision guardrails, system rules
- `04_Current_System_and_Indicators/Current_System_Map.md` — **6-gate A+ decision framework**
- `Daily_Ritual.md` — pre/post session routines
- `13_Week_Roadmap.md` — migration → backtest → Apex evaluation timeline

## Built with Claude Code

Designed and built end-to-end using [Claude Code](https://claude.ai/code).
