---
name: log-change
description: >
  Record a system change in the Change Log. Trigger when the user says
  "log change", "record change", "update changelog", or after completing
  a significant system modification.
allowed-tools: Read, Write, Bash
---

# Change Log Skill

Append a structured entry to the Change Log and optionally create a git commit.

## Process

1. **Read the change log:**
   - `06_Backtesting_and_Validation/Change_Log.md`

2. **Gather information** from the user or from the just-completed work:
   - What changed
   - Why it changed
   - What system version it applies to
   - What effect is expected
   - What actually happened (if known)

3. **Append entry** using this format:

```
### YYYY-MM-DD — [System Version]

**Change:** [What was changed]
**Reason:** [Why it was changed]
**Expected Effect:** [What improvement is expected]
**Result:** [What actually happened — fill in after testing, or mark as "pending"]
```

4. **Create git commit** with the change description as the commit message

## Rules

- Use today's date (absolute, not relative)
- Be specific about what changed — "adjusted SMT filter" is better than "tweaked indicator"
- Always include the reason — changes without reasons violate Principle #8
- Mark Result as "pending" if not yet tested
