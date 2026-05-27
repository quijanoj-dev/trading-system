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

### Main Parameters
| Parameter | Value |
|-----------|-------|
| Session gate | 10:00–11:00 ET only |
| Stop hunt lookback | 20 bars |
| SMT variant | Confirmed only (NQ divergence — lower low on ES, higher low on NQ for bullish) |
| FVG minimum size | 1.0 point |
| Structure confirmation | CHoCH minimum (close through most recent opposite swing) |
| Setup expiry | 6 bars after stop hunt |
| Stop placement | Low/high of candle immediately after sweep candle |
| Target | 2R (fixed; proxy for liquidity target) |
| Commission | $2.50/contract |
| Slippage | 1 tick |

### Metrics
*(Fill after running Silver_Bullet_V1_Strategy.pine on TradingView Strategy Tester — 1m ES1!, 3–6 months)*

| Metric | Result |
|--------|--------|
| Net profit | $332.71 |
| Profit factor | 4.26 |
| Win rate | 66.7% |
| Average win | $217.35 |
| Average loss | $101.98 |
| Expectancy (R) | $110.90 |
| Max drawdown | 0.40%  ($101.98) |
| Max losing streak | 1 |
| Total trades | 3 |
| Avg trades / week | — |
| Avg hold time (bars) | — |

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

### Notes
- Strategy is an approximation. Stop hunt and CHoCH use simplified pivot-based logic — not identical to SMC-FVG-ICT-DOB-SH indicator output. Results indicate directional validity of the concept, not exact replication of live execution.
- 1-trade Python backtest result (100% win rate, $1,257.50) has no statistical meaning. Expected win rate is unknown; 30+ trades needed.
- Compare result with and without the time gate (Candidate 1 baseline) to quantify the gate's contribution.
- Re-run `python3 -m execution.silver_bullet.run_backtest --save` monthly as new 5m data accumulates.
