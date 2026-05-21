# Trading System

ES/NQ intraday scalping system — automated pipeline from market data to signal to execution. Built for prop firm funding challenges (Apex Trader Funding) and extending into prediction markets.

## Architecture

```
Signal → Risk → Execution
```

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
  polymarket/
    connector.py             # Polymarket CLOB API wrapper (dry-run by default)
    strategy.py              # ResolutionAmbiguity + LiquidityMispricing strategies
    bot.py                   # Autonomous market scanner + executor
  market_data/
    interfaces.py            # MarketDataFeed ABC + typed dataclasses
    unusual_whales.py        # UnusualWhales client (options flow, dark pool, congressional)
  tests/
    test_backtester.py       # 25 backtester tests
    test_risk_manager.py     # 19 risk manager tests
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
# 44 tests, Python 3.14+, ~100s
```

## TradingView Indicators

Pine Script v6. Load each file in TradingView Pine Editor and add to chart.

- **MMT_Companion** — Asia/London/NY session ranges, fair value gaps, order blocks, liquidity pool markers
- **CVD_Divergence** — Cumulative Volume Delta vs price divergence detection, alerts on 2+ bar divergence
- **OI_Analysis** — OI regime: accumulation / distribution / short-covering / long-liquidation with on-chart labels

## Backtester

```python
from execution.backtester import Backtester, BacktestConfig
from execution.risk_manager import RiskConfig

config = BacktestConfig(risk_config=RiskConfig(risk_pct=0.01))
bt = Backtester(config)
result = bt.run(ohlcv_df, signals)
print(bt.summary(result))
```

## Polymarket Bot (dry-run)

```bash
python -m execution.polymarket.bot
# --live flag enables real execution (requires API keys)
```

## Environment Variables

```bash
POLYMARKET_API_KEY=...         # Polymarket CLOB trading
POLYMARKET_SECRET=...
UNUSUAL_WHALES_API_KEY=...     # Options flow + dark pool (paid subscription required)
```

## Knowledge Base

- `Framework_Working_Principles.md` — decision guardrails, system rules
- `Framework_Master_Index.md` — index of all framework documents
- `01_Trading_Profile_and_Objectives/` — trader profile, objectives, edge definition
- `04_Current_System_and_Indicators/` — active indicator inventory

## Built with Claude Code

Designed and built end-to-end using [Claude Code](https://claude.ai/code).
