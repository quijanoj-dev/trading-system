# Alpha Triage — ES/NQ Trading System
**Source:** 239-source NLM audit, 4-pass synthesis (2026-05-25)
**Focus:** Volume Divergence + PineScript + Infrastructure

---

## ALPHA BOOSTERS — Implement in Pine Script Now

### 1. Add Exhaustion Print + Thin Print Layer to CVD_Divergence.pine
**Source cluster:** A (Footprint)
**What:** Overlay exhaustion print signals (<9 contracts at candle extremes) and thin print zones onto existing CVD_Divergence indicator as confirmation labels.
**Logic:**
- On 1m ES/NQ: flag candle when `volume_at_ask[high] < 9` (exhaustion, red candle top)
- Flag thin print: zero imbalance in candle body middle
- Show label only when CVD divergence is also active → high-conviction convergence
**Files:** `08_TradingView_Indicators/mmt/CVD_Divergence.pine` — add plot layer
**Effort:** Medium (2–3h Pine coding)

### 2. Upgrade CDDO Engine: Volume Z-Score Gate
**Source cluster:** B (SMT-CDDO docs)
**What:** Volume Z-score filter is currently disabled by default in SMT-CDDO-RT.pine. Enable and tune it.
**Logic:** Only fire CDDO divergence signal when volume Z-score exceeds threshold (start at 0.5, tune per backtest). Eliminates false positives on low-volume chop.
**Files:** `08_TradingView_Indicators/SMT-CDDO-RT.pine`
**Effort:** Low (1h — parameter change + backtest)

### 3. Long-Only Mode Toggle for Bull Regime
**Source cluster:** B (strategy optimization)
**What:** Add `longOnly` input bool to strategy variants. When enabled: strip `strategy.entry("short")`, replace with `strategy.close("long")`.
**Why:** Backtested improvement from 1.19 → ~2.0+ profit factor by eliminating short drag in trending markets. HMM regime can gate this toggle.
**Files:** SMT-CDDO strategy variants + new `regime_gate.pine` bridge
**Effort:** Low–Medium (2h)

### 4. ATR Vstop Integration (length=22, mult=3.0)
**Source cluster:** B
**What:** Add ATR Vstop as dynamic stop-loss visualizer on ES/NQ 1m/5m charts.
**Logic:** Hard-coded settings (22, 3.0) shown to filter wick hunts. Plot as trailing stop line, use for exit signal when price closes below (long) or above (short).
**Files:** New `execution/indicators/atr_vstop.pine` or add to MMT_Companion.pine
**Effort:** Low (1h)

### 5. $ADD + $TICK Divergence Panel
**Source cluster:** A (market internals)
**What:** Add $ADD (NYSE Advance-Decline) and $TICK panel to ES chart. Flag divergence automatically.
**Logic:**
- Import `USIDC:ADD` and `USI:TICK.US` via `request.security()`
- Divergence: ES makes new low but $ADD higher low → bullish divergence label
- $TICK threshold lines at ±600 and ±1000
**Files:** New `08_TradingView_Indicators/Market_Internals.pine`
**Effort:** Medium (3–4h)

### 6. Multi-Symbol SMT Minimum Confirmations = 2
**Source cluster:** B (SMT-CDDO NoLagGPT docs)
**What:** Set `min_symbol_confirmations = 2` (currently likely 1) in SMT-CDDO-NoLagGPT.pine. Signal fires only when ≥2 of ES/NQ/YM/RTY confirm same pivot direction.
**Files:** `08_TradingView_Indicators/SMT-CDDO-NoLagGPT.pine`
**Effort:** Low (30m — input parameter change)

---

## INFRASTRUCTURE ENHANCERS — Python Execution Layer

### 7. Rithmic Connector Stub
**Source cluster:** E + F
**What:** Create `execution/market_data/rithmic.py` with interface matching `execution/market_data/interfaces.py`.
**Critical config:** Must set `aggregated_quotes=False` in login handshake — else tick data is fragmented.
**Effort:** High (depends on Rithmic API docs + account access)
**Blocker:** Rithmic account + R|Protocol library required

### 8. PostgreSQL Candle Store
**Source cluster:** E (5-layer stack)
**What:** Store last 200 bars per timeframe (1m/5m/15m/1h/4h/D) for ES + NQ → Postgres. Enables Monte Carlo on top, strategy regime detection without re-fetching.
**Schema:** `(symbol, timeframe, timestamp, open, high, low, close, volume)` + index on `(symbol, timeframe, timestamp DESC)`
**Files:** `execution/market_data/candle_store.py`
**Effort:** Medium (4–6h)

### 9. HMM Regime → Pine Script Bridge (Alert)
**Source cluster:** E + existing HMM module
**What:** Python script queries `RegimeDetector` (already built), sends regime to TradingView via webhook → Pine indicator reads regime from external input or alert note.
**Flow:** `cron.py` runs every 15m → `RegimeDetector.predict(ohlcv)` → POST to TV webhook → alert label shows current regime on chart
**Files:** `execution/hmm_regime/regime_broadcaster.py`
**Effort:** Medium (3–4h)

### 10. PreMarket.sh + PostTrade.sh Hooks
**Source cluster:** E (5-layer agent stack)
**What:** Shell hooks for daily trading session management.
**PreMarket.sh:** Fetches overnight high/low, sets session bias from HMM regime, writes to `context/session.md`
**PostTrade.sh:** Logs fill to `trades.log` (instrument, direction, entry, stop, size, setup type, timestamp)
**Files:** `execution/hooks/PreMarket.sh`, `execution/hooks/PostTrade.sh`
**Effort:** Low–Medium (2–3h)

---

## LONG-TERM RESEARCH — Archive in Developer-Vault

| Item | Cluster | Why Archived |
|------|---------|--------------|
| Options strategies (IV crush, straddles, spreads) | D | Off-focus for futures system |
| ThinkorSwim scanners + custom scripts | F | Different platform; reference if adding equities |
| FINVIZ scanning patterns | F | Stock screener; not ES/NQ relevant |
| Polarity ATI machine learning indicator | F | Black-box; no source code access |
| Monte Carlo simulation framework (Python) | E | Backlog after candle store built (#8) |
| Spanish-language content | misc | May contain unique ICT/SMC concepts; review separately |

**Archive target:** `~/Developer-Vault/01-projects/Trading-System/research/`

---

## Implementation Priority

```
Week 1:  #6 (30m) → #2 (1h) → #4 (1h) → #3 (2h)     [Pine, no infra needed]
Week 2:  #5 (4h) → #1 (3h)                              [Pine, adds internals layer]  
Week 3:  #10 (3h) → #9 (4h)                             [Python hooks + HMM bridge]
Week 4:  #8 (6h) → #7 (blocked on Rithmic account)      [Infra / data layer]
```

---

## Risk Constraints (APEX Trader — bake into Risk.md)

```
MAX_TRAIL_DRAWDOWN_UNREALIZED: $2,500
CLOSE_BY: 17:00 EST (hard rule)
NO_OVERNIGHT: true
NEWS_BLACKOUT_FUNDED: [CPI, FOMC, NFP, PPI]
CONSISTENCY_RULE: no single day > 30% of total account gain
EVAL_MIN_DAYS: 7
FUNDED_PAYOUT_MIN_DAYS: 10
```
