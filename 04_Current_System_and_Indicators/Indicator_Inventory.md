# Indicator Inventory

8 active indicators in `08_TradingView_Indicators/`. Last updated: 2026-03-19.

---

## 1. Market Session Lines

### Category
session

### Purpose
Draws vertical time-separator lines at key session boundaries (Market Open 09:30, Noon Relax 12:00, Power Hour 15:00, Market Close 16:00) for immediate visual context about which session phase current price action belongs to.

### What It Measures
Clock time relative to US equity session. Purely temporal orientation — no price or volume measurement.

### Inputs / Key Settings
- Timezone (default: America/New_York)
- Keep last N days (default 5)
- Enable/disable each of 4 session markers individually
- Color, style (Solid/Dashed/Dotted), width per marker
- Future projection days (D+1 through D+N, default 1)

### Signals Produced
- Vertical lines at each session time
- Labels ("MARKET OPEN", "NOON RELAX", "POWER HOUR", "MARKET CLOSE")
- Future-projected lines for next N trading days (skips weekends)

### Timing Nature
Coincident — lines appear exactly at session time. Future projections are forward-looking reference markers.

### Confirmation Requirement
None. Time-based only.

### Repaint Risk
None. No `request.security()` calls, no lookahead. Historical lines via `barstate.isconfirmed`.

### Delay Risk
Zero bars. Lines placed at exact timestamps.

### Strengths
- Zero computational overhead
- Clear session awareness at a glance
- Future projection anticipates upcoming session boundaries
- Fully customizable times, colors, styles

### Weaknesses
- No directional information
- Only meaningful on intraday timeframes (hidden on daily+)
- Does not account for half-days or market holidays

### Overlap With Other Indicators
Partial overlap with Premarket Levels (both mark session boundaries). No overlap with signal-generating indicators.

### Unique Value
Only indicator projecting future session time boundaries forward in time.

### Can It Be Used in a Strategy Script?
No — purely visual overlay, no buy/sell logic.

### Can It Be Automated?
No — no actionable signals.

### Role in My Current System
Supporting

### Keep / Review / Remove
**Keep** — Essential orientation tool with negligible resource cost. Prevents trading during dead zones (noon).

---

## 2. Premarket Levels

### Category
Session, liquidity

### Purpose
Tracks and displays key OHLC reference levels from multiple timeframes: Premarket (04:00-09:30), Current Day RTH (09:30-16:00), Previous Day, Previous Week, and Previous Month. Levels act as support/resistance and liquidity targets.

### What It Measures
- Premarket Open/High/Low (04:00-09:30 ET)
- Current Day Open/High/Low (09:30-16:00 ET)
- Previous Day Open/High/Low/Close
- Previous Week Open/High/Low/Close
- Previous Month Open/High/Low/Close

### Inputs / Key Settings
- Future extension bars (default 10)
- Plot Active Lines On Prev Days (default 15)
- Global line opacity, style, width
- Show/hide toggle and color for each of 18 individual level lines
- Label balloons (Left/Right/Off)

### Signals Produced
- Horizontal price level lines for each enabled level
- Color-coded labels (PMO, PMH, PML, CDO, CDH, CDL, PDO, PDH, PDL, PDC, PWO, PWH, PWL, PWC, PMoO, PMoH, PMoL, PMoC)
- Lines extend rightward with future projection

### Timing Nature
Coincident/Leading — Premarket and current-day levels update in real time during their sessions, then freeze as reference for the rest of the day.

### Confirmation Requirement
None. Levels are objective OHLC values.

### Repaint Risk
Low. Uses `request.security()` with `barmerge.lookahead_off`. Prior period values use `[1]` offset for non-repainting previous-period data. Intraday PM/CD levels tracked bar-by-bar with no lookahead.

### Delay Risk
Zero for intraday PM/CD levels. PD/PW/PM levels update at period boundaries.

### Strengths
- Comprehensive multi-timeframe level set covering 5 distinct periods
- Non-repainting reference levels from confirmed prior periods
- PM levels extend throughout the day as key reference
- Highly configurable per-level show/hide and colors

### Weaknesses
- Chart can become visually cluttered with all 18 levels enabled
- No dynamic update of PD/PW/PM mid-period (by design)
- Only useful on intraday timeframes

### Overlap With Other Indicators
Opening Range module in OTE-OR-HTF-PO3 covers session-based high/low ranges. Partial overlap.

### Unique Value
Only indicator providing Premarket OHL levels that persist throughout the regular session. Also the only source for Previous Week and Previous Month OHLC.

### Can It Be Used in a Strategy Script?
Partially — levels can serve as entry/exit targets, but no signal logic built in.

### Can It Be Automated?
Partially — levels can be exported as price thresholds, but no built-in alerts.

### Role in My Current System
Core

### Keep / Review / Remove
**Keep** — Core reference level framework. Premarket and prior-period levels are fundamental to ICT/SMC methodology for identifying liquidity pools and reaction zones.

---

## 3. OTE-OR-HTF-PO3

### Category
Execution, structure, session

### Purpose
Three-module indicator: (1) Optimal Trade Entry (OTE) Fibonacci levels from a higher timeframe, (2) Opening Range time-based session levels (Asia, London, 15m OR, Silver Bullet), and (3) HTF Power of Three (PO3) candle visualization projected to chart right side. Provides confluence zones for trade entries.

### What It Measures
- **OTE:** Fibonacci retracement/extension grid (0, 0.5, 0.705, integers +/-1 through +/-6) from configurable HTF candle (default 60m). Includes 0.618-0.786 cloud zones.
- **OR:** Session high/low ranges for Asia (18:00-00:00), London (00:00-06:00), 15m Opening Range (09:30-09:45), Silver Bullet (04:00-09:30).
- **PO3:** Last 6 candles from 4 configurable HTFs (default 5m, 15m, 1h, 4h) as mini-candle groups projected right, with volume bars, volume MA, FVG detection.

### Inputs / Key Settings
- OTE: HTF period (default 60m), periods back, near-distance mode, line/cloud styles
- OR: Session start/end times for Asia/London/OR15/SF, history count, styles
- PO3: 4 HTF inputs, candle opacity, gap between groups, FVG toggle, volume bar height, volume MA type/length
- Shared: Future Extension bars (default 10)

### Signals Produced
- OTE: Horizontal fib-level lines, 0.618-0.786 cloud boxes, hit-detection highlighting
- OR: Session high/low horizontal lines with labels ("Asia High", "London Low", etc.)
- PO3: Mini-candle boxes, FVG boxes, volume bar boxes, volume MA lines, group labels

### Timing Nature
Mixed. OTE levels reset on HTF rollover (coincident). OR levels form during sessions then freeze (coincident). PO3 shows completed candles (lagging by definition).

### Confirmation Requirement
OTE requires HTF candle close for frozen levels. OR requires session end for final values. PO3 uses `barmerge.lookahead_off` so current HTF candle is live.

### Repaint Risk
Low. All `request.security()` calls use `barmerge.lookahead_off`. OTE freezes previous HTF candle values on rollover.

### Delay Risk
OTE levels appear immediately on HTF rollover. OR levels draw after session close. PO3 is visual-only.

### Strengths
- Three independently useful modules in one indicator (saves indicator slots)
- OTE provides precise Fibonacci confluence zones
- OR covers all major ICT session ranges
- PO3 gives HTF candlestick context without changing chart timeframe
- Hit-detection tracks which OTE levels price has touched

### Weaknesses
- Very complex script — heavy resource usage with all 3 modules active
- PO3 projection takes significant right-side chart space
- No alerting or signal generation — purely visual
- OTE levels can be numerous (36 fib levels + 12 cloud zones)

### Overlap With Other Indicators
OR module overlaps with Premarket Levels (session-based levels).

### Unique Value
Only indicator providing ICT Optimal Trade Entry fib grid from HTF data. Only indicator showing HTF PO3 candlestick visualization with FVG detection and volume profiling.

### Can It Be Used in a Strategy Script?
Partially — OTE levels and OR ranges could define entry zones, but significant refactoring needed.

### Can It Be Automated?
Partially — OTE hit-detection and OR session breaks could trigger alerts; PO3 is visual-only.

### Role in My Current System
Core

### Keep / Review / Remove
**Keep** — Provides execution-level detail (OTE zones, session ranges, HTF context) that no other indicator covers. Consider splitting into 3 separate lighter indicators if performance becomes an issue.

---

## 4. SMC-FVG-ICT-DOB-SH

### Category
Structure, liquidity

### Purpose
Comprehensive Smart Money Concepts (SMC) structural analysis: Break of Structure (BOS) and Change of Character (CHoCH) at multiple tiers, Fair Value Gaps (FVG) with tiered thresholds and mitigation tracking, Order Blocks (traditional + displacement-based), Equal Highs/Lows, and Stop Hunts (liquidity sweeps of fractal levels).

### What It Measures
- **Market Structure:** Internal and Swing BOS/CHoCH using pivot leg detection
- **Real-Time Structure:** Internal and Swing without right-side confirmation delay
- **ICT Anchored Market Structures:** Short-term, Intermediate-term, Long-term BOS/CHoCH
- **FVGs:** Three-tier size thresholds (T1/T2/T3) with mitigation tracking
- **Order Blocks:** Internal and Swing OBs (traditional) + Displacement OBs (ATR-filtered)
- **Equal Highs/Lows:** ATR-tolerance detection of double tops/bottoms
- **Stop Hunts:** Fractal level sweeps with optional FVG-zone filtering

### Inputs / Key Settings
- Mode: Historical vs Present
- Internal/Swing OB size (default 5), OB filter (ATR/Range), mitigation (Close/High-Low)
- FVG thresholds T1/T2/T3 (0.01%/0.025%/0.05%), min tick gap, mitigated times, auto-close
- Stop Hunt: max bars back (200), recent FVG hunt filter
- ICT AMS: separate settings for ST, IT, LT structures
- Real-Time structure: separate settings for Internal and Swing

### Signals Produced
- BOS/CHoCH horizontal lines with labels (color-coded bull/bear)
- FVG cloud boxes (color-coded by tier, grey when mitigated)
- Order Block boxes with optional projection lines
- Equal High/Low labels and connector lines
- Stop Hunt labels and raid lines/dots at swept fractal levels
- ICT AMS structure labels at ST/IT/LT pivot breaks

### Timing Nature
Mixed. Traditional structure uses pivot detection with right-side confirmation (lagging by pivot size bars). Real-Time structure uses close-break detection (coincident). Stop Hunts fire on the bar that sweeps the level (coincident).

### Confirmation Requirement
Traditional BOS/CHoCH require pivot confirmation (right-side bars). Real-Time requires close beyond level. FVGs form on bar[2] (3-bar pattern). OBs require subsequent move to qualify.

### Repaint Risk
Low-Medium. No `request.security()` with lookahead. Traditional pivot-based structures are non-repainting (delayed but stable). Real-Time structures fire on bar close. FVGs use historical bar references.

### Delay Risk
Traditional structure: delay = pivot size bars (3-5). Real-Time: 0-1 bar. FVG: inherently 2 bars old when detected. OBs marked retroactively.

### Strengths
- Most comprehensive SMC indicator — covers structure, gaps, blocks, equal levels, stop hunts
- Dual structure modes (traditional + real-time) provide both confirmed and fast signals
- Three-tier FVG system with mitigation tracking
- ICT Anchored Market Structures at 3 timeframe tiers without multi-TF requests
- Stop Hunt detection adds liquidity sweep awareness

### Weaknesses
- Extremely complex and resource-heavy (max_lines=500, max_boxes=500, max_labels=500)
- Many overlapping structure layers can clutter chart
- No divergence detection — purely structural
- No volume or delta analysis
- Pivot-based structures have inherent delay

### Overlap With Other Indicators
No other indicator provides BOS/CHoCH, FVG, OB, or Stop Hunt detection. Structurally unique.

### Unique Value
The only indicator providing market structure breaks (BOS/CHoCH), Fair Value Gaps, Order Blocks, Equal Highs/Lows, and Stop Hunt detection. Irreplaceable structural backbone.

### Can It Be Used in a Strategy Script?
Partially — BOS/CHoCH breaks and FVG zones could define strategy entries, but complex visual components need stripping.

### Can It Be Automated?
Partially — alerts for BOS/CHoCH/FVG/StopHunt events are definable, but many type/tier/direction combinations.

### Role in My Current System
Core

### Keep / Review / Remove
**Keep** — Structural foundation of the ICT/SMC methodology. No other indicator replicates any of its features. Consider performance optimization if TradingView resource limits are hit.

---

## 5. SMT-CD Divergence

### Category
Divergence

### Purpose
Detects Smart Money Tool (SMT) divergence across correlated index futures (ES/NQ/YM/RTY) and Cumulative Delta Divergence Oscillator (CDDO) divergence using a hybrid CDDO+KVO Z-score engine. Original variant with configurable right-side pivot confirmation and optional real-time CDDO pivot mode.

### What It Measures
- **SMT:** Price pivot divergence between chart symbol and up to 3 comparison symbols (default: NQ1!, YM1!, RTY1!). Detects when one index makes higher highs while another makes lower highs (bearish) or vice versa.
- **CDDO:** Divergence between price pivots and a blended Z-score oscillator (CDDO 60% + KVO 40%) derived from proxy cumulative delta and Klinger Volume Oscillator.

### Inputs / Key Settings
- 3 comparison symbols with auto ES/NQ toggle
- 3 pivot ranges: Micro (2-10 bars), Intraday (12-25 bars), Session (30-60 bars)
- Per-range right-side confirmation bars (Micro: 2, Intraday: 1, Session: 0)
- CDDO Realtime Pivots toggle (left-side only for CDDO)
- Early SMT signals toggle (right=0 pass for faster signals alongside confirmed)
- CDDO filters: extreme zone, EMA trend, volume gate, ATR swing gate, cooldown, wait-for-close
- 10-point signal grading system (volume, candle confirmation, engine spread, trend slope)
- Invalidation: show/hide invalidated signals with faded color

### Signals Produced
- SMT labels with star count (1-3 stars for multi-symbol confirmation)
- CDDO labels ("RCDD" regular / "HCDD" hidden) with diamond tier (1-3)
- Merged SMT+CDDO bubbles when both fire at same bar+direction
- Invalidated signals shown faded (optional)
- Early [EARLY] vs Confirmed [CONF] stage labels

### Timing Nature
Mixed. SMT with right bars > 0: lagging. SMT with right bars = 0: coincident. CDDO realtime ON: 1-bar delay. CDDO realtime OFF: lagging by pivotLen bars.

### Confirmation Requirement
SMT: configurable right-side bars per range (0-10) + optional early pass. CDDO: pivot confirmation + volume gate + ATR swing gate + extreme zone + cooldown.

### Repaint Risk
Low. All `request.security()` use `barmerge.lookahead_off`. `waitForClose` flag gates signal logic behind `barstate.isconfirmed`.

### Delay Risk
SMT Micro: 2 bars. Intraday: 1 bar. Session: 0 bars. CDDO (realtime): 1 bar. CDDO (symmetric): pivotLen bars. Early signals add parallel 0-delay pass.

### Strengths
- Most feature-rich SMT+CDDO combination — dual-stage signals (early + confirmed)
- Multi-symbol confluence with star-rating system
- Asymmetric right-bar configuration per range tier
- Extensive CDDO filtering and 10-point grading
- Signal invalidation tracking

### Weaknesses
- High complexity with many tunable parameters
- Heavy computation: up to 108 pivot calculations per bar
- CDDO is proxy delta (not real order flow)
- Even micro-range pivots have 1-2 bar minimum delay

### Overlap With Other Indicators
Directly overlaps with SMT-CDDO-Lag (#6), SMT-CDDO-NoLagGPT (#7), SMT-CDDO-RT (#8) — all share ~80% identical core engine.

### Unique Value
Only variant offering dual-stage Early + Confirmed signals and configurable asymmetric right-side bars per range.

### Can It Be Used in a Strategy Script?
Yes — SMT and CDDO signals have clear boolean conditions.

### Can It Be Automated?
Yes — discrete events with direction, grading, and invalidation state.

### Role in My Current System
Core

### Keep / Review / Remove
**Review** — Most full-featured SMT variant but overlaps heavily with #6-8. Best candidate if both early and confirmed signals are valued, but highest resource usage. See consolidation recommendation below.

---

## 6. SMT-CDDO-Lag

### Category
Divergence

### Purpose
Variant using classic `ta.pivothigh()`/`ta.pivotlow()` with configurable right-side confirmation bars. Traditional symmetric or asymmetric pivot confirmation without real-time or early-signal mode.

### What It Measures
Same as #5: SMT inter-market divergence + CDDO+KVO Z-score oscillator divergence.

### Inputs / Key Settings
- Same 3 comparison symbols with auto ES/NQ
- Same 3 pivot ranges: Micro, Intraday, Session
- Separate right-bar inputs for SMT (Micro: 2, Intraday: 1, Session: 1) and CDDO (cddoRightBars: 2)
- No early signal mode, no realtime pivot toggle
- Signal cooldown default: 10 bars (vs 0 in #5)

### Signals Produced
Same as #5: SMT labels with stars, CDDO labels with diamond tiers, merged bubbles, invalidation fading. No [EARLY]/[CONF] distinction.

### Timing Nature
Lagging. All pivots use classic `ta.pivothigh(left, right)`. SMT Micro: 2-bar delay. Intraday: 1-bar. Session: 1-bar. CDDO: 2-bar.

### Confirmation Requirement
All pivots require right-side confirmation bars. CDDO has separate cddoRightBars setting. Same volume/ATR/extreme/cooldown filters.

### Repaint Risk
None. Classic `ta.pivothigh()/ta.pivotlow()` with right-side bars are inherently non-repainting.

### Delay Risk
Minimum 1-2 bars for all signals. CDDO: 2-bar delay. Most delayed variant.

### Strengths
- Most stable/reliable signals — zero repaint risk
- Separate CDDO right-bar control for independent tuning
- Higher default cooldown (10 bars) reduces noise
- Simple mental model: all signals are confirmed pivots

### Weaknesses
- Slowest signal delivery of all four SMT variants
- No early/fast signal option
- 1-2 bar delay can miss optimal scalping entries on 1-minute charts

### Overlap With Other Indicators
Directly overlaps with #5, #7, #8.

### Unique Value
Cleanest zero-repaint implementation. Best for backtesting and strategy development where signal stability is paramount.

### Can It Be Used in a Strategy Script?
Yes

### Can It Be Automated?
Yes — most reliable for automation due to zero repaint.

### Role in My Current System
Optional (unless backtesting is the priority)

### Keep / Review / Remove
**Review** — Redundant with #5 (which can replicate this behavior). Keep only if used specifically for backtesting.

---

## 7. SMT-CDDO-NoLagGPT

### Category
Divergence

### Purpose
Zero-lag variant using "CloseBreak" pivot detection — triggers when close breaks above rolling N-bar high or below rolling N-bar low. Adds enhanced SMT filtering (trend, slope, reversal break, ATR swing, cooldown, min symbol confirmations) and running-extremes pivot tracking.

### What It Measures
Same core: SMT inter-market divergence + CDDO+KVO divergence. Both SMT and CDDO pivots detected via CloseBreak rather than traditional ta.pivothigh/ta.pivotlow.

### Inputs / Key Settings
- Same symbols (NQ, YM, RTY, auto ES/NQ)
- Same 3 pivot ranges (Micro/Intraday/Session — all ON by default)
- Swing Trigger Mode: CloseBreak (fixed)
- SMT Strong Filters: EMA trend, slope filter, reversal break requirement, ATR swing (0.5x ATR), cooldown (8 bars), min symbol confirmations (1)
- Same CDDO engine with all filters

### Signals Produced
Same labels/lines/merged bubbles as #5, without [EARLY]/[CONF] staging since all signals are inherently zero-lag.

### Timing Nature
Coincident/Leading. Both SMT and CDDO pivots fire on current bar when close breaks rolling range. Zero right-side delay.

### Confirmation Requirement
CloseBreak requires bar close beyond rolling N-bar extreme. Additional filters: EMA trend, slope, reversal break, ATR swing minimum, min symbol confirmations.

### Repaint Risk
Medium. CloseBreak fires on current bar's close. With `waitForClose` ON and `barstate.isconfirmed`, signals are stable once bar closes. On realtime bars before close, signal can appear/disappear.

### Delay Risk
Zero bars after bar close. Fastest signal delivery of all four variants.

### Strengths
- Zero-lag signal delivery — optimal for 1-minute scalping
- Enhanced SMT filtering layer reduces noise despite no right-side delay
- Running-extremes pivot tracking avoids traditional pivot lookback
- Highest conviction with min confirmations set to 2+ symbols

### Weaknesses
- Higher false-positive rate than lagging variants despite filters
- Running-extremes SMT tracking is most complex pivot logic — harder to debug
- CloseBreak can fire prematurely on volatile bars
- Medium repaint risk on open bars

### Overlap With Other Indicators
Directly overlaps with #5, #6, #8.

### Unique Value
Only variant using CloseBreak with running-extremes tracking and enhanced SMT filters (trend, slope, reversal break, min confirmations). Most aggressive noise-filtering for zero-lag.

### Can It Be Used in a Strategy Script?
Yes — CloseBreak signals are discrete bar-close events.

### Can It Be Automated?
Yes — zero-lag signals ideal for real-time automation, though higher false-positive rate requires filter tuning.

### Role in My Current System
Core (if real-time zero-lag execution is the priority)

### Keep / Review / Remove
**Review** — Most innovative variant with strongest noise-filtering for zero-lag signals. See consolidation recommendation.

---

## 8. SMT-CDDO-RT

### Category
Divergence

### Purpose
Real-time zero-lag variant using `ta.pivothigh(high, N, 0)` / `ta.pivotlow(low, N, 0)` (left-only, zero right bars). Adds wick rejection filter, volume Z-score filter, ATR swing filter, and per-direction cooldown maps. Simplest zero-lag approach.

### What It Measures
Same core: SMT inter-market divergence + CDDO+KVO divergence. Pivots detected with N left bars and 0 right bars.

### Inputs / Key Settings
- Same symbols (NQ, YM, RTY, auto ES/NQ)
- 3 pivot ranges: Micro (OFF by default), Intraday (ON), Session (OFF)
- Wick Reject Ratio (default 0.10) — requires minimum rejecting wick proportion
- Volume Z-Score Threshold (default 0.0 = disabled)
- Min Price Swing ATR (default 0.3x)
- Signal Cooldown (default 8 bars, per bull/bear direction)

### Signals Produced
Same labels/lines/merged bubbles as other SMT variants. No stage distinction.

### Timing Nature
Coincident. `ta.pivothigh(high, N, 0)` fires when current bar is highest of last N+1 bars. Zero right-side delay.

### Confirmation Requirement
Left-side structure only. Filtered by wick rejection, volume Z-score, ATR swing minimum, and cooldown.

### Repaint Risk
Medium. `ta.pivothigh(src, left, 0)` evaluates on current bar. With `waitForClose` ON, gated to `barstate.isconfirmed`. Wick rejection adds validation layer. Stable on confirmed bars.

### Delay Risk
Zero bars after bar close.

### Strengths
- Simpler implementation than #7 (no running-extremes, no CloseBreak)
- Wick rejection filter is unique noise reducer
- Per-direction cooldown prevents signal clustering
- Micro range defaults OFF (acknowledges noise at that scale)
- Lighter computational footprint than #7

### Weaknesses
- Less sophisticated pivot tracking than #7
- Wick filter may reject valid signals during strong momentum
- Volume Z-score disabled by default (needs tuning)
- Medium repaint risk on open bars

### Overlap With Other Indicators
Directly overlaps with #5, #6, #7.

### Unique Value
Only variant with wick rejection filtering and volume Z-score threshold. Simplest zero-lag implementation — easiest to maintain and debug.

### Can It Be Used in a Strategy Script?
Yes

### Can It Be Automated?
Yes — clean signal events with wick/volume validation.

### Role in My Current System
Core (if simplicity + zero-lag is the priority)

### Keep / Review / Remove
**Review** — Solid zero-lag variant, simpler than #7 but fewer noise filters. See consolidation recommendation.

---

## Cross-Indicator Analysis

### Redundancy Map

The 4 SMT-CDDO variants (#5-#8) share ~80% identical code. They differ only in pivot detection mode and filtering:

| Variant | Pivot Mode | Right-Side Delay | Unique Filters | Repaint |
| --- | --- | --- | --- | --- |
| #5 SMT-CD Divergence | Asymmetric right bars + optional RT | 0-2 bars | Early + Confirmed stages | Low |
| #6 SMT-CDDO-Lag | Classic symmetric/asymmetric | 1-2 bars | Independent CDDO right bars | None |
| #7 SMT-CDDO-NoLagGPT | CloseBreak + running extremes | 0 bars | Trend/slope/reversal/min confirms | Medium |
| #8 SMT-CDDO-RT | ta.pivothigh(N, 0) | 0 bars | Wick reject, vol Z-score | Medium |

### Consolidation Recommendation

**Keep as-is:** #1 Market Session Lines, #2 Premarket Levels, #3 OTE-OR-HTF-PO3, #4 SMC-FVG-ICT-DOB-SH — all serve non-overlapping roles.

**Consolidate:** #5, #6, #7, #8 — merge into a single indicator with a "Pivot Mode" dropdown (Symmetric, Asymmetric, CloseBreak, Zero-Lag) to eliminate redundancy while preserving all capabilities. This would free up 3 TradingView indicator slots.

### Decision Flow Coverage

| Decision Flow Step | Indicators That Support It |
| --- | --- |
| 1. Identify session and time of day | #1 Market Session Lines, #2 Premarket Levels |
| 2. Determine directional bias | #3 OTE (HTF PO3), #4 SMC (BOS/CHoCH) |
| 3. Check HTF structure/context | #3 OTE (HTF PO3), #4 SMC (ICT AMS) |
| 4. Look for liquidity interaction/sweep | #2 Premarket Levels, #4 SMC (Stop Hunt, Equal H/L) |
| 5. Look for divergence/confirmation | #5-8 SMT-CDDO variants |
| 6. Wait for trigger candle/displacement | #4 SMC (Displacement OB, FVG) |
| 7. Define invalidation | #5-8 (signal invalidation), #4 SMC (structure break) |
| 8. Enter | #3 OTE zones, #4 FVG zones, #5-8 divergence signals |
| 9. Manage to target/exit | #2 Premarket Levels (liquidity targets), #3 OR levels |
