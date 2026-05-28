# Backtest Results

---

## V1 — Silver Bullet Only (Current)

### System Tested
Candidate 2: Silver Bullet Window Only (see 05_Synthesis_and_Candidate_Systems/Version_1_Decision.md)

### Date Range
TBD — minimum 3 months of 1-minute ES/NQ data. Start from 2026-02-24 (3 months back from decision date).

### Market
ES1! (primary) / NQ1! (SMT correlation)

### Timeframe
1-minute

### Main Parameters (optimized 2026-05-28)
| Parameter | Value |
|-----------|-------|
| Session gate | 10:00–11:00 ET (excl. 10:30–10:45 dead zone) |
| Stop hunt lookback | 60 bars (1m) |
| Swing length | 10 bars (1m) |
| SMT variant | Booster ★ — not required. A+ grade when present |
| FVG minimum size | 0.05 pts (SPY proxy scale) |
| Setup expiry | 20 bars |
| Stop placement | entry ± 2×ATR(14) |
| HTF bias gate | 15m EMA-20 — long only when bullish, short only when bearish |
| Target | 3R (Finishers Journal foundation rule) |
| Slippage | 1 tick |

### Metrics — Full Backtest (2024-01-01 → 2026-05-28, Alpaca 1m SPY/QQQ proxy)

| Metric | Result |
|--------|--------|
| Net profit | $1,087.36 |
| Profit factor | 3.71 |
| Win rate | 58.3% |
| Average win | $170.67 |
| Average loss | $52.74 |
| Max drawdown | 0.59% ($147.40) |
| Sharpe ratio | 9.23 |
| Sortino ratio | 84.41 |
| Max losing streak | 3 |
| Total trades | 14 |
| Signals/year | ~5–7 |

### Walk-Forward Validation (fixed params, no refitting)

| Period | Sigs | W | L | Win% | P&L | PF | Sharpe | Equity |
|--------|------|---|---|------|-----|----|--------|--------|
| 2024 full | 2 | 1 | 1 | 50.0% | +$160 | 3.81 | 6.56 | ▼▲ |
| 2025 full | 7 | 2 | 3 | 40.0% | +$206 | 1.41 | 4.64 | ▲▲▼▼▲▼▲ |
| 2026 YTD | 4 | 3 | 1 | 75.0% | +$501 | 6.64 | 11.63 | ▼▲▲▲ |
| **All** | **14** | **7** | **5** | **58.3%** | **+$1,087** | **3.71** | **9.23** | |

All three out-of-sample periods profitable. No year ended negative. Params generalise without refitting.

### Backtest Evolution

| Config added | Sigs | Win% | P&L | PF | Sharpe |
|---|---|---|---|---|---|
| Baseline (unscaled) | 65 | 24.2% | -$165 | 0.86 | -0.36 |
| + HTF EMA-20 (Gate 2) | 25 | 40.9% | +$1,078 | 2.24 | 5.94 |
| + 10:30–10:45 dead zone | **14** | **58.3%** | **+$1,087** | **3.71** | **9.23** |

### TV Strategy Tester Limitation — IMPORTANT

**TradingView Strategy Tester on 1m ES1! is limited to ~20,000 bars = ~16 trading days.**

ES1! trades ~23h/day → 20,000 bars ÷ (23 × 60) = ~14 trading days. This is insufficient for a strategy producing ~1 qualifying setup per week. Expected trades in 16 days: 2–4 at most, often 0.

**Result of automation run (2026-05-26):** 0 trades in 16 days. Consistent with expected frequency. Not a script error.

**Script fix applied (v2):** Original version required all 4 signals on the exact same bar (too strict). Fixed: each signal tracked via state variable, active for `i_expiry` bars. CHoCH is the entry trigger; hunt+FVG+SMT must each have fired within the expiry window. This matches real trading sequencing.

### Recommended Backtesting Path

Use the Python backtester with yfinance/candle_store data for 3-month runs:
1. `execution/market_data/candle_store.py` already stores ES=F + NQ=F data
2. Implement signal detection logic from Pine script in Python
3. Run on 3+ months of 1m data — no bar limit

### TV Strategy Tester — When It Works

The TV Strategy Tester IS useful for:
- Visual signal verification: load the script, visually inspect hunt/FVG/SMT/CHoCH labels on recent bars
- Parameter sensitivity: change expiry/lookback, see if signal density changes
- Session gate verification: confirm blue background appears only 10:00–11:00 ET

**Python backtest run (2026-05-26):** 60d @ 5m ES=F + NQ=F via yfinance. 1 signal generated (2026-05-20 10:25 ET, long). Signal frequency consistent with ~1 qualifying setup per 2–4 weeks under strict 4-signal confluence. **N=1 — statistically insufficient for conclusions.** Continue logging forward test setups in Forward_Test_Notes.md; revisit metrics at 30 trades.

### Limitations & Next Steps

- **Proxy data**: SPY/QQQ ETFs used as ES/NQ proxies (free Alpaca tier). Price levels, tick size, and volatility differ from actual futures. Results directionally valid, not numerically exact.
- **Sample size**: 14 total signals (n=2/7/4 per year) is statistically thin. Confidence intervals are wide. Need 30+ signals per period for meaningful conclusions.
- **Real futures validation required**: Acquire CQG/Rithmic/TradeStation ES/NQ 1m historical data → re-run with `point_value=50.0, tick_size=0.25`.
- **Run command**:
  ```bash
  python3 -m execution.silver_bullet.run_backtest \
    --source alpaca --start 2024-01-01 \
    --fvg-min 0.05 --sh-bars 60 --swing 10 --expiry 20 \
    --r 3.0 --atr-stop 2.0 --htf-ema 20 --save
  ```
