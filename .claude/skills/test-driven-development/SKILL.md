---
name: test-driven-development
description: >
  Use when implementing any Pine Script indicator feature or modification.
  Adapted for Pine Script: define expected behavior first, then implement,
  then verify on chart. Specification-Driven Development for trading indicators.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
---

# Specification-Driven Development — Pine Script

Pine Script has no unit test framework. But the discipline of "define expected behavior
before writing code" is MORE important in trading — where unverified signals cost money.

**Core principle:** If you didn't define what the signal should look like before coding it,
you don't know if the code produces the right signal.

## The Iron Law

```
NO PINE SCRIPT IMPLEMENTATION WITHOUT A SPECIFICATION FIRST
```

Write the expected behavior spec before coding. If you wrote code first, stop and
define what it SHOULD do before proceeding.

## When to Use

**Always:**
- New indicators or modules
- New signal types or detection modes
- Bug fixes (define what correct behavior looks like)
- Filter additions or modifications
- Refactoring that could affect signal timing

**Exceptions (ask the user):**
- Pure visual/cosmetic changes (colors, styles, label formatting)
- Input parameter additions that don't change logic

## The Spec-Implement-Verify Cycle

```
SPEC → IMPLEMENT → VERIFY → REFINE
```

### SPEC — Define Expected Behavior

Before writing any Pine Script, document:

```markdown
## Signal Specification

**Signal name:** [e.g., "Bearish SMT Divergence — Micro Range"]

**Trigger condition (plain English):**
[e.g., "Chart symbol makes a higher high while comparison symbol makes a lower high,
within the micro pivot range (2-10 bars), with at least 1 right-side confirmation bar"]

**Expected visual output:**
- [e.g., "Red label below the higher-high bar showing 'SMT ★' with comparison symbol name"]
- [e.g., "Red dashed line connecting the chart's higher-high to the comparison's lower-high"]

**Expected timing:**
- [e.g., "Signal appears 1 bar after the right-side confirmation bar closes"]
- [e.g., "On bar N, if bar N-1 is the confirmed pivot and bar N confirms it"]

**Non-repainting requirement:**
- [e.g., "Signal must not appear on bar N and then disappear when bar N+1 forms"]
- [e.g., "Once a signal is placed, it stays permanently"]

**Invalidation behavior:**
- [e.g., "If price breaks above the higher-high pivot within 20 bars, the signal
  label color fades to grey but the label remains"]

**Edge cases:**
- What happens at market open (first bars of session)?
- What happens at session boundaries?
- What if no comparison symbol data is available?
- What if multiple signals fire on the same bar?

**Filter requirements:**
- [e.g., "Must pass volume gate (volume > 50% of 20-bar MA)"]
- [e.g., "Must be outside cooldown period (8 bars since last signal)"]
```

### IMPLEMENT — Write Minimal Code

Write the simplest Pine Script that satisfies the spec. Nothing more.

**Good:**
```pine
// Detect bearish SMT divergence - micro range
smtBearish = chartHigherHigh and compLowerHigh and rightBarsConfirmed
if smtBearish and passesFilters
    label.new(bar_index - rightBars, high, "SMT ★", color=color.red)
```

**Bad:**
```pine
// Over-engineered: adding configurable colors, multiple display modes,
// optional trailing lines, and gradient backgrounds before the basic
// signal even works
```

### VERIFY — Check Against Spec

Verification is done ON CHART, not in code review:

1. **Apply indicator to ES 1-minute chart**
2. **Find a signal instance and check each spec item:**

   | Spec Item | How to Verify |
   |-----------|---------------|
   | Trigger condition | Manually check: did the condition actually exist at that bar? |
   | Visual output | Does the label/line appear as specified? |
   | Timing | Count bars: does signal appear at the expected offset? |
   | Non-repainting | Scroll back and forward — does the signal persist? |
   | Invalidation | Find an invalidated case — does it fade correctly? |
   | Edge cases | Check market open, session boundary, missing data |
   | Filters | Find a bar where condition exists but filter blocks — is it correctly suppressed? |

3. **Use debug helpers to verify internal state:**

   ```pine
   // Temporarily add to verify intermediate values
   bgcolor(triggerCondition ? color.new(color.yellow, 90) : na)
   plotchar(filterValue, "Filter", "", location.top)
   ```

4. **Check both positive and negative cases:**
   - Positive: signal appears where it should
   - Negative: signal does NOT appear where it shouldn't
   - Both are equally important

### REFINE — Clean Up

After verification passes:
- Remove debug helpers (`bgcolor`, `plotchar`, temporary labels)
- Clean up code structure
- Verify signals still appear correctly after cleanup
- Update the indicator inventory entry

## Strategy Tester as "Unit Test"

For signals that can be converted to strategy entries, use Pine Script's strategy
tester as an automated verification tool:

```pine
//@version=6
strategy("Signal Verification", overlay=true)

// [Paste the signal logic]

if longSignal
    strategy.entry("Long", strategy.long)
if shortSignal
    strategy.entry("Short", strategy.short)

// Strategy tester will show:
// - Total signals generated
// - Win rate
// - Whether signals cluster (overtrading)
// - Whether signals align with expected market behavior
```

This doesn't replace chart verification, but it provides quantitative evidence
about signal frequency and basic viability.

## Red Flags — STOP

- Writing Pine Script before defining expected behavior
- "I'll figure out what it should do while coding"
- "The logic is obvious, no spec needed"
- Defining the spec AFTER seeing what the code produces (that's rationalization)
- Skipping edge case specification
- "It compiles, so it works"
- Declaring completion without chart verification

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Pine Script can't have tests" | It can have specifications and chart verification |
| "I'll know it when I see it" | Define "it" first. Vague expectations produce vague signals. |
| "Small change, no spec needed" | Small changes cause repaint. Define expected behavior. |
| "The existing code is the spec" | Then define what should CHANGE and what should STAY THE SAME |
| "Strategy tester is enough" | Strategy tester shows stats, not correctness. Chart-verify. |

## Quick Reference

| Phase | Trading System Activity | Evidence Required |
|-------|------------------------|-------------------|
| **SPEC** | Define signal behavior in plain English | Written specification |
| **IMPLEMENT** | Write minimal Pine Script | Code that targets the spec |
| **VERIFY** | Check on ES/NQ 1-min chart | Each spec item confirmed |
| **REFINE** | Clean up, update docs | Signals survive cleanup |

## Integration with Other Skills

- **After spec:** Use `/pine-architect` for implementation
- **During verify:** Use `/verification-before-completion` for the full checklist
- **If bugs found:** Use `/systematic-debugging` to find root cause
- **After completion:** Use `/log-change` to record what was built
