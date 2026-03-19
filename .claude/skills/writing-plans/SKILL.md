---
name: writing-plans
description: >
  Write detailed implementation plans for trading system work — Pine Script indicators,
  system changes, strategy development. Use when you have a design or spec for a
  multi-step task, before touching code.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Agent
---

# Writing Plans — Trading System

Write comprehensive, bite-sized implementation plans for trading system work.
Assume the implementer needs full context — which files to touch, exact Pine Script
patterns, how to verify, and how to test.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Save plans to:** `docs/plans/YYYY-MM-DD-<feature-name>.md`

## Phase 1: Load Context

Read before planning:
- `CLAUDE.md` — architecture and current state
- `04_Current_System_and_Indicators/Indicator_Inventory.md` — existing indicator details
- `Framework_Working_Principles.md` — decision guardrails
- The approved design/spec from brainstorming

## Phase 2: Scope Check

If the design covers multiple independent components (e.g., "build new indicator + modify
existing indicator + update system map"), create separate plans — one per component.
Each plan should produce a working, testable deliverable on its own.

## Phase 3: File Structure

Map out which files will be created or modified:

**For Pine Script work:**
- `08_TradingView_Indicators/[Indicator Name].pine` — the indicator file
- `04_Current_System_and_Indicators/Indicator_Inventory.md` — inventory entry
- `04_Current_System_and_Indicators/Current_System_Map.md` — decision flow update
- `08_TradingView_Indicators/INDICATOR_CHANGELOG.md` — change record

**For system changes:**
- The specific framework files being modified
- `06_Backtesting_and_Validation/Change_Log.md` — change record

## Phase 4: Task Granularity

Each step is one action (2-10 minutes for Pine Script work):

**Pine Script indicator development:**
```
- [ ] Step 1: Write indicator header (indicator(), inputs, constants)
- [ ] Step 2: Implement core calculation logic
- [ ] Step 3: Implement signal detection
- [ ] Step 4: Implement visualization (plots, labels, lines, boxes)
- [ ] Step 5: Add alertcondition() calls
- [ ] Step 6: Verify non-repainting behavior
- [ ] Step 7: Test on chart with historical data
- [ ] Step 8: Test on live data (forward bars)
- [ ] Step 9: Update indicator inventory entry
- [ ] Step 10: Update system map if decision flow changes
- [ ] Step 11: Record change in changelog
- [ ] Step 12: Commit
```

**Pine Script modification:**
```
- [ ] Step 1: Read current code and identify change points
- [ ] Step 2: Document current behavior (before screenshot/description)
- [ ] Step 3: Implement the change
- [ ] Step 4: Verify change doesn't introduce repaint
- [ ] Step 5: Verify change doesn't break existing signals
- [ ] Step 6: Test on chart
- [ ] Step 7: Update inventory entry if behavior changed
- [ ] Step 8: Record change in changelog
- [ ] Step 9: Commit
```

## Plan Document Header

Every plan MUST start with:

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development (recommended)
> or superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [One sentence]

**Architecture:** [2-3 sentences about approach]

**Platform:** Pine Script v6 / TradingView

**Indicators affected:** [List which indicators are created/modified]

---
```

## Task Structure

````markdown
### Task N: [Component Name]

**Files:**
- Create: `08_TradingView_Indicators/New Indicator.pine`
- Modify: `04_Current_System_and_Indicators/Indicator_Inventory.md`
- Update: `08_TradingView_Indicators/INDICATOR_CHANGELOG.md`

- [ ] **Step 1: Write indicator header**

```pine
//@version=6
indicator("Indicator Name", overlay=true, max_lines_count=100)

// === INPUTS ===
enableModule = input.bool(true, "Enable Module")
lookback    = input.int(14, "Lookback Period", minval=1)
```

- [ ] **Step 2: Implement core logic**

```pine
// === CORE CALCULATION ===
// [exact code here]
```

- [ ] **Step 3: Verify non-repainting**

Check:
- No `request.security()` with `barmerge.lookahead_on`
- No `barstate.isrealtime` without `barstate.isconfirmed` gate
- No referencing `close` on current bar without confirmation
- Pivots use appropriate right-side bars or `barstate.isconfirmed`

- [ ] **Step 4: Test on TradingView chart**

Apply to ES 1-min chart. Verify:
- Signals appear at expected locations
- Historical signals match expected behavior
- No excessive resource usage warnings
- Labels/lines/boxes render correctly

- [ ] **Step 5: Update inventory and changelog**

- [ ] **Step 6: Commit**

```bash
git add "08_TradingView_Indicators/New Indicator.pine"
git add "04_Current_System_and_Indicators/Indicator_Inventory.md"
git add "08_TradingView_Indicators/INDICATOR_CHANGELOG.md"
git commit -m "feat: add New Indicator for [purpose]"
```
````

## Pine Script Verification Checklist

Every plan involving Pine Script MUST include these verification steps:

- [ ] Non-repainting: no lookahead, confirmed bars only
- [ ] Delay assessment: how many bars before signal appears?
- [ ] Resource check: object counts within TradingView limits
- [ ] Chart test: visual verification on ES/NQ 1-minute chart
- [ ] Edge cases: market open, session boundaries, low-volume periods
- [ ] Compatibility: works alongside existing 8 indicators

## Quality Standards

- Exact file paths always
- Complete Pine Script code in plan (not "add signal logic")
- Exact verification steps with expected outcomes
- Follow Pine v6 conventions
- Enforce non-repainting by default
- Reference Framework Working Principles where relevant
- DRY, YAGNI, frequent commits

## Execution Handoff

After saving the plan, offer:

**1. Subagent-Driven (recommended)** — fresh subagent per task, review between tasks

**2. Inline Execution** — execute tasks in this session with checkpoints
