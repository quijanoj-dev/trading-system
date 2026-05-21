# Boris Protocol — Exhaustive Analysis

Named after Boris Cherny's engineering philosophy: exhaustive analysis > incremental guessing.

## When to Use

Boris is NOT just for debugging. Use it for ANY situation requiring evidence-first thinking:

**Debugging:** Bug survives the first fix attempt, root cause unclear, multiple hypotheses equally plausible.

**Deep analysis:** Comparing complex alternatives, evaluating architecture, auditing code quality, researching a question with non-obvious answers.

**Decision support:** When a choice needs grounding in evidence (not intuition), when the user says "boris", "разберись", "debug this systematically".

**Self-audit:** Verifying your own output for errors, checking assumptions, catching drift.

## Why This Exists

Evidence (I020): 3 incremental debugging attempts at admin panel fix, each targeting
wrong root cause (RSC → router.push → cookies). Boris protocol found actual root cause
(missing `jobs` field in API response) in ONE pass. Cost of 3 guesses > cost of 1 exhaustive analysis.

This principle extends beyond debugging: 3 quick opinions on architecture < 1 exhaustive analysis of trade-offs.

**Principle:** W4 (Evidence) > W2 (Feedback Speed) when hypothesis space is uncertain.

## Steps — Bug Investigation

### 1. STOP Hypothesizing
Do not guess. Do not "try this and see." Collect evidence first.

### 2. Reproduce in Real Environment
- Open the actual URL/app/API in a real browser or client
- Not curl, not mock, not "I think it does X" — REAL environment
- Capture the exact state the user sees

### 3. Collect ALL Signals (before analyzing any)
- Console errors (exact text, not summary)
- Network requests (status codes, response bodies, timing)
- DOM state (missing elements, wrong attributes, wrong data)
- API responses (actual shape vs expected shape)
- Logs (server-side, if accessible)
- Environment (which deployment, which branch, which config)

### 4. Trace Data Flow
Start from the symptom and trace backwards:
- Which component/function produces the error?
- What data does it receive?
- Where does that data come from?
- At which point does actual data diverge from expected?
- The divergence point = root cause location

### 5. Verify Root Cause
Before fixing, confirm:
- Can you explain WHY this causes the symptom?
- Does this explain ALL symptoms, not just one?
- If you're not sure → collect more signals (go to step 3)

### 6. Fix and Verify
- Fix the root cause (not the symptom)
- Verify in real environment (not just tests)
- Check that all symptoms are resolved

## Steps — Deep Analysis

### 1. STOP Concluding
Do not answer immediately. Collect evidence first.

### 2. Define the Question
What exactly are we trying to understand? Write it down explicitly.

### 3. Collect ALL Relevant Sources
- Read all relevant code/files (not just the obvious ones)
- Check documentation, READMEs, changelogs
- Search for prior art (templates, examples, competitors)
- Look at actual data/metrics if available
- Check web sources if needed

### 4. Multi-Pass Analysis
Run 2-3 iterations:
- **Pass 1:** What does the evidence say? (no opinion yet)
- **Pass 2:** What patterns emerge? What's surprising vs expected?
- **Pass 3:** What conclusions follow? What's still uncertain?

### 5. Ground Conclusions
Every claim must cite specific evidence. No source → write `(?)`.

## Common Closing Steps (both modes)

### 7. Record Finding
Write to findings log:
```json
{
  "date": "2026-03-26",
  "mode": "bug|analysis",
  "question": "what we investigated",
  "initial_assumption": "what was assumed first",
  "finding": "what we actually found",
  "action": "what was done",
  "lesson": "what pattern to watch for"
}
```

### 8. Check for Pattern
- Does this finding match any known patterns?
- Could this apply elsewhere in the codebase or other projects?
- If pattern found → write to insight.md with fractal check

## Anti-Patterns
- Jumping to conclusions before collecting evidence
- Changing multiple things at once (can't isolate cause)
- Testing in a different environment than where bug occurs
- Assuming the answer is in the layer you're most familiar with
- "It works on my machine" without checking actual deployment
- Retrying the same approach hoping for different results
- Stating opinions as facts without grounding
