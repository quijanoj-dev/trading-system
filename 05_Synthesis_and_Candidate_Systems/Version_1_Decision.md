# Version 1 Decision

Decided 2026-05-26. Based on Candidate_System_Scorecard.md (4 candidates scored).

## Decision Criteria
- Fit for ES/NQ
- Fit for 1-minute execution
- Rule clarity (can be stated precisely without interpretation)
- Backtest readiness (sample set extractable from historical data now)
- Automation feasibility
- Realism under prop-firm constraints
- Robustness
- Simplicity

## Chosen System

**Candidate 2: Silver Bullet Window Only**

Entry only between 10:00–11:00 ET. Required confluence: stop hunt + confirmed SMT divergence (confirmed variant) + iFVG/FVG entry zone + CHoCH or MSS (CHoCH minimum). All four signals required. Stop = low/high of candle immediately after the sweep candle. Target = nearest visible liquidity pool, fallback = fixed R.

## Why It Won

1. **Directly addresses the primary leak.** Current_System_Map §9 identifies early entries as the primary weakness — entering on 2 signals before CHoCH confirmation. Candidate 2 fixes this two ways: strict 4-signal requirement AND a time gate that structurally prevents entries outside the highest-quality session window.

2. **Highest rule clarity of all 4 candidates.** The time gate is binary — you're either in the 10:00–11:00 window or you're not. No judgment call. The confirmed-SMT-only constraint removes the multi-variant ambiguity documented in §10.

3. **Best backtest readiness.** Time constraint makes the sample set well-defined. Can filter historical data to 10:00–11:00 ET and count qualifying setups. No proxies needed for the time gate.

4. **Personal evidence supports the window.** §8 explicitly states: "Silver Bullet timing — setups during 10:00–11:00 ET have cleaner follow-through vs. random intraday entries." Concentrating all trading in this window maximizes time spent in highest-edge conditions.

5. **Prop firm safe.** Low trade frequency + tight structure-defined stops + maximum 1 hour of daily exposure = low daily drawdown profile.

6. **Simplest daily workflow.** Only need to be active 10:00–11:00 ET. Rest of the session is observation only.

## What Was Rejected and Why

**Candidate 1 (Strict 4-Signal, no time gate):** Strong system but lacks the time constraint. Without a time gate, the early-entry leak can still occur outside the Silver Bullet window where follow-through is weaker. Candidate 2 is strictly better — same signals, additional guard rail. Test Candidate 1 as Version 1B if time gate proves too restrictive.

**Candidate 3 (OR Breakout):** Different system type — breakout rather than reversal/sweep. Medium 1-minute fit. Higher daily drawdown risk from wider OR-based stops. Worth testing independently in a future version but competes with rather than complements Candidate 2.

**Candidate 4 (HTF Bias + AMS Continuation):** Weakest evidence quality. AMS alignment is interpretive, making backtesting and consistent execution harder. No liquidity sweep context increases false entry risk. Not yet ready to test — needs more external research (folder 03) before it can be properly defined.

## Immediate Next Test

Backtest Candidate 2 on historical ES/NQ 1-minute data:
- Time window: 10:00–11:00 ET only
- Signal requirements: stop hunt + confirmed SMT + iFVG/FVG + CHoCH/MSS
- Stop: candle after sweep (not wick)
- Target: first visible liquidity pool
- Sample: minimum 3 months of data, log every qualifying setup regardless of whether it was taken
- Metrics: win rate, R-multiple distribution, max consecutive losses, average trade duration

## Risks to Monitor

1. **Low sample size.** Candidate 2 generates 1–2 setups per week. 3 months = ~12–25 setups. May not be statistically significant — extend to 6 months if needed.

2. **Missed setups outside the window.** The 10:00–11:00 time gate will exclude valid setups that appear at 09:45 or 11:15. This is intentional — the constraint is the point. Monitor whether excluded setups would have been profitable to assess whether extending the window is warranted after V1 validation.

3. **SMT confirmed variant lag.** Confirmed SMT signals after structure confirmation may produce late entries with poor R/R. Track entry price vs stop/target ratio to detect if lag is compressing R.

4. **CHoCH minimum may still be ambiguous.** Current indicators label BOS, CHoCH, MSS, and CISD. The rule is CHoCH minimum. Define this precisely for backtesting: CHoCH = a swing high/low that breaks the most recent opposing swing, confirmed by a closed 1-minute candle above/below it. Do not count BOS (same direction) or candles that merely wick through.
