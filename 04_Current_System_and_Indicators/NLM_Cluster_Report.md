# NotebookLM Source Cluster Report
**Notebook:** Trading System | NotebookLM (239 sources)
**Generated:** 2026-05-25 via 4-pass NLM multi-query synthesis

---

## Thematic Clusters

| # | Cluster | Est. Sources | Core Topics |
|---|---------|-------------|-------------|
| A | Volume & Order Flow | ~30 | CVD divergence, Bookmap absorption, footprint charts, delta traps, tick imbalance |
| B | PineScript Development | ~25 | SMT-CDDO indicator suite, zero-lag patterns, ATR models, CDDO+KVO engine |
| C | ES/NQ Execution Logic | ~40 | Day trading setups, scalping, session timing, APEX prop firm rules |
| D | Options & Derivatives | ~45 | Call/put spreads, IV crush, straddle mechanics, covered calls |
| E | AI Trading Automation | ~20 | Claude+TradingView MCP bridge, 5-layer agent stack, webhook automation |
| F | Platform & Tools | ~30 | ThinkorSwim scanners, Bookmap/Rithmic setup, APEX Trader, Benzinga, FINVIZ |
| G | System Docs + Cleanup | ~29 | 4 markdown files (Inventory, System Map, Templates) + ~25 duplicates |

**Total accounted:** 219 (20 unclustered — Spanish-language content, misc tutorials)

---

## Duplicate Sources (~25 — candidates for deletion)

| Title | Copies |
|-------|--------|
| "How I Would Start Over As A Beginner Trader" | 3x |
| "Cheap Option Trading Strategies" | 2x |
| "Supply & Demand Trading Guide" | 2x |
| "Claude + TradingView" | 2x |
| Google Antigravity variants | 3-4x |
| Other misc duplicates | ~12 |

**Action:** Confirm with user before deleting. Use `mcp__notebooklm__source_delete` per ID.

---

## Source-to-Pine File Cross-Reference

| Cluster A/B Source | Existing Pine File |
|--------------------|-------------------|
| SMT-CDDO indicator docs | `08_TradingView_Indicators/SMT-CDDO-NoLagGPT.pine` |
| CVD divergence strategy | `08_TradingView_Indicators/mmt/CVD_Divergence.pine` |
| SMT-CD Divergence v5 source | `08_TradingView_Indicators/SMT-CD Divergence.pine` |
| Real-time CDDO variant docs | `08_TradingView_Indicators/SMT-CDDO-RT.pine` |
| Indicator inventory markdown | `04_Current_System_and_Indicators/Indicator_Inventory.md` |

---

## Key Cluster A Findings — Volume & Order Flow

### Footprint Chart Logic
- **Delta Trap:** +1000 positive delta candle that fails to push higher → trapped buyers confirmed
- **Exhaustion Print:** <9 contracts at top-ask (red candle) or bottom-bid (green candle)
- **Thin Print:** Zero imbalance in the middle body = aggressive sweep cleared the level
- **Entry Rule:** Wait for back-to-back confirmation candles (never trade single-candle setup)
- **Stop:** 4–5.5 pts above/below trapping candle
- **Target:** Nearest untested thin print; else 1:1 to 1:2 RR (5–6.5 pts)

### Bookmap Absorption ("Effort vs. Reward")
- Look for large green volume dots hitting thick orange/red liquidity wall with no price follow-through
- **Short entry (reversal):** Stop 1–3 pts above wall; target next $5/$10 liquidity increment
- **Long entry (push-through):** Price absorbs wall, breaks $0.50–$1.00, pullback to retest → stop 30¢–$1.50 below, target next $5/$10 level
- Always take profit *just in front of* major liquidity — never hold into it

### $ADD + $TICK Divergence (ES/NQ macro)
- **$ADD divergence:** ES makes new low but $ADD doesn't → sellers exhausted → counter-trend long
- **$TICK exhaustion thresholds:** ±600 (moderate vol day), ±1000 (high vol VIX day)
- Signal sequence: $ADD divergence → wait for TICK extreme → enter on pullback to Market Profile key level

### SMT-CDDO (Algorithmic)
- Engine: 60% Cumulative Delta + 40% Klinger Volume Oscillator → Z-score
- Divergence trigger: price makes HH/LL but CDDO fails to follow
- Required filters: ATR swing ≥0.3x (RT variant) or ≥0.5x (NoLagGPT), wick reject ratio 0.10, 8-bar cooldown per direction
- Zero-lag entry: CloseBreak — fires on close beyond rolling N-bar extreme (no wait for right pivot bars)

---

## Key Cluster B Findings — PineScript Development

### No v6 Content in Sources
Sources reference Pine Script v5 max. v5→v6 migration not documented here.

### Zero-Lag Patterns (v5)
1. **CloseBreak:** `close > ta.highest(high, N)[1]` → fires on current bar close, no lookback lag
2. **Left-only pivot:** `ta.pivothigh(high, N, 0)` gated behind `barstate.isconfirmed`

### ATR Math Models
- **ATR Vstop:** length=22, multiplier=3.0 → filters wick hunts on stop-losses
- **ATR swing gate:** require price swing ≥ 0.3x–0.5x ATR before any divergence signal
- **Measured move:** signal valid if directional push ≥35% of ATR(10–13 bars)
- **ATR bands:** multiplier=3 for trailing stop visualization

### Volume-Weighted Models
- CDDO+KVO Z-score (60/40 blend) — see Cluster A above
- VWMA(150) → profit factor 1.41 in backtests (vs EMA/SMA equivalents)
- Volume Z-score as secondary gate on zero-lag pivots (disabled by default, needs tuning)

### Code Architecture Patterns
- **Signal cooldown maps:** 8–10 bars per direction (bull/bear separate maps) — prevents chop
- **Long-only optimization:** In bull market, strip `strategy.entry("short")`, replace with `strategy.close("long")` on bearish signal → ~2x profit factor improvement in tested cases
- **Multi-symbol confluence:** Grade signal strength by how many correlated symbols (ES/NQ/YM/RTY) confirm the same pivot

---

## Key Cluster E Findings — AI Automation

### 5-Layer Agent Stack (from sources)
| Layer | File/Component | Purpose |
|-------|----------------|---------|
| L1 Memory | `CLAUDE.md`, `Risk.md` | Always-loaded rules: max drawdown, position limits, session behavior |
| L2 Knowledge | `breakout.md`, `pullback.md`, `mean-reversion.md` | On-demand playbooks per regime |
| L3 Guardrails | `PreMarket.sh`, `PostTrade.sh`, `EndOfDay.sh` | Deterministic hooks — no AI hallucination risk |
| L4 Delegation | `market-researcher`, `risk-manager` subagents | Isolated context windows, return single clean answer |
| L5 Distribution | `plugin.json` | Bundle + deploy to any machine |

### TradingView → Execution Pipeline
- Alpha Insider webhook: Strategy ID + Stock ID + leverage in JSON alert → Alpha Insider auto-trade bot → broker (Hyperliquid, Blofin, Alpaca)
- Alternative: Claude Co-work endpoint — Claude generates webhook URL, TradingView POSTs JSON → Claude executes trade via exchange API
- **MCP bridge:** Claude reads TradingView DOM live (exact candle values, indicators, drawings) — not screenshots

### Signal Memory Storage (cross-session)
- **Graphify/Obsidian:** Knowledge graph of strategy docs → 70x token reduction vs full file reads
- **PostgreSQL:** Store last 200 candles per timeframe (15m/1h/4h/D); Monte Carlo simulation on top
- **trades.log:** PostTrade.sh hook writes instrument, direction, entry, stop, size, fill time, setup type
- **journal-analyzer subagent:** Queries trades.log for recurring mistakes + best setup types

### Rithmic + Bookmap Setup (critical config)
- **Rithmic:** Disable "Enable Aggregated Quotes" on login screen — else order flow data is fragmented/inaccurate
- **Bookmap:** Use Instrument Copy for multi-timeframe views on separate monitors; TraderMap Pro filters orders ≥10 contracts (removes retail noise, shows institutional MBO)

---

## Key Cluster C Findings — ES/NQ Execution

### APEX Trader Funding Constraints
- $50k account: $2,500 trailing threshold (on **unrealized** P&L — drawdown locks permanently)
- Funded account threshold hit at $52,600 → trailing stops trailing
- Close all positions by **5:00 PM EST**, no overnight
- **No news trading on funded accounts** (CPI, FOMC = payout denied)
- 30% consistency rule: no single day outsized vs baseline
- Eval: minimum 7 trading days; Funded payout: minimum 10 trading days

### High-Probability Session Windows
| Window | Time (EST) | Setup Type |
|--------|-----------|-----------|
| London/German overlap | 2:00–3:00 AM | Liquidity sweep + reversal |
| Pre-market macro | 8:20–8:40 AM | Opening range setup |
| NY Open macro | 9:20–9:40 AM | Highest probability — news-driven momentum |

---

## Source Quality Assessment

| Cluster | Signal Quality | Actionability |
|---------|---------------|--------------|
| A — Volume/Order Flow | HIGH — specific thresholds, entry logic | Immediate — Pine + Python |
| B — PineScript | HIGH — existing indicators documented | Immediate — code refinements |
| E — AI Automation | HIGH — architectural patterns | Near-term — Project-OS skills |
| C — ES/NQ Execution | MEDIUM — setup logic solid, prop rules important | Immediate — CLAUDE.md rules |
| D — Options | LOW (for futures focus) | Archive |
| F — Platform Tools | MEDIUM | Reference only |
| G — Docs + Cleanup | Admin | Prune duplicates |
