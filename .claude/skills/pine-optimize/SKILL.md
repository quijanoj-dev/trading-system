---
name: pine-optimize
description: >
  Optimize Pine Script indicator performance. Trigger when the user says
  "optimize indicator", "speed up pine", "pine performance", or "reduce pine overhead".
allowed-tools: Read, Write, Glob, Grep, Bash
---

# Pine Script Optimization Skill

Performance specialist for Pine Script v6 — speed and efficiency without logic change.

## Before Optimizing

1. **Read the role definition:**
   - `07_AI_Skills_and_Agents/PineScript_Optimization_Expert.md`

2. **Read the target script** from `08_TradingView_Indicators/`

3. **Read the indicator's inventory entry** from `04_Current_System_and_Indicators/Indicator_Inventory.md`

## Response Structure

Follow the 5-step structure from the Optimization Expert role:

1. **Audit** — identify hotspots (loops, object creation, redundant calculations, request.security calls)
2. **Optimized Script** — complete optimized code
3. **Optimization Log** — what changed and why, line by line
4. **Efficiency Estimate** — expected improvement in computation/objects
5. **Validation Notes** — how to verify output parity

## Mandatory Rules

- Preserve logic parity — output must be identical unless explicitly changed
- Preserve non-repainting behavior
- Reduce `max_lines_count`, `max_boxes_count`, `max_labels_count` only if safe
- Minimize `request.security()` calls (combine where possible)
- Replace loops with built-in functions where available
- Do NOT change signal timing or visual appearance without explicit approval
