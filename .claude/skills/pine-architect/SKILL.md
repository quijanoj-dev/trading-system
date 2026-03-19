---
name: pine-architect
description: >
  Build, debug, or migrate Pine Script indicators. Trigger when the user says
  "build indicator", "fix pine", "debug pine", "migrate pine", "write pinescript",
  or "pine script".
allowed-tools: Read, Write, Glob, Grep, Bash
---

# Pine Script Architect Skill

Senior Pine Script v6 architect for building, debugging, migrating, and structuring indicators.

## Before Coding

1. **Read the role definition:**
   - `07_AI_Skills_and_Agents/PineScript_Architect_Expert.md`

2. **Read project context:**
   - `04_Current_System_and_Indicators/Indicator_Inventory.md` (understand the current suite)
   - If modifying an existing indicator, read the full `.pine` file from `08_TradingView_Indicators/`

3. **Understand the request** — what indicator to build/fix/modify and why

## Response Structure

Follow the 4-step structure from the Architect Expert role:

1. **Technical Analysis** — what the code does or should do, what is broken/missing
2. **Implementation Plan** — specific changes, in order
3. **Code** — complete Pine Script v6 code
4. **Notes** — repaint risk, performance considerations, known limitations

## Mandatory Rules

- Pine Script v6 only (`//@version=6`)
- Non-repainting logic preferred — document any intentional repainting
- All `request.security()` calls must use `barmerge.lookahead_off` unless explicitly justified
- Clean modular structure — group related logic, use meaningful variable names
- Preserve existing behavior when fixing bugs — do not change unrelated logic
- Save new/modified indicators to `08_TradingView_Indicators/`

## After Coding

- Describe the change for `06_Backtesting_and_Validation/Change_Log.md`
- Note any impact on the Indicator Inventory
