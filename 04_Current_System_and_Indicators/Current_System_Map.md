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

**Required confluence (all preferred, minimum 2-3):**

| Signal | Role | Indicator |
|--------|------|-----------|
| Stop Hunt (liquidity sweep) | Setup condition | Premarket Levels, SMC-FVG Equal H/L |
| SMT Divergence (or any divergence) | Primary trigger | SMT-CDDO, CVD_Divergence, SMT-CDDO-NoLagGPT, SMT-CDDO-RT |
| iFVG or FVG | Entry zone | SMC-FVG-ICT-DOB-SH |
| CHoCH, MSS, or CISD | Structural confirmation | SMC-FVG-ICT-DOB-SH, OTE-OR-HTF-PO3 |

**Entry mechanics:** Mixed
- Limit order pre-placed at iFVG/FVG zone or OTE level when setup is clear in advance
- Market order after trigger candle closes when price is moving aggressively (aggressive entry)

**SMT variant:** Any variant that fires in confluence — no hard preference between confirmed vs. zero-lag. Resolving which to trust is an open confusion point (see §10).

---

## 5. Current Exit Logic

**Targets (first hit wins):**

1. **Specific liquidity** — nearest visible pool: premarket high/low, session high/low, equal highs/lows, BSL/SSL visible on chart
2. **Fixed R multiple** — fallback when no clear liquidity target or as partial exit

No trailing stop currently. No opposing-signal exit. Exit is mechanical once target is defined at trade entry.

---

## 6. Current Invalidation Logic

**Stop placement:** High/low of the candle immediately after the stop hunt candle.
- Long (bullish): stop = low of the candle after the sweep low
- Short (bearish): stop = high of the candle after the sweep high

This gives tight, structure-defined risk anchored to the confirmation candle — not the sweep wick itself.

**Trade invalidation triggers:**
- Price closes back through the FVG/iFVG entry zone (imbalance fully filled without continuation)
- Price takes out the stop candle level defined above
- No time-based invalidation rule currently

**SMT built-in invalidation:** The CDDO indicators fade divergence signals when price breaks the divergence pivot. This serves as a secondary invalidation signal but not the primary stop trigger.

---

## 7. Current Session Preferences

**Best windows:**
- Silver Bullet 1: pre-open / London overlap (early morning)
- Silver Bullet 2: 10:00–11:00 ET (post-open Silver Bullet)

**Session rules:**
- No hard time-based avoidance — trade on signal only regardless of session
- No maximum trade count per session

**Note:** The OR module tracks 04:00–09:30 for overnight range context. Market Session Lines marks 09:30 open, 12:00 noon, 15:00 power hour. No explicit avoidance of noon lull or power hour.

---

## 8. Current Strengths

- **Stop hunt + SMT divergence + iFVG confluence** setups — highest-confidence pattern: liquidity swept, divergence confirmed, imbalance provides entry zone, structure shift confirms direction
- **Silver Bullet timing** — setups during 10:00–11:00 ET have cleaner follow-through vs. random intraday entries
- **Precise stop placement** — anchoring stop to the candle after the sweep (not the wick) gives tight, well-defined risk with clear invalidation
- **Multi-source divergence** — having CVD, SMT, and volume divergence available provides multiple lenses on the same price action

---

## 9. Current Weaknesses

**Primary leak: early entries before full confirmation.**
- Entering on 1-2 signals (e.g., FVG + divergence) without waiting for structure confirmation (CHoCH/MSS/CISD)
- Result: price continues against the trade before the actual setup triggers
- Pattern: impatience at the zone, entering on the first divergence signal rather than the confirmed structure shift

**Secondary issues:**
- 4 SMT variants (confirmed, NoLagGPT, RT, base) fire at slightly different times — creates uncertainty about which to act on
- No max-trade rule means no circuit breaker after a string of early entries

---

## 10. Current Sources of Confusion

**1. Which SMT variant to trust (confirmed vs. NoLagGPT vs. RT)**
- All four variants can fire on the same bar or different bars
- Zero-lag variants (NoLagGPT, RT) signal earlier but repaint risk; confirmed lags but is clean
- No current rule for which takes priority when they disagree

**2. Which structure break label matters (BOS vs. CHoCH vs. MSS vs. CISD)**
- SMC indicator labels BOS and CHoCH; OTE-OR module tracks PO3; CISD is a separate concept
- All are "structure shifts" but with different implications for conviction
- No decision rule for minimum structure break required (e.g., "CHoCH minimum, prefer MSS")

**3. When is confluence "enough" to enter vs. wait for more**
- The full ideal setup (stop hunt + divergence + FVG + structure shift) is rare
- No explicit rule for minimum confluence count — leads to inconsistent entries
- Early entry leak (§9) is directly caused by this ambiguity
