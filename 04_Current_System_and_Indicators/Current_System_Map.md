# Current System Map

**System:** ICT-SMC PO3-AMD (Accumulation-Manipulation-Distribution)
**Version:** Silver Bullet V1
**Last updated:** 2026-05-27

---

## The 6-Gate A+ Decision Framework

If ANY gate fails → **NO TRADE**. Journal only.

---

### Gate 1 — CONTEXT GATE
*Am I allowed to trade today?*

| Check | Rule |
|-------|------|
| News | High-impact events checked (economic calendar / Benzinga). No trade ±30 min of high-impact release. |
| Session | London or New York only. No other sessions. |
| State | Calm, focused, not trading to recover losses. |
| Daily loss limit | NOT hit. |
| Consecutive losses | Max consecutive loss rule respected. |

**IF all YES → Gate 2. ELSE → NO TRADE.**

---

### Gate 2 — HTF BIAS GATE
*Is the market offering a narrative?*

| Check | Rule |
|-------|------|
| HTF POI identified | PDH/PDL, PWH/PWL, or Swing H/L marked on chart. |
| Directional bias | Clear directional bias OR clear range context established. |
| Price proximity | Price is near a HTF Point of Interest. |
| Narrative coherent | Expectation makes sense (know where price wants to go). |

**Supporting indicators:** Premarket Levels (PDH/PDL/PWH/PWL), OTE-OR-HTF-PO3 (HTF PO3 visualization)

**IF all YES → Gate 3. ELSE → NO TRADE.**

---

### Gate 3 — PO3 STRUCTURE GATE
*Is the algorithm active?*

| Phase | Condition |
|-------|-----------|
| Accumulation | Price compressing / ranging — visible consolidation. |
| Manipulation | Liquidity grab confirmed: stop hunt past prior H/L, OR SMT divergence between ES/NQ, OR turtle soup / CVD divergence. Long-body candle with FVG or price over-extended to EMA qualifies. |
| Distribution intent | Direction is clear after manipulation. Price shows intent to expand away from the sweep. |

All three phases must be identifiable on the 1m chart. Manipulation confirmation is required before any entry attempt.

**Supporting indicators:** SMC-FVG-ICT-DOB-SH (Stop Hunt labels), SMT-CD Divergence (SMT divergence), OTE-OR-HTF-PO3 (PO3 structure)

**IF all YES → Gate 4. ELSE → NO TRADE.**

---

### Gate 4 — LTF ENTRY GATE
*Is this a textbook A+ execution?*

All four signals required. Missing one = NO TRADE.

| Signal | Requirement |
|--------|-------------|
| 1. Stop hunt | Liquidity sweep of prior high/low confirmed on 1m. |
| 2. SMT divergence | ES and NQ diverge at the sweep point (confirmed SMT variant — not zero-lag). |
| 3. iFVG or FVG | Entry zone present in the reversal area. |
| 4. CHoCH or MSS | Market structure shift confirmed on 1m (minimum CHoCH, prefer MSS). CHoCH = 1m close above/below most recent opposing swing, not just a wick through. |

**Entry mechanics:**
- Entry is NOT chasing: price must come to the level (FVG/iFVG or OTE zone), not market-order into momentum.
- Limit order at FVG/iFVG zone when setup is clear in advance.
- Market order only after confirmed CHoCH/MSS candle close (no anticipatory entry).

**Stop placement:**
- Long: stop = low of the candle immediately after the sweep candle.
- Short: stop = high of the candle immediately after the sweep candle.
- Stop anchored to the confirmation candle structure, not the sweep wick itself.

**Supporting indicators:** SMC-FVG-ICT-DOB-SH (FVG, CHoCH/MSS, Stop Hunt), SMT-CD Divergence (confirmed SMT), OTE-OR-HTF-PO3 (OTE entry zones)

**IF all four signals present AND entry is at level → Gate 5. ELSE → NO TRADE.**

---

### Gate 5 — RISK GATE
*Is this mathematically worth it?*

| Check | Rule |
|-------|------|
| Stop loss | Logical, predefined — candle after sweep (Gate 4 rule). |
| Take profit | Logical, predefined — nearest visible liquidity pool (premarket H/L, session H/L, equal H/L, BSL/SSL), fallback = fixed R. |
| Risk : Reward | ≥ 1:3. If the visible target does not offer at least 3R, do not take the trade. |
| Position size | Respects account rules. |
| Max exposure | Total account risk ≤ 10% at any time. |

**Supporting indicators:** Premarket Levels (TP targets), OTE-OR-HTF-PO3 (OR levels as targets)

**IF all YES → Gate 6. ELSE → NO TRADE.**

---

### Gate 6 — EXECUTION GATE
*Can I manage this trade cleanly?*

| Check | Rule |
|-------|------|
| Know where wrong | Invalidation level defined before entry. |
| Know where right | Take profit level defined before entry. |
| SL discipline | Stop loss will NOT be moved emotionally. |
| Loss acceptance | The maximum loss is accepted before entering. |

**IF all YES → EXECUTE. ELSE → NO TRADE.**

---

## Execution Window

**Session:** New York only (primary execution window: 10:00–11:00 ET Silver Bullet)
- Active monitoring begins at 09:30 ET (Open)
- Primary entry window: 10:00–11:00 ET
- No trades outside London or New York sessions
- No trades during high-impact news ±30 min

---

## Post-Trade (Mandatory — Win or Loss)

1. Screenshot HTF + LTF.
2. Log in TradeZella. Tag: A+ / Rule-break / Emotion.
3. Write ONE improvement (max).

---

## Indicator-to-Gate Map

| Indicator | Gate |
|-----------|------|
| Market Session Lines | Gate 1 (session context) |
| Premarket Levels | Gate 2 (HTF POI), Gate 5 (TP targets) |
| OTE-OR-HTF-PO3 | Gate 2 (HTF bias), Gate 3 (PO3 structure), Gate 4 (OTE entry zones) |
| SMC-FVG-ICT-DOB-SH | Gate 3 (manipulation: Stop Hunt), Gate 4 (FVG/iFVG, CHoCH/MSS) |
| SMT-CD Divergence | Gate 3 (SMT divergence confirmation), Gate 4 (required signal #2) |

---

## The One Rule That Overrides Everything

**"No setup is better than a forced setup. Capital protection > opportunity."**
