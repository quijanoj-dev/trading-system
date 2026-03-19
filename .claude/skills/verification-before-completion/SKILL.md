---
name: verification-before-completion
description: >
  Use before claiming any Pine Script work is complete, any indicator is fixed,
  or any system change is done. Requires verification evidence — not assumptions.
  Evidence before assertions, always.
allowed-tools: Read, Write, Grep, Glob, Bash
---

# Verification Before Completion — Trading System

Claiming a Pine Script indicator works without verification is dishonesty, not efficiency.

**Core principle:** Evidence before claims, always.

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't verified the specific claim, you cannot make it.

## The Gate Function

```
BEFORE claiming any status:

1. IDENTIFY: What evidence proves this claim?
2. CHECK: Verify against the appropriate checklist below
3. DOCUMENT: Record what was verified and what the result was
4. ONLY THEN: Make the claim

Skip any step = unverified claim
```

## Pine Script Verification Checklist

Every Pine Script change must be verified against ALL applicable items:

### Non-Repainting Verification

- [ ] No `request.security()` with `barmerge.lookahead_on`
- [ ] No `barstate.isrealtime` used for signal logic (only for visual optimization)
- [ ] Signal logic gated behind `barstate.isconfirmed` where needed
- [ ] Pivot-based signals use confirmed bars (appropriate right-side bars or close-break)
- [ ] No signal placement at `bar_index` that could shift on unconfirmed bars
- [ ] Historical signals match what would have appeared in real-time

### Signal Timing Verification

- [ ] Signals appear at the expected bar (not too early, not too late)
- [ ] Delay is consistent with the documented timing nature (lagging/coincident/leading)
- [ ] Signal does not fire on every bar (noise check)
- [ ] Cooldown period is working correctly
- [ ] Invalidation logic correctly fades or removes invalid signals

### Resource Usage Verification

- [ ] No TradingView "exceeds maximum" errors
- [ ] `max_lines_count`, `max_boxes_count`, `max_labels_count` are sufficient but not excessive
- [ ] No "script takes too long" warnings
- [ ] `request.security()` calls are minimized

### Visual Verification

- [ ] Labels/lines/boxes render at correct positions
- [ ] Colors match expected bull/bear conventions
- [ ] Text content is correct (signal names, values, tiers)
- [ ] No visual clutter or overlapping elements
- [ ] Works on both ES and NQ charts

### Compatibility Verification

- [ ] Compiles without errors in Pine v6
- [ ] Works alongside existing indicators (no conflicts)
- [ ] Works at 1-minute timeframe
- [ ] Works at session boundaries (market open, close)

## System Change Verification

For non-Pine changes (framework files, system map, inventory):

- [ ] Updated files are internally consistent
- [ ] Cross-references between files are correct
- [ ] No orphaned references to removed content
- [ ] INDICATOR_CHANGELOG.md updated if indicator changed
- [ ] Change_Log.md updated if system rule changed
- [ ] Git commit includes all modified files

## Common Failures

| Claim | Requires | NOT Sufficient |
|-------|----------|----------------|
| "Indicator is non-repainting" | Full repaint checklist above | "I didn't use lookahead" |
| "Signal timing is correct" | Chart verification on ES 1-min | "The logic looks right" |
| "No resource issues" | Applied to chart without errors | "I kept object counts low" |
| "Works on both ES and NQ" | Tested on both charts | "It uses auto-detect" |
| "Fix doesn't break other signals" | Checked other signals still appear | "I only changed one thing" |
| "Inventory entry is accurate" | Re-read Pine code and compared | "I wrote it based on the code" |

## Red Flags — STOP

- Using "should", "probably", "seems to", "looks like it works"
- Expressing satisfaction before verification ("Done!", "Fixed!", "Working!")
- About to commit without checking the verification list
- Trusting that "small change = safe change"
- Assuming compatibility because "it compiled"
- Claiming non-repainting without checking the full checklist

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "It compiled, so it works" | Compilation ≠ correct behavior |
| "Small change, no need to verify" | Small changes cause repaint. Verify. |
| "Same logic as the other variant" | Verify independently. ~80% same ≠ 100% same. |
| "I checked the code, looks right" | Code review ≠ runtime verification |
| "It worked before this change" | Verify it still works after this change |

## The Bottom Line

**No shortcuts for verification.**

Check the list. Confirm each item. THEN claim the result.

This is non-negotiable.
