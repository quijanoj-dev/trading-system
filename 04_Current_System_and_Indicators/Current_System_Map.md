# Current System Map

## 1. What I Currently Trade
I primarily trade:
- ES
- NQ

I execute mainly on:
- 1-minute chart

## 2. What I Currently Look For
- market structure
- session behavior
- divergences
- displacement
- liquidity sweeps
- FVGs
- momentum shifts
- support / resistance
- trend continuation
- reversal setups

## 3. My Current Decision Flow

| Step | Action | Supporting Indicators |
| --- | --- | --- |
| 1 | Identify session and time of day | Market Session Lines, Premarket Levels |
| 2 | Determine directional bias | OTE-OR-HTF-PO3 (HTF PO3), SMC-FVG-ICT-DOB-SH (BOS/CHoCH) |
| 3 | Check higher timeframe structure/context | OTE-OR-HTF-PO3 (HTF PO3, OTE), SMC-FVG-ICT-DOB-SH (ICT AMS) |
| 4 | Look for liquidity interaction or sweep | Premarket Levels, SMC-FVG-ICT-DOB-SH (Stop Hunt, Equal H/L) |
| 5 | Look for divergence / confirmation | SMT-CD Divergence / SMT-CDDO variants |
| 6 | Wait for trigger candle or displacement | SMC-FVG-ICT-DOB-SH (Displacement OB, FVG) |
| 7 | Define invalidation | SMT-CDDO (signal invalidation), SMC (structure break) |
| 8 | Enter | OTE zones, FVG zones, divergence signals |
| 9 | Manage to target or exit | Premarket Levels (liquidity targets), OR levels |

## 4. Current Entry Logic

*Questions to answer based on your indicator suite:*

- Your indicators detect SMT divergence, FVG zones, OTE fib levels, and displacement order blocks. Which of these are **entry triggers** vs. **confirmations**? In what combination?
- Do you require SMT divergence before entering, or is a BOS/CHoCH + FVG enough?
- Which SMT variant do you actually use for entries — the confirmed lag version or one of the zero-lag variants (NoLagGPT / RT)?
- Do you enter at OTE fib zones, at FVG zones, at displacement OB zones, or a combination?
- Is your entry on a limit order at a zone, or on a market order after a trigger candle?

## 5. Current Exit Logic

*Questions to answer:*

- Do you use fixed tick/point targets, or do you target specific liquidity levels (Premarket Levels, session highs/lows)?
- Do you exit on opposing SMT divergence signals?
- Do you use trailing stops based on structure (e.g., BOS in the opposite direction)?
- Does the OTE-OR module provide your exit targets (e.g., -1, -2 fib extensions)?
- Is your exit logic currently mechanical or mostly discretionary?

## 6. Current Invalidation Logic

*Questions to answer:*

- Your SMT-CDDO indicators have built-in invalidation logic (signal fading when price breaks the divergence pivot). Is that your primary invalidation?
- Do you invalidate based on structure (e.g., CHoCH against your trade direction from SMC indicator)?
- Is your stop placement at a fixed distance, at the invalidation level, or at a structure level?
- Do you have a time-based invalidation (e.g., exit if target not hit within N bars)?

## 7. Current Session Preferences

*Questions to answer (Market Session Lines marks Open 09:30, Noon 12:00, Power Hour 15:00, Close 16:00):*

Best times:
- Do you primarily trade the open (09:30-10:30)?
- Do you trade the Silver Bullet windows (your OR module tracks 04:00-09:30)?
- Do you trade the Power Hour (15:00-16:00)?

Avoid:
- Do you avoid the Noon Relax zone (12:00-14:00)?
- Do you avoid trading before 09:30 (premarket)?
- Do you have a max trades per session rule?

## 8. Current Strengths

*Questions to answer:*

- Which setups do you feel most confident executing?
- Which indicator signals have been most reliable in your experience?
- What market conditions produce your best results (trending, ranging, high-vol)?

## 9. Current Weaknesses

*Questions to answer:*

- Where do you lose the most — false signals, late entries, early exits, or overtrading?
- Do you find yourself ignoring invalidation signals?
- Are there too many indicators creating conflicting signals?
- Is the 4-variant SMT divergence suite causing confusion about which signal to follow?

## 10. Current Sources of Confusion

*Questions to answer:*

- Which indicator signals do you find most ambiguous or hard to interpret?
- Do you struggle with when to use confirmed (lagging) vs. zero-lag divergence signals?
- Is there overlap between BOS/CHoCH structure breaks and SMT divergence that creates noise?
- Do you find it difficult to determine which FVG tier (T1/T2/T3) is worth trading?
