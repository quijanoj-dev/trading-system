# Candidate System Scorecard

Scored 2026-05-26. Derived from Current_System_Map.md (sections 1–10) — no external research yet.
Four candidates represent distinct rule variants of the known setup, not new strategies from scratch.

---

## Candidate 1: Strict 4-Signal Confluence

**Description:** Current system made strict. All four signals required: stop hunt + confirmed SMT divergence (confirmed variant only, no zero-lag) + iFVG/FVG entry zone + CHoCH or MSS (CHoCH minimum — no entries on BOS alone). No exceptions to minimum confluence.

### System Type
- Reversal / liquidity sweep

### Market Regime Fit
Trending days with clear directional bias from HTF PO3. Fails in choppy/consolidating sessions (stop hunts without follow-through).

### ES/NQ Fit
- Strong

### 1-Minute Fit
- Strong

### Rule Clarity
- Medium — CHoCH vs MSS ambiguity partially resolved (CHoCH minimum). SMT confirmed variant removes timing debate but still requires reading indicator output.

### Automation Feasibility
- Medium — SMT detection is custom Pine output, CHoCH is indicator label. Both can be read programmatically but require label parsing.

### Backtest Readiness
- Needs proxies — stop hunt detection requires custom Pine logic; CHoCH labeling must be backtestable.

### Complexity
- Medium — 4 conditions, 3 indicators minimum (Premarket Levels + SMT-CDDO + SMC-FVG-ICT-DOB-SH)

### Indicator Load
- Moderate

### Redundancy Risk
- Low — each signal adds independent confirmation. Stop hunt → SMT → FVG → structure each serve distinct roles.

### Evidence Quality
- Medium — conceptually sound (ICT framework), not yet statistically validated on personal execution data.

### Prop Firm Compatibility
- Strong — tight, structure-defined stops (candle after sweep). Defined risk per trade. Infrequent entries.

### Daily Drawdown Risk
- Low — 4-signal requirement significantly reduces trade count. Fewer opportunities = fewer losses on bad days.

### Expected Trade Frequency
- Low (estimated 2–4 setups/week with all 4 signals present)

---

## Candidate 2: Silver Bullet Window Only

**Description:** Same 4-signal confluence as Candidate 1, but with a hard time gate: entries only between 10:00–11:00 ET. No trades outside the Silver Bullet window regardless of setup quality. Addresses the primary weakness (early entries at wrong session times) via structural constraint rather than discipline.

### System Type
- Hybrid (reversal / liquidity sweep + session timing)

### Market Regime Fit
Same as Candidate 1 — trending days. Time gate concentrates exposure in the highest-quality session hour.

### ES/NQ Fit
- Strong

### 1-Minute Fit
- Strong — 10:00–11:00 ET is a 1-minute chart environment (fast moves, clean candles post-open).

### Rule Clarity
- Strong — time gate is binary and objective. Removes all "is this the right time?" decisions.

### Automation Feasibility
- Strong — time filter is trivial to code. Remaining signals same as Candidate 1.

### Backtest Readiness
- Ready now — time constraint makes the sample set well-defined and extractable from historical data.

### Complexity
- Medium — same signals as Candidate 1 plus one additional rule (time gate). Net effect: simplifies decision-making.

### Indicator Load
- Moderate (same as Candidate 1)

### Redundancy Risk
- Low

### Evidence Quality
- Medium — Silver Bullet timing has documented conceptual basis (ICT); personal observation in Current_System_Map §8 confirms cleaner follow-through in this window.

### Prop Firm Compatibility
- Strong — limited window reduces daily drawdown exposure. Structured risk.

### Daily Drawdown Risk
- Low — maximum 1 hour of exposure per day. Natural circuit breaker.

### Expected Trade Frequency
- Low (1–2 setups/week in the Silver Bullet window with full confluence)

---

## Candidate 3: Opening Range Breakout (ORB)

**Description:** Uses the OR module (overnight range 04:00–09:30 ET) as the reference. Trade first confirmed breakout at NY open: price clears OR high/low with displacement candle, then pulls back to OR midpoint or 50% retrace. Enter on first pullback. HTF PO3 must agree with direction. No stop hunt or SMT divergence required.

### System Type
- Breakout / opening drive

### Market Regime Fit
Gap-and-go days, trending opens. Fails on inside days and fake breakouts (common in ES/NQ around FOMC, CPI).

### ES/NQ Fit
- Strong

### 1-Minute Fit
- Medium — ORB setups typically develop on 5m or 15m before the 1m entry. Execution on 1m is fine; analysis timeframe is higher.

### Rule Clarity
- Strong — OR levels are objective (fixed time range, clearly visible). Breakout + pullback is mechanical.

### Automation Feasibility
- Strong — OR high/low/mid are computed values, breakout detection is straightforward.

### Backtest Readiness
- Ready now — OR levels are fully objective, no discretionary labeling required.

### Complexity
- Low — 2 conditions (HTF PO3 direction + OR breakout with pullback). Minimal indicator dependency.

### Indicator Load
- Minimal (OTE-OR-HTF-PO3 module only)

### Redundancy Risk
- Medium — lacks liquidity sweep and divergence context. Higher probability of entering on false breakout.

### Evidence Quality
- Medium — ORB is widely documented and traded. Less aligned with personal confluence framework.

### Prop Firm Compatibility
- Strong — clear setup definition, objective stops (below OR high/low that was broken).

### Daily Drawdown Risk
- Medium — stop is placed at OR boundary, which can be wider than structure-based stop from Candidate 1/2.

### Expected Trade Frequency
- Medium (1 setup per session on qualifying days; higher than Candidate 1/2)

---

## Candidate 4: HTF Bias + ICT AMS Continuation

**Description:** Directional bias from HTF PO3 (daily/weekly market structure). Trade in direction of bias when ICT AMS (Asia-London-NY alignment) confirms. Enter at first 1-minute FVG in the bias direction during NY morning. No stop hunt required. No SMT divergence required. Bias-first, momentum-continuation approach.

### System Type
- Trend continuation

### Market Regime Fit
Strong trending days with clear higher-timeframe delivery. Poor in range days or when HTF PO3 is ambiguous.

### ES/NQ Fit
- Strong

### 1-Minute Fit
- Strong (FVG entry on 1m is mechanical)

### Rule Clarity
- Medium — ICT AMS alignment is interpretive. HTF PO3 direction requires reading the OTE-OR-HTF-PO3 indicator's output, which can be ambiguous at turning points.

### Automation Feasibility
- Medium — FVG detection is coded in existing indicators. AMS alignment is harder to encode objectively.

### Backtest Readiness
- Needs proxies — AMS alignment requires discretionary judgment in current implementation.

### Complexity
- Medium — fewer conditions than Candidate 1/2 but AMS alignment adds interpretive overhead.

### Indicator Load
- Moderate

### Redundancy Risk
- Medium — no liquidity sweep confirmation means higher exposure to trend continuation failures.

### Evidence Quality
- Weak — least tested of the four. HTF PO3 + FVG is conceptually sound but lacks personal execution data and clear statistical support.

### Prop Firm Compatibility
- Medium — entries without stop hunt context can have less well-defined risk anchors.

### Daily Drawdown Risk
- Medium — trend continuation trades can run against you hard if HTF bias is wrong.

### Expected Trade Frequency
- Medium-High (multiple FVGs per session in bias direction — requires additional filtering to avoid overtrading)
