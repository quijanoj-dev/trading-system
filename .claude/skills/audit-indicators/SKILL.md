---
name: audit-indicators
description: >
  Audit the indicator suite for overlap, gaps, and redundancy. Trigger when the user says
  "audit indicators", "check indicator overlap", "indicator review", or "which indicators
  should I keep".
allowed-tools: Read, Glob, Grep, Bash, Agent
---

# Indicator Audit Skill

Analyze the full indicator suite for overlap, redundancy, gaps, and optimization opportunities.

## Process

1. **Read current state:**
   - `04_Current_System_and_Indicators/Indicator_Inventory.md`
   - `04_Current_System_and_Indicators/Current_System_Map.md`
   - All `.pine` files in `08_TradingView_Indicators/` (read headers + key logic sections)

2. **Overlap analysis:**
   - Identify indicators measuring the same market data
   - Compare the 4 SMT-CDDO variants: which modes are actually used?
   - Check OR module (OTE-OR-HTF-PO3) vs Premarket Levels overlap
   - Count total TradingView indicator slots consumed

3. **Gap analysis:**
   - Map each decision flow step to supporting indicators
   - Identify steps with no indicator support
   - Identify signal types missing from the suite (e.g., volume profile, momentum oscillator)

4. **Recommendations:**
   - Which indicators to keep, review, or remove
   - Whether the 4 SMT variants should be consolidated into one
   - Whether any indicator is too resource-heavy for TradingView limits
   - Specific suggestions for reducing chart clutter

## Output Format

Produce a structured audit report with: Overlap Matrix, Gap Analysis, Consolidation Recommendations, and Priority Actions.
