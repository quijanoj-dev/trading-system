# Framework Master Index

Navigation guide for the Trading System Framework. System: **ICT-SMC PO3-AMD, Silver Bullet V1.**

---

## Decision Framework (6 Gates)

Every trade must pass all six gates in order. If any gate fails → NO TRADE.

| Gate | Question | Primary Docs |
|------|----------|-------------|
| 1 — CONTEXT | Am I allowed to trade today? | `Daily_Ritual.md` |
| 2 — HTF BIAS | Is the market offering a narrative? | `Trading_Profile_Master.md`, `Indicator_Inventory.md` |
| 3 — PO3 STRUCTURE | Is the algorithm active? | `Current_System_Map.md` |
| 4 — LTF ENTRY | Is this a textbook A+ execution? | `Current_System_Map.md`, `Indicator_Inventory.md` |
| 5 — RISK | Is this mathematically worth it? | `Current_System_Map.md` |
| 6 — EXECUTION | Can I manage this trade cleanly? | `Current_System_Map.md` |

---

## Root Files

| File | Purpose |
|------|---------|
| `README.md` | System overview, stack, repo structure |
| `Framework_Master_Index.md` | This file — navigation guide |
| `Framework_Working_Principles.md` | Decision guardrails, system rules |
| `Daily_Ritual.md` | Pre/post session routines |
| `13_Week_Roadmap.md` | 13-week execution plan (migration → backtest → Apex) |

---

## Folder Guide

### `01_Trading_Profile_and_Objectives/`
Define the trader, objectives, constraints, and risk philosophy.

| File | Purpose |
|------|---------|
| `Trading_Profile_Master.md` | Trader identity, markets, platform stack, core objectives |
| `Finishers_Journal_Trading_Goals.md` | 90-day SMART goals and key motivations |
| `Risk_Philosophy.md` | Risk rules, position sizing, loss limits |

---

### `02_Paid_Courses_Actionable_Extraction/`
Convert paid courses and education into structured, actionable rules.
Supplementary only — does not override DOCX framework.

| File | Purpose |
|------|---------|
| `Course_01_Extraction.md` | Extracted rules from primary ICT-SMC course |

---

### `03_External_Strategy_Research/`
Collect and rank only the best external strategies after normalization.

| File | Purpose |
|------|---------|
| `Ranked_External_Ideas.md` | Ranked external strategy candidates |

---

### `04_Current_System_and_Indicators/`
Active system map and indicator inventory.

| File | Purpose |
|------|---------|
| `Current_System_Map.md` | **Primary decision doc** — 6-gate A+ framework with indicator-to-gate mapping |
| `Indicator_Inventory.md` | Indicator descriptions, gate assignments, consolidation notes |
| `System_Extraction_Template.md` | Template for documenting new systems |

---

### `05_Synthesis_and_Candidate_Systems/`
Version selection and rationale.

| File | Purpose |
|------|---------|
| `Version_1_Decision.md` | Why Silver Bullet V1 was chosen (Candidate 2), rejection rationale |
| `Candidate_System_Scorecard.md` | All 4 candidates scored against criteria |

---

### `06_Backtesting_and_Validation/`
Track what happens once ideas become tested systems.

| File | Purpose |
|------|---------|
| `Backtest_Results.md` | Backtest outcomes, signal counts, metrics |
| `Forward_Test_Notes.md` | Live forward test observations |
| `TradeZella_Findings.md` | Journal stats and behavioral patterns |
| `Change_Log.md` | What changed, why, and what happened |

---

### `07_AI_Skills_and_Agents/`
AI role files and prompt packs.

| File | Purpose |
|------|---------|
| `PineScript_Architect_Expert.md` | Pine Script architecture prompts |
| `PineScript_Optimization_Expert.md` | Optimization prompts |
| `PineScript_Strategy_Converter_Expert.md` | Strategy conversion prompts |
| `NotebookLM_Prompt_Pack.md` | NotebookLM research prompts |
| `Claude_Antigravity_Prompt_Pack.md` | Claude synthesis prompts |

---

### `08_TradingView_Indicators/`
Active Pine Script v6 indicators.

| Indicator | Gate | Purpose |
|-----------|------|---------|
| `Market Session Lines.pine` | Gate 1 | Session time markers |
| `Premarket Levels.pine` | Gates 2, 5 | Multi-TF OHLC reference levels + TP targets |
| `OTE-OR-HTF-PO3.pine` | Gates 2, 3, 4 | OTE Fibonacci + Opening Range + HTF PO3 visualization |
| `SMC-FVG-ICT-DOB-SH.pine` | Gates 3, 4 | BOS/CHoCH + FVG + OB + Stop Hunt |
| `SMT-CD Divergence.pine` | Gates 3, 4 | SMT inter-market divergence (confirmed variant — primary) |

---

## Quick Reference

**Executing a trade:**
1. Run all 6 gates top-to-bottom.
2. All 6 pass → execute. Any fail → journal only.

**Starting a session:**
→ `Daily_Ritual.md` morning routine (30 min pre-market)

**Weekly review:**
→ `TradeZella_Findings.md` + `Change_Log.md`
