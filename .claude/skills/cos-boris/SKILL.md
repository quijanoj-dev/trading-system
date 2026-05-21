<!-- provisioner:begin generated -->
---
name: cos-boris
description: Structural fact verification protocol. Use when a question has multiple plausible answers, when the user says "boris" or "разберись", when a bug survives the first fix attempt, when comparing complex alternatives, or when any work requires evidence-first thinking. Do NOT use for simple questions with obvious answers.
---

# Boris Protocol — Structural Fact Verification

Read `.claude/cognitive-os/protocols/boris.md` for the full methodology.

## Core Principle

**Every assertion = source. Every action = verification. Every conclusion = evidence chain.**

Boris makes working without facts expensive. It is ONE protocol — debugging, analysis, sprints, audits are all applications of the same principle.

> W4 (Evidence) > W2 (Feedback Speed) when hypothesis space is uncertain.

## The Protocol

### 1. STOP
Do not hypothesize. Do not conclude. Do not answer yet.

### 2. Define the Question
Write it down explicitly. Vague question → vague evidence → vague conclusion.

### 3. Collect ALL Evidence
Before ANY opinion, gather everything relevant. The checklist is context-dependent:
- **Bug:** Console errors, network failures, DOM state, API responses, server logs. Use Playwright MCP for real environment.
- **Architecture:** Code, docs, competitors, benchmarks, prior decisions in `.claude/cognitive-os/decisions.md`.
- **Sprint/plan:** Requirements, dependencies, blockers, velocity data.
- **Audit:** Read all relevant files, check actual state vs documented state.

Every number must have a source. No source → write `(?)`.

### 4. Trace to Root
Start from observation. Trace backwards to where actual ≠ expected.
That divergence point is where the answer lives.

### 5. Multi-Pass Verification (2-3 iterations)
- **Pass 1:** Evidence only — no opinion
- **Pass 2:** Patterns — what's surprising vs expected?
- **Pass 3:** Conclusions — what follows? What remains uncertain?

### 6. Act and Verify
Fix root cause, not symptom. Verify in real environment. Confirm ALL issues resolved.

### 7. Record Finding
Append to `findings-log.jsonl` in this skill directory:
```json
{
  "date": "YYYY-MM-DD",
  "project": "project-name",
  "question": "what we investigated",
  "initial_assumption": "what was assumed first",
  "finding": "what we actually found",
  "action": "what was done",
  "lesson": "pattern to watch for"
}
```

### 8. Check for Insight
- Does this finding match patterns in `.claude/cognitive-os/insight.md`?
- Is this a new pattern? → Write new insight with fractal check
- Could this apply elsewhere? → Search for same pattern

## Examples

### Good Boris Output

**Question:** "Why does the order API fail for region-specific bundles?"

**Pass 1 (Evidence):**
- API logs: POST /v1/orders returns 422 for bundle `region_1gb_7d`
- Supplier docs: this region requires `coverage_type: local` (not `region`)
- DB: bundle record has `coverage_type: region` — seeded incorrectly
- No console errors, no network timeout — pure data issue

**Pass 2 (Pattern):**
- Surprising: coverage_type mismatch only for one region, not others
- Expected: seed script uses API response directly
- Finding: seed script hardcodes `region` for all bundles in this group

**Pass 3 (Conclusion):**
- Root cause: seed script line 47, hardcoded `coverage_type: region` for entire group
- Fix: use `bundle.coverage_type` from API response
- Remaining uncertainty: are other fields also hardcoded? → audit needed

### Bad Boris Output (avoid)

**Question:** "Why does provisioning fail?"

"It might be a network issue. Let me try restarting the server."
→ **Violation:** Hypothesized before collecting evidence (Step 1: STOP). No API logs checked, no error codes cited, jumped to solution.

"The error is probably in the adapter."
→ **Violation:** "Probably" without source. No `(?)` marker. No trace to root.

## Gotchas (accumulated from past investigations)
<!-- This section grows over time as Boris finds patterns -->
<!-- Format: short description — root cause -->
<!-- provisioner:end generated -->

<!-- provisioner:begin local-overrides -->
<!-- Add project-specific overrides here. -->
<!-- provisioner:end local-overrides -->
