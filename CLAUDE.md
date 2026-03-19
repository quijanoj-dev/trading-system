# Trading System Framework

## Project Identity

ES/NQ intraday scalper building one robust, automatable 1-minute trading system.

- **Markets:** E-mini S&P 500 (ES), Nasdaq (NQ) futures
- **Execution:** 1-minute chart
- **Platform Stack:** TradingView (charting) → NinjaTrader (execution) → TradeZella (journal) → Apex Trader Funding (prop firm)
- **Goal:** Pass funding evals consistently, reduce discretion, build toward automation

## Architecture

```
01_Trading_Profile_and_Objectives/   ✅ COMPLETE - identity, goals, risk philosophy
02_Paid_Courses_Actionable_Extraction/ ⬜ EMPTY - waiting for first course
03_External_Strategy_Research/         ⬜ EMPTY - waiting for research
04_Current_System_and_Indicators/      🔶 70% - inventory done, system map sections 4-10 need user input
05_Synthesis_and_Candidate_Systems/    ⬜ EMPTY - waiting for synthesis phase
06_Backtesting_and_Validation/         ⬜ EMPTY - waiting for testing phase
07_AI_Skills_and_Agents/               ✅ COMPLETE - 3 Pine roles + 2 prompt packs
08_TradingView_Indicators/             ✅ 8 active Pine indicators + legacy archive
```

## Active Pine Indicators (folder 08)

| Indicator | Purpose |
| --- | --- |
| Market Session Lines | Vertical lines at Market Open / Noon / Power Hour / Close |
| Premarket Levels | Premarket + previous day/week/month OHLC reference levels |
| OTE-OR-HTF-PO3 | Fibonacci OTE zones + Opening Range + HTF Power of 3 candles |
| SMC-FVG-ICT-DOB-SH | BOS/CHoCH + FVG + Displacement Order Blocks + Stop Hunt |
| SMT-CD Divergence | Multi-symbol SMT divergence + Cumulative Delta, 3 pivot tiers |
| SMT-CDDO-Lag | Classic symmetric pivot divergence (confirmed but delayed) |
| SMT-CDDO-NoLagGPT | Zero-lag CloseBreak divergence + EMA/slope/ATR filters |
| SMT-CDDO-RT | Real-time divergence variant, zero right-side delay |

## AI Skills (folder 07)

- **PineScript Architect Expert** — build, debug, migrate Pine v6 code
- **PineScript Optimization Expert** — speed/efficiency without logic change
- **PineScript Strategy Converter Expert** — convert discretionary ideas → testable rules
- **NotebookLM Prompt Pack** — 5 prompts for knowledge extraction and ranking
- **Claude Antigravity Prompt Pack** — synthesis, candidate design, Pine-ready rules

## Conventions

- **Pine Script:** v6 only, non-repainting logic preferred
- **System extractions:** Use `04_Current_System_and_Indicators/System_Extraction_Template.md` format
- **Indicator inventory entries:** Use `04_Current_System_and_Indicators/Indicator_Inventory.md` template format
- **Change tracking:** Record all system changes in `06_Backtesting_and_Validation/Change_Log.md`
- **Working principles:** See `Framework_Working_Principles.md` (14 core rules — plan before building, research before optimization, simplicity over complexity)

## Workflow Pipeline

1. Define identity/goals/constraints → **DONE**
2. Document current system and indicators → **IN PROGRESS**
3. Normalize paid courses → extraction template
4. Normalize external strategies → same template
5. NotebookLM: compare and summarize
6. Claude: synthesize candidate systems
7. Convert candidates → Pine-ready rule sets
8. Build, debug, optimize Pine code
9. Backtest and forward-validate
10. Promote only the most robust version

## Claude Code Skills (.claude/skills/)

### Trading Workflow Skills (8)

| Skill | Purpose |
| --- | --- |
| `/extract-course` | Process paid courses into structured rules |
| `/extract-strategy` | Normalize external strategies |
| `/audit-indicators` | Indicator overlap and gap analysis |
| `/score-candidate` | Evaluate candidate systems against scorecard |
| `/pine-architect` | Build/debug/migrate Pine Script v6 |
| `/pine-optimize` | Optimize Pine performance |
| `/sync-notebooklm` | Upload docs to NotebookLM |
| `/log-change` | Record system changes + git commit |

### Meta-Capability Skills (4)

| Skill | Purpose |
| --- | --- |
| `/create` | Create new skills or agents for this project |
| `/research` | Deep research grounded in trader profile |
| `/swarm` | Decompose complex tasks into parallel subagents |
| `/system-design` | Design trading pipelines and automation architecture |

### Superpowers — Adapted Discipline Skills (5)

Project-level overrides of the global superpowers plugin, adapted for Pine Script and trading:

| Skill | Purpose |
| --- | --- |
| `/brainstorming` | Design before implementation — explore intent, assess fit, propose approaches |
| `/writing-plans` | Detailed bite-sized implementation plans for Pine Script work |
| `/test-driven-development` | Spec-Driven Development for Pine Script (spec → implement → verify on chart) |
| `/systematic-debugging` | Root cause investigation for Pine Script bugs, repaint, signal errors |
| `/verification-before-completion` | Non-repainting checklist, signal timing, resource usage verification |

### Superpowers — Used As-Is from Global Plugin (9)

These work without trading-specific adaptation:

- `superpowers:dispatching-parallel-agents` — parallelize independent tasks
- `superpowers:subagent-driven-development` — fresh subagent per task + review
- `superpowers:executing-plans` — execute plans in separate sessions
- `superpowers:finishing-a-development-branch` — merge/PR completed work
- `superpowers:using-git-worktrees` — isolated workspaces
- `superpowers:requesting-code-review` — dispatch code reviewer
- `superpowers:receiving-code-review` — evaluate feedback technically
- `superpowers:writing-skills` — create new skills with TDD discipline
- `superpowers:using-superpowers` — skill invocation rules

### Workflow Chains

**Building a new indicator:**

`/brainstorming` → `/writing-plans` → `/test-driven-development` → `/pine-architect` → `/verification-before-completion` → `/log-change`

**Debugging an indicator:**
`/systematic-debugging` → `/test-driven-development` (define correct behavior) → fix → `/verification-before-completion` → `/log-change`

**Processing new knowledge:**
`/extract-course` or `/extract-strategy` → `/sync-notebooklm` → `/score-candidate`

**Designing system changes:**
`/brainstorming` → `/system-design` → `/writing-plans` → implement → `/verification-before-completion`

## NotebookLM Integration

MCP server configured. Notebook: "Trading System - NotebookLM" (id: `ef97cc40-896f-4d2d-b7b8-6dea75274e69`).
7 foundation sources loaded. Use `/sync-notebooklm` skill to upload/update sources.
