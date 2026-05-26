# Change Log

Track every rule change, parameter adjustment, or system version update here.
Format: one entry per change, newest at top.

---

## Entry Format
- **Date:**
- **System Version:**
- **Change Made:**
- **Reason:**
- **Expected Effect:**
- **Result:** *(fill after observing forward test impact)*

---

## 2026-05-26 — V1 System Defined

- **Date:** 2026-05-26
- **System Version:** V1.0 — Silver Bullet Only
- **Change Made:** Initial system definition. Candidate 2 selected from 4-candidate synthesis (see 05_Synthesis_and_Candidate_Systems/Version_1_Decision.md).
- **Reason:** Current system (Current_System_Map.md) had no hard rules — informal 2–3 signal minimum with no time constraint. Primary leak was early entries before CHoCH confirmation. V1 formalizes strict rules to eliminate the leak.
- **Expected Effect:** Lower trade frequency (1–2/week vs untracked). Higher per-trade quality. Elimination of pre-10am and post-11am trades.
- **Result:** *(pending backtest + forward test)*

**V1.0 Rules:**
1. Time gate: 10:00–11:00 ET only. No exceptions.
2. Stop hunt required: wick through recent swing low/high, close back inside.
3. SMT divergence required: confirmed variant only. ES lower low + NQ higher low (bull). ES higher high + NQ lower high (bear).
4. FVG/iFVG required: imbalance zone present within 6 bars of stop hunt.
5. CHoCH required: minimum structure break. Close through most recent opposite swing. BOS alone is not sufficient.
6. Stop: low/high of candle immediately after the sweep candle (not the wick).
7. Target: nearest visible liquidity pool. Fallback: 2R fixed.
8. No max trade count per day. No time-based exit. Manage to target or stop.
