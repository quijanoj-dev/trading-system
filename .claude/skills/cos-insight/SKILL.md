<!-- provisioner:begin generated -->
---
name: cos-insight
description: Record and validate a cross-domain pattern using prediction-error and fractal check. Use when noticing a pattern that connects 2+ contexts, when the user says "insight" or "pattern", or when an unexpected result reveals a reusable principle.
---

# Insight Recording with Fractal Validation

Bridges Cognitive OS insight mechanism to Claude Code.

## When to Trigger

- You notice the same pattern in 2+ different contexts
- An unexpected result reveals something generalizable
- User says "insight", "pattern", "I see a pattern"
- A debugging session reveals a structural issue (not just a bug)

## Steps

1. **State the expectation** — what did you think was true?

2. **State reality** — what actually happened?

3. **Compute delta** — WHY is there a gap? What does it mean?

4. **Ground in evidence** — cite specific incidents, numbers, code references

5. **Run fractal check:**
   - Variable level: does this pattern apply to individual values/names? ✓/✗
   - Module level: does it apply to module/component boundaries? ✓/✗
   - Service level: does it apply to service architecture? ✓/✗
   - Business level: does it apply to business decisions? ✓/✗
   - If 3+ levels: → **META** (principle)
   - If 1-2 levels: → **surface** (tactic)

6. **Determine next insight ID** — read `.claude/cognitive-os/insight.md`, find highest I0XX, increment

7. **Write entry** — append to `.claude/cognitive-os/insight.md`:

```markdown
## I[NNN]: [Pattern name]
- **When:** [date] | **Source project:** [where observed]
- **Expectation:** [what you expected]
- **Reality:** [what happened]
- **Delta:** [the insight]
- **Grounding:** [concrete evidence]
- **Fractal check:** [results per level] → [surface/META]
- **Status:** observation
```

8. **Check for META convergence:**
   - Do 2+ existing insights point to the same root pattern?
   - If yes → write a META insight that synthesizes them
   - META format includes: Pattern, Root cause, Prescription

9. **Check for kernel evolution trigger:**
   - Do 2+ decision outcomes show the same pattern as this insight?
   - If yes → propose kernel principle update to user (do NOT auto-update)
   - Show evidence, get approval, then update kernel.md

## Examples

### Good Insight Record

```markdown
## I017: Binary checks > judgment rules under drift
- **When:** 2026-03-02 | **Source project:** Cognitive OS
- **Expectation:** Judgment rules ("cite the relevant weight") would prevent drift
- **Reality:** When drifting, model skips judgment rules entirely — reasoning already compromised
- **Delta:** Binary checks (verified? yes/no) work under drift because they require honesty, not reasoning
- **Grounding:** 3 sessions where weight citation was skipped; 0 sessions where (?) marker was skipped
- **Fractal check:**
  - Variable: type check (binary) catches bugs that code review (judgment) misses ✓
  - Module: interface contract (binary) > "good API design" (judgment) ✓
  - Service: health check (binary) > monitoring dashboard interpretation (judgment) ✓
  - Business: go/no-go gate (binary) > "market feels right" (judgment) ✓
  → **META** — principle holds at all 4 levels
- **Status:** confirmed (anti-drift mechanism built on this)
```

### Bad Insight Record (avoid)

```markdown
## I099: Testing is important
- **Expectation:** none stated
- **Reality:** tests caught a bug
- **Delta:** testing is good
```
→ **Problems:** No expectation = no prediction-error = no insight. "Testing is important" is received wisdom, not observation. No fractal check. No grounding (which bug? which test? what was surprising?).

## Important

- Insights from PREDICTION-ERROR are more valuable than pattern-matching
- Without explicit expectation, there is no delta
- Without delta, there is no insight
- Record even if uncertain — status: "observation" allows future validation
<!-- provisioner:end generated -->

<!-- provisioner:begin local-overrides -->
<!-- Add project-specific overrides here. -->
<!-- provisioner:end local-overrides -->
