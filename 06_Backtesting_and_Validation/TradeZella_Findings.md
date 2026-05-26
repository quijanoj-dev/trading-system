# TradeZella Findings

## Key Metrics to Track

| Metric | Why It Matters for V1 |
|--------|----------------------|
| Setup win rate | Is the full 4-signal confluence actually predictive? |
| Expectancy by setup | Net R per trade — must be positive after commissions |
| Time-of-day performance | Within the 10:00–11:00 window: does 10:00–10:30 differ from 10:30–11:00? |
| Day-of-week performance | Is Monday/Friday weaker? Do NFP/FOMC days distort results? |
| Max consecutive losses | Prop firm daily DD risk — how many back-to-back losers is realistic? |
| A+ setup frequency | How often do all 4 signals align? What % of sessions have a qualifying setup? |
| Average hold time | How long does it take to hit stop or target? Impacts overnight risk + fatigue. |
| Adherence to rules | Rule violation rate — are the 4 signal rules actually being followed? |

## Tagging Setup in TradeZella

Tag every trade with:
- `SBV1` — system version
- `stop-hunt` — stop hunt was present
- `smt-confirmed` — SMT confirmed variant fired
- `fvg` or `ifvg` — which imbalance type
- `choch` or `mss` — which structure break type
- `time-gate` — trade was within 10:00–11:00 ET (should always be true for V1)
- `full-confluence` — all 4 signals present
- `partial-confluence` — 2–3 signals only (log but do not take these trades in V1)

## Observations
*(Fill after 10+ trades)*

-

## Lessons
*(Fill as patterns emerge — minimum 30 trades before drawing conclusions)*

-

## TradeZella Dashboard Setup — Filters for V1 Analysis

Run these filters regularly:
1. Tag = `SBV1` + Tag = `full-confluence` → should match all V1 trades
2. Tag = `SBV1` + Tag = `partial-confluence` → setups observed but not taken (should be $0 if rules followed)
3. Time filter: 10:00–11:00 ET → verify no trades outside window
4. Day-of-week breakdown: check if any day has win rate < 30% (candidate for future session filter)
5. R distribution: plot histogram — should cluster around -1R and +2R for V1 (fixed target)

## Minimum Sample for Conclusions

| Conclusion Type | Minimum Trades |
|----------------|---------------|
| Frequency check (setups/week) | 10 sessions |
| Win rate estimate (±15% error) | 30 trades |
| Win rate estimate (±10% error) | 70 trades |
| Day-of-week breakdown | 50 trades |
| System version decision (continue/adjust/abandon) | 30 trades OR 3 months |
