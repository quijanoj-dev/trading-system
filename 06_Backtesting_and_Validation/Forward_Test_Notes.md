# Forward Test Notes

---

## System
V1.0 — Silver Bullet Only (defined 2026-05-26)
Full rules in Change_Log.md entry 2026-05-26.

## Testing Period
- Start: 2026-05-27 (next trading day after system definition)
- Minimum duration: 30 qualifying setups OR 3 months, whichever comes first
- A "qualifying setup" = all 4 signals present in session (counted even if not taken)

## Execution Notes

**Log every session, even if no trade taken.** Template per session:
```
Date: YYYY-MM-DD
Session active: 10:00–11:00 ET observed: Y/N
Stop hunt(s) seen: [describe level swept, direction]
SMT divergence: Y/N — [which instrument diverged]
FVG present: Y/N — [price level of zone]
CHoCH confirmed: Y/N — [level broken, bar time]
Full confluence achieved: Y/N
Trade taken: Y/N
  If yes: entry price, stop level, target, outcome (W/L), R result
  If no: why not (signal missing / already in trade / rule violation)
```

## What Matched Research
*(Fill as forward test progresses)*

-

## What Broke Down
*(Fill as forward test progresses)*

-

## Rule Violations
*(Log every rule violation, even minor ones. Pattern recognition happens here.)*

- Format: [Date] | Rule violated | What happened instead | Why

## Adjustments to Consider
*(Flag ideas here — do NOT implement until 30+ setups logged)*

- Do NOT adjust rules during the first 30 setups. Data collection phase only.
- After 30 setups: review Change_Log.md, propose one change at a time, document expected effect before implementing.

## Key Questions Forward Test Should Answer

1. How often does full confluence (all 4 signals) occur in the 10:00–11:00 window? (Frequency check)
2. What is the win rate on confirmed full-confluence setups?
3. Does the time gate eliminate the early-entry pattern or does it just shift it to 10:00am entries without full confluence?
4. Is CHoCH the actual confirmation or are entries still happening on FVG alone?
5. Which is the more common failure mode: stop hunt with no follow-through, or SMT divergence that resolves before CHoCH confirms?
