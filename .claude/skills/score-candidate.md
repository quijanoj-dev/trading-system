---
name: score-candidate
description: >
  Score a candidate trading system against the evaluation criteria. Trigger when the user says
  "score system", "evaluate candidate", "scorecard", or "compare systems".
allowed-tools: Read, Write, Glob, Grep
---

# Candidate System Scoring Skill

Evaluate a candidate trading system against the standardized scorecard dimensions.

## Process

1. **Read context files:**
   - `05_Synthesis_and_Candidate_Systems/Candidate_System_Scorecard.md` (scoring template)
   - `01_Trading_Profile_and_Objectives/Trading_Profile_Master.md`
   - `01_Trading_Profile_and_Objectives/Risk_Philosophy.md`
   - `04_Current_System_and_Indicators/Indicator_Inventory.md`

2. **Identify the candidate** from user input or from an extraction file

3. **Score across all dimensions:**
   - System type classification
   - Market regime fit
   - ES/NQ fit
   - 1-minute timeframe fit
   - Rule clarity (mechanical vs discretionary)
   - Automation feasibility
   - Backtest readiness
   - Complexity
   - Indicator load
   - Redundancy risk
   - Evidence quality
   - Prop firm compatibility (Apex constraints)
   - Daily drawdown risk
   - Expected trade frequency

4. **Write scored entry** to `05_Synthesis_and_Candidate_Systems/Candidate_System_Scorecard.md`

5. **Compare** against any previously scored candidates if they exist

## Quality Standards

- Every score must include a justification
- Flag assumptions explicitly
- Rate evidence quality honestly — "interesting" is not "proven"
- Highlight what data is missing to make a better assessment
