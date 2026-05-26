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
| Net profit | — |
| Profit factor | — |
| Win rate | — |
| Average win | — |
| Average loss | — |
| Expectancy (R) | — |
| Max drawdown | — |
| Max losing streak | — |
| Total trades | — |
| Avg trades / week | — |
| Avg hold time (bars) | — |

### Notes
- Strategy is an approximation. Stop hunt and CHoCH use simplified pivot-based logic — not identical to SMC-FVG-ICT-DOB-SH indicator output. Results indicate directional validity of the concept, not exact replication of live execution.
- If total trades < 20, extend date range to 6 months before drawing conclusions.
- Compare result with and without the time gate (Candidate 1 baseline) to quantify the gate's contribution.
