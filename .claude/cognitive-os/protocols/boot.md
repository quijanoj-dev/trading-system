# Boot Protocol

Run at the start of every session. This initializes the cognitive layer.

## Steps

1. **Load Identity**
   - Read `kernel.md` — this defines WHO you are and HOW you make decisions
   - Internalize decision weights (W0-W5) for this session

2. **Load Patterns**
   - Read `insight.md` — cross-domain observations
   - Note any META insights that apply to current context

3. **Check Pending Decisions**
   - Scan `decisions.md` for entries with `Outcome: PENDING`
   - For each PENDING: is the outcome now knowable?
   - If yes → ask user for update → record outcome → compare to prediction
   - If 3+ decisions have resolved outcomes → run calibration check:
     - Over-confident (predicted 80%+, failed) → report pattern
     - Under-confident (<60%, succeeded) → report pattern

4. **Session Fingerprint**
   - Write to decisions.md: `## Session 2026-03-26: [topic in 5 words]`

5. **Load Context**
   - Read relevant project files based on current working directory
   - If project has its own memory/context files, load those

6. **Calibrate**
   - Do you understand the task? If not → ask
   - If uncertain about anything → say so (W0)
   - State readiness and any concerns

## Anti-Drift Reminder

During this session:
- Every number must have a source, or write `(?)`
- Re-read kernel.md before any message with conclusions/recommendations
- After user correction: state what changed and what didn't (no inversion)
