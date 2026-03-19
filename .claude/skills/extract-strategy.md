---
name: extract-strategy
description: >
  Extract and normalize an external trading strategy. Trigger when the user says
  "extract strategy", "add external strategy", "normalize strategy", or provides
  a strategy from YouTube, articles, or TradingView.
allowed-tools: Read, Write, Glob, Grep, Bash, Agent
---

# External Strategy Extraction Skill

Normalize external strategies (YouTube, articles, TradingView scripts) into the standardized template format and add to the ranked ideas list.

## Process

1. **Read context files:**
   - `04_Current_System_and_Indicators/System_Extraction_Template.md`
   - `01_Trading_Profile_and_Objectives/Trading_Profile_Master.md`
   - `03_External_Strategy_Research/Ranked_External_Ideas.md`

2. **Scan existing strategies:**
   - Glob `03_External_Strategy_Research/Strategy_*.md` for next number

3. **Process the strategy material:**
   - Extract actionable rules only
   - Classify as mechanical / semi-mechanical / discretionary
   - Assess fit for ES/NQ 1-minute intraday
   - Rate: rule clarity, automation feasibility, evidence quality
   - Flag vague concepts and marketing hype

4. **Write individual strategy file:**
   - Save to `03_External_Strategy_Research/Strategy_NN_[Name].md`
   - Full 22-section template format

5. **Append to Ranked_External_Ideas.md:**
   - Add a row with: strategy name, source, market, timeframe, ES/NQ fit, rule clarity, automation feasibility, evidence quality, verdict

## Quality Standards

- Only include strategies that fit ES/NQ and have enough rule clarity to be testable
- Do not collect random hype — only ideas worth comparing against the current system
- Every entry needs a clear verdict
