<!-- provisioner:begin generated -->
---
name: cos-boot
description: Initialize Cognitive OS session. Use at the start of every conversation, when the user says "boot", or when no prior session context is evident. Loads identity, checks pending decisions, calibrates readiness.
---

# Cognitive OS Boot

Bridges the model-agnostic Cognitive OS to Claude Code.

**OS directory:** `.claude/cognitive-os/`
If your OS lives elsewhere, update the paths below.

## Steps

### 1. Load Identity (always — ~200 tokens)
- Read `.claude/cognitive-os/kernel.md` — internalize decision weights (W0-W5)
- These weights guide ALL decisions this session

### 2. Load Memory Index (always — ~100 tokens)
- Read `.claude/cognitive-os/MEMORY.md` — scan for relevant project files
- Based on current working directory, read matching project memory files
- Do NOT read full decisions.md or insight.md yet — load on demand

### 3. Check Pending Decisions (lightweight scan)
- Use Grep to find `Outcome: PENDING` in `.claude/cognitive-os/decisions.md`
- Only read the surrounding context of PENDING entries (not the full file)
- For each: is the outcome now knowable? If yes → ask user for update
- Record outcome, compare to prediction, note calibration
- If 3+ resolved decisions available → check confidence calibration:
  - Over-confident (predicted 80%+, failed) → report pattern
  - Under-confident (<60%, succeeded) → report pattern

### 4. Check Inbox (if exists)
- If `.claude/cognitive-os/inbox.md` exists and has entries beyond the header
- Report: "You have N unprocessed thoughts in inbox. Process now?"
- If user says yes → invoke cos-capture batch mode

### 5. Session Fingerprint
- Append to `.claude/cognitive-os/decisions.md`: `## Session YYYY-MM-DD: [topic in 5 words]`

### 6. Calibrate
- State readiness and any concerns
- If uncertain about the task → say so (W0)

## What Gets Loaded Later (on demand)
- Full `decisions.md` — loaded by `/cos-decide` when recording a decision
- Full `insight.md` — loaded by `/cos-insight` when recording a pattern
- `protocols/boris.md` — loaded by `/cos-boris` when debugging

## Anti-Drift Reminders (active for entire session)

- Every number must have a source, or write `(?)`
- Re-read kernel.md before any message with conclusions or recommendations
- After user correction: state what changed AND what didn't
<!-- provisioner:end generated -->

<!-- provisioner:begin local-overrides -->
<!-- Add project-specific overrides here. -->
<!-- provisioner:end local-overrides -->
