# Project-OS Skill Candidates — Trading System
**Source:** NLM 239-source audit synthesis (2026-05-25)
**Purpose:** Skills to create in `~/.claude/skills/` that encapsulate trading system intelligence

---

## Skill 1: `/volume-regime` — Combined Regime + CVD Gate

**Trigger:** `/volume-regime`
**Purpose:** Before any ES/NQ trade, query current HMM regime + CVD divergence alignment. Returns a structured session brief: regime state, divergence signal, TICK/ADD reading, session bias.

**Logic:**
1. Call `RegimeDetector.predict(ohlcv)` → regime (bull/bear/chop) + probability
2. Query TradingView MCP (`mcp__tradingview__data_get_study_values`) → current CVD_Divergence signal
3. Query `mcp__tradingview__data_get_pine_labels` → SMT-CDDO active signals
4. Fetch $ADD + $TICK via `mcp__tradingview__quote_get`
5. Output: regime + CVD direction + TICK level + session bias + trade filter (e.g., "CHOP regime — no momentum entries, range only")

**Files to create:**
```
~/.claude/skills/volume-regime/
  SKILL.md       ← skill definition
```

**Cross-references:**
- `execution/hmm_regime/regime_detector.py` — Python HMM source
- `08_TradingView_Indicators/mmt/CVD_Divergence.pine` — CVD signal source
- `CLAUDE.md` / `Risk.md` — regime-gated risk rules

---

## Skill 2: `/es-nq-monitor` — Real-Time Market Monitor

**Trigger:** `/es-nq-monitor`
**Purpose:** Live session assistant. Monitors ES + NQ via TradingView MCP, fires alerts when high-conviction setups align (footprint exhaustion + CVD divergence + TICK extreme).

**Logic:**
1. `mcp__tradingview__chart_set_symbol` → ES1! (or NQ1!)
2. Poll `mcp__tradingview__data_get_study_values` every bar for: CDDO signal, CVD direction, volume Z-score
3. Check `mcp__tradingview__data_get_pine_labels` for SMT divergence labels
4. When 3-factor convergence (regime + CVD + TICK threshold): emit alert via `mcp__tradingview__alert_create` or push notification
5. Log signal to `trades.log` format via PostTrade.sh

**Session timing gates:**
- Only active 8:15–11:30 AM EST and 1:30–3:00 PM EST (NY macro windows)
- Skip during news blackout: CPI, FOMC, NFP

**Files to create:**
```
~/.claude/skills/es-nq-monitor/
  SKILL.md
```

---

## Skill 3: `/pine-v6-converter` — PineScript Migration Assistant

**Trigger:** `/pine-v6-converter`
**Purpose:** Assists migrating existing v5 Pine indicators to v6 (when v6 becomes production). Documents known v5 patterns in this codebase and their v6 equivalents.

**Known v5 patterns in codebase to track for migration:**
| v5 Pattern | File | v6 Change Needed |
|-----------|------|-----------------|
| `ta.pivothigh(high, N, 0)` | SMT-CDDO-RT.pine | Verify v6 `ta.*` namespace changes |
| `barstate.isconfirmed` gate | Multiple | Likely unchanged |
| `request.security()` multi-symbol | SMT indicators | Check v6 security() signature |
| `strategy.entry("short")` | Strategy variants | Check v6 strategy syntax |
| `ta.highest(high, N)[1]` CloseBreak | NoLagGPT | Verify offset syntax |

**Note:** Sources contain no v6 content. This skill is forward-looking — build when TradingView releases v6 production docs. Use `/context7` to pull Pine v6 docs when available.

**Files to create:**
```
~/.claude/skills/pine-v6-converter/
  SKILL.md
```

---

## Skill 4: `/trading-session-start` — Pre-Market Brief Hook

**Trigger:** `/trading-session-start`
**Purpose:** Runs the 5-layer agent stack L1+L3 sequence before market open. Outputs structured session brief in <60 seconds.

**Sequence:**
1. Load `Risk.md` → print today's max drawdown ceiling + APEX trailing threshold status
2. Call `RegimeDetector` → current regime + probability
3. Query overnight high/low via `mcp__tradingview__data_get_ohlcv` (ES1!, D timeframe, last 2 bars)
4. Fetch $ADD + $TICK opening levels via TradingView MCP
5. Flag today's news events (FOMC, CPI, NFP) → if funded account: mark as blackout
6. Output `context/session.md`:
   ```
   DATE: 2026-05-25
   REGIME: bull 95.7%
   OVERNIGHT_HIGH: 5340.25  OVERNIGHT_LOW: 5310.00
   SESSION_BIAS: long-preferred (above VWAP)
   TICK_LEVEL: -200 (neutral)
   NEWS_BLACKOUT: none
   MAX_LOSS_TODAY: $2,500 trailing (unrealized)
   ```

**Cross-references:**
- `execution/hmm_regime/regime_detector.py`
- `execution/hooks/PreMarket.sh`
- `Alpha_Triage.md` → risk constraints block

**Files to create:**
```
~/.claude/skills/trading-session-start/
  SKILL.md
```

---

## Mapping to Existing `07_AI_Skills_and_Agents/` Docs

| Existing File | Relationship to New Skills |
|---------------|---------------------------|
| `PineScript_Optimization_Expert.md` | Feeds `/pine-v6-converter` — use as reference for current patterns |
| `PineScript_Strategy_Converter_Expert.md` | Feeds `/pine-v6-converter` — existing conversion prompts |
| `NotebookLM_Prompt_Pack.md` | Feeds future NLM query batches — reuse cluster query templates from this audit |
| `Claude_Antigravity_Prompt_Pack.md` | Feeds L2 Playbooks — extract regime-specific prompts |
| `PineScript_Architect_Expert.md` | Feeds new indicator builds (#1–#6 in Alpha_Triage.md) |

---

## Implementation Order

1. `/trading-session-start` — highest daily utility, minimal coding (hook script + SKILL.md)
2. `/volume-regime` — core intelligence layer, needs HMM + TradingView MCP wired
3. `/es-nq-monitor` — real-time (requires TradingView MCP stable + session discipline)
4. `/pine-v6-converter` — forward-looking, build when Pine v6 docs published
