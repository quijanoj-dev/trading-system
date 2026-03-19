---
name: systematic-debugging
description: >
  Use when encountering any Pine Script bug, indicator malfunction, signal error,
  repaint issue, or unexpected behavior — before proposing fixes. Find the root
  cause first.
allowed-tools: Read, Write, Grep, Glob, Bash, Agent
---

# Systematic Debugging — Trading System

Random Pine Script fixes waste time, introduce repaint risk, and create new signal errors.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY trading system issue:
- Pine Script compilation errors
- Indicator signals appearing at wrong locations
- Signals that repaint (appear/disappear on historical bars)
- Excessive delay in signal generation
- TradingView resource limit errors (max_lines, max_boxes, etc.)
- Indicator not showing expected behavior
- Divergence between historical and real-time signals
- Performance degradation
- Conflicts between indicators

## The Four Phases

Complete each phase before proceeding to the next.

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read Error Messages Carefully**
   - Pine Script compiler errors contain exact line numbers and descriptions
   - Runtime errors appear in TradingView's Pine Script console
   - Don't skip warnings — they often indicate repaint risk

2. **Identify the Symptom Category**

   | Symptom | Likely Root Cause Area |
   |---------|----------------------|
   | Signal appears/disappears on historical bars | Repaint: `lookahead_on`, unfenced `barstate.isrealtime`, `close` on current bar |
   | Signal appears too late | Excessive right-side pivot bars, lagging confirmation |
   | Signal at wrong price level | Wrong source data, HTF data alignment issue |
   | Too many signals (noise) | Missing filters, cooldown too short, pivot range too small |
   | Too few signals | Filters too aggressive, pivot range too large, condition too restrictive |
   | Resource limit exceeded | Too many objects (lines/boxes/labels), unbounded loops, excessive `request.security()` |
   | Conflict with other indicator | Shared symbol names, overlapping visual elements |

3. **Check Recent Changes**
   - `git diff` — what changed since last working version?
   - Was an input default changed?
   - Was a `request.security()` call modified?
   - Was a bar confirmation gate removed?

4. **Trace the Signal Logic**

   For Pine Script debugging, trace backward from the visual output:

   ```
   Visual output (label/line/box)
     ← What condition triggers it?
       ← What variables does that condition depend on?
         ← Where are those variables calculated?
           ← What data feeds those calculations?
             ← Is the data from request.security()? What are the barmerge settings?
   ```

5. **Check the Repaint Chain**

   If repaint is suspected, verify each link:
   ```
   request.security() → barmerge.lookahead_off? ✓/✗
   Pivot detection → requires right-side bars? How many?
   Signal gating → barstate.isconfirmed? ✓/✗
   Signal placement → bar_index or bar_index[N]?
   Invalidation → can a signal be removed after placement?
   ```

### Phase 2: Pattern Analysis

1. **Find Working Behavior**
   - Does the indicator work correctly on some bars but not others?
   - Does it work on one symbol but not another?
   - Does it work on one timeframe but not another?
   - Compare working vs broken instances

2. **Compare Against Inventory**
   - Read the indicator's entry in `04_Current_System_and_Indicators/Indicator_Inventory.md`
   - Does the observed behavior match the documented behavior?
   - Check documented repaint risk, delay risk, and known weaknesses

3. **Check Sibling Indicators**
   - The 4 SMT-CDDO variants share ~80% code
   - If one variant works and another doesn't, diff the specific divergent section
   - Don't assume "same logic" — verify line by line

### Phase 3: Hypothesis and Testing

1. **Form Single Hypothesis**
   - "I think X is causing the repaint because Y"
   - Be specific: which line, which variable, which condition

2. **Test Minimally**
   - Change ONE thing at a time in the Pine Script
   - Add `plotchar()` or `label.new()` debug markers to visualize intermediate values
   - Use `bgcolor()` to highlight bars where conditions are true
   - Compare before/after on the same chart region

3. **Verify Before Continuing**
   - Did the fix work? → Phase 4
   - Didn't work? → New hypothesis, don't stack fixes

4. **If 3+ Fixes Failed**
   - STOP. Question whether the approach is fundamentally sound
   - Is this indicator trying to do too much?
   - Should this be split into smaller components?
   - Discuss with the user before attempting more fixes

### Phase 4: Implementation

1. **Document Current Behavior**
   - What the indicator does now (before the fix)
   - Screenshot or description of the problematic output

2. **Implement Single Fix**
   - ONE change at a time
   - No "while I'm here" improvements
   - Preserve non-repainting behavior

3. **Verify Fix**
   - Does the signal appear at the correct bar?
   - Does it persist on historical bars (no repaint)?
   - Are other signals unaffected?
   - Does it work on both ES and NQ?
   - Resource usage within TradingView limits?

4. **Update Documentation**
   - Update inventory entry if behavior changed
   - Record the change in INDICATOR_CHANGELOG.md
   - Use `/log-change` skill

## Red Flags — STOP and Return to Phase 1

- "Quick fix: just change this one setting"
- "Just add another filter to reduce noise"
- "Switch to lookahead_on to fix the delay" (NEVER — this introduces repaint)
- "It probably works, I'll check later"
- "The other SMT variant handles this differently, let me copy that"
- Making multiple changes before testing any of them
- Proposing fixes without reading the actual code first

## Pine Script Debug Toolkit

Useful debug techniques for Phase 3:

```pine
// Visualize a boolean condition
bgcolor(myCondition ? color.new(color.green, 90) : na)

// Debug a value on chart
plotchar(myValue, "Debug Value", "", location.top)

// Mark specific bars
if myCondition
    label.new(bar_index, high, str.tostring(myVariable), size=size.tiny)

// Check if code path is reached
var int hitCount = 0
if myCondition
    hitCount += 1
plot(hitCount, "Hit Count")
```

## Common Pine Script Root Causes

| Bug Pattern | Common Root Cause |
|-------------|------------------|
| Signals disappear on scroll back | `barstate.islast` or `barstate.isrealtime` without history mode |
| Signal moves to different bar | `request.security()` with `lookahead_on` |
| Signal appears 1 bar early | Using `close` instead of `close[1]` for confirmed data |
| "Max objects exceeded" | Unbounded object creation without cleanup/deletion |
| Different results on replay vs live | `timenow` or `barstate.isrealtime` dependencies |
| Signal fires every bar | Missing pivot confirmation or cooldown |
