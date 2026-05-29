# Course 01 — ICT SMC PO3 Strategy
**Source:** `Trading Summary/ICT-SMC-PO3/ICT SMC PO3 Strategy.pdf`  
**Extracted:** 2026-05-28  
**Framework:** AMD (Accumulation → Manipulation → Distribution)

---

## AMD Framework Overview

| Phase | Timeframe | What to Look For |
|-------|-----------|-----------------|
| Accumulation | LTF (1m, 5m, 15m) | Consolidation; price sweeping Highs or Lows to set up Manipulation |
| Manipulation | 5m, 15m, 1h | SMT Divergence OR Liquidity Sweep / Stop Hunt through Premium/Discount PD Arrays |
| Distribution | 1m, 5m | Entry models fire after Manipulation confirmed |

---

## HTF Analysis (1W, 1D, 4h, 1h)

1. Directional Bias — Bullish (HHs/HLs) or Bearish (LHs/LLs)
2. Market Structure SMC — identify swing structure
3. PD Arrays — Premium/Discount levels, Order Blocks
4. Manipulation confirmation — HTF Trend Confirmation

---

## LTF Analysis (15m, 5m, 1m)

1. Accumulation — LTF Consolidation (price taking out Highs/Lows)
2. Manipulation — Stop Hunt or SMT Divergence
3. Distribution — entry model fires

---

## Entry Models (Distribution Phase)

### Entry Model 1 (1m, 5m)
```
Turtle Soup → FVG or iFVG → Order Block → Inversion
```
- Turtle Soup = price sweeps a level then reverses sharply
- FVG or iFVG = gap confirms displacement
- OB = institutional order block as entry zone
- Inversion = OB flips support ↔ resistance

### Entry Model 2 (1m, 5m) — **SBV1 uses this**
```
CHoCH or MSS or CISD → FVG or iFVG → Breaker Block (L, H, LL, HH) → Inversion
```
- CHoCH (Change of Character) or MSS (Market Structure Shift) or CISD
- FVG/iFVG confirms displacement
- Breaker Block = prior swing high/low that price should respect

### Entry Model 3
```
LTF FVG → PO3 model → Inversion
```
- 1m/15m/1h PO3: **Buy below 15m/1h candle Open**, Sell above 15m/1h candle Open
- 5m/1h/4h PO3: Buy below 1h/4h candle Open, Sell above 1h/4h candle Open
- Entry is below/above the current period's open = Power of 3 AMD within that candle

---

## Manipulation Phase Detail

**Confirmed by either:**
- SMT Divergence (ES makes new extreme, NQ diverges)
- Liquidity Sweep = Stop Hunt — price crosses Premium PD Array (for Shorts) or Discount PD Array (for Longs)

**PO3 Models active during Manipulation:**
- 1m/15m/1h PO3
- 5m/1h/4h PO3

---

## Pre-Trade Checklist

- [ ] Identify Trend & Directional Bias (1h, 4h, 1D, 1W, 1M)
- [ ] Draw FVG in 1m, 5m, 15m charts
- [ ] Draw Supply/Demand Zones (Premium/Discount Arrays) in 15m chart
- [ ] Identify Stop Hunts + SMT Divergence
- [ ] Create Entry Scenarios in 15m chart using:
  - Asia High/Low
  - London High/Low
  - PDH (Prior Day High), PDL (Prior Day Low), PDC (Prior Day Close)
  - PWH (Prior Week High), PWL (Prior Week Low)
  - PMH (Prior Month High), PML (Prior Month Low), PMO (Prior Month Open)

---

## Gap Analysis vs SBV1 Implementation

| Strategy Rule | SBV1 Status | Notes |
|--------------|-------------|-------|
| CHoCH trigger | ✅ Implemented | `signals.py` — close crosses last confirmed pivot |
| FVG detection | ✅ Implemented | 3-bar gap >= `fvg_min` |
| SMT Divergence | ✅ Implemented | ES/NQ divergence flag (optional gate) |
| Stop Hunt | ✅ Implemented | `bull_hunt` / `bear_hunt` sweeps recent high/low |
| HTF bias (EMA) | ✅ Implemented | 15m EMA-20 gate, `htf_ema_period=20` |
| **iFVG (Inverse FVG)** | ❌ Missing | SBV1 only checks regular FVG; iFVG = prior FVG that inverted and now acts as support/resistance |
| **Order Block** | ❌ Missing | Entry Model 1+2 require OB confirmation zone |
| **Breaker Block** | ❌ Missing | Prior swing high/low used as entry zone (Entry Model 2) |
| **MSS / CISD** | ❌ Missing | MSS = stronger version of CHoCH; CISD = candle-level structure shift |
| **PO3 open bias** | ❌ Missing | Buy below 15m/1h open, sell above — not checked in signals.py |
| **Key reference levels** | ❌ Missing | PDH, PDL, PWH, PWL, Asia H/L, London H/L not used |
| **Premium/Discount zones** | ⚠️ Partial | HTF EMA is a proxy; no proper 50% equilibrium range check |
| Entry Model 1 (Turtle Soup) | ❌ Missing | Full model not implemented |
| Entry Model 3 (LTF FVG + PO3) | ❌ Missing | Not implemented |

---

## Improvement Candidates for SBV1 (Prioritized)

### High Priority — Low Effort
1. **PO3 open bias gate** — add check: long only if `entry_price < htf_open`, short only if `entry_price > htf_open`. Small change in signals.py. Filters entries that are already past the manipulation target.
2. **iFVG detection** — inverse of current FVG logic: a prior bullish FVG that price has since filled and is now retesting from below. Adds 1 more confluence gate.

### Medium Priority — Medium Effort
3. **Order Block detection** — identify the last bullish/bearish displacement candle before the FVG. Check if entry is near (within 0.5 ATR of) the OB zone.
4. **Key reference levels** — fetch PDH, PDL, PWH, PWL from daily/weekly OHLC. Add gate: avoid entries where stop is beyond a key level (improves stop placement).

### Low Priority — High Effort
5. **MSS + CISD** — more granular structure confirmation. Significant refactor to signals.py state machine.
6. **Entry Model 1 (Turtle Soup)** — new signal path. Build after Model 2 (current) accumulates n=30.
7. **Entry Model 3 (PO3)** — requires multi-timeframe open tracking.

---

## Session Notes

SBV1 currently implements a focused subset of Entry Model 2. The canonical strategy is broader — Entry Models 1 and 3 are entire additional signal paths not yet built. Immediate wins: PO3 open bias gate (1-line filter) and iFVG detection (adds confluence).
