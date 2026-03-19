# Framework Master Index

This file is the navigation guide for the entire Trading System Framework.

Use it to understand:
- what each folder is for
- what each file does
- the recommended order of use
- how the framework moves from research to strategy to validation

---

## 1. Recommended Workflow Order

Follow the framework in this order:

1. Define your identity, goals, and constraints
2. Document your current system and indicators
3. Normalize paid education into structured extracts
4. Normalize external strategies into the same structure
5. Use NotebookLM to compare and summarize
6. Use Claude / Antigravity to synthesize candidate systems
7. Convert candidate systems into Pine-ready rule sets
8. Build, debug, and optimize Pine code
9. Backtest and forward-validate
10. Promote only the most robust version

---

## 2. Root Files

### `README.md`
High-level explanation of the framework and intended workflow.

### `Framework_Master_Index.md`
This file. Master navigation guide for all folders and files.

### `Framework_Working_Principles.md`
Operating principles for the framework.

### `Research_Questions_Master.md`
Master bank of questions to ask across research, systems, risk, and validation.

### `NotebookLM_Prompt_Pack.md`
Prompt pack designed for NotebookLM as the knowledge brain.

### `Claude_Antigravity_Prompt_Pack.md`
Prompt pack designed for Claude Opus / Antigravity as the reasoning and synthesis layer.

### `PineScript_Architect_Expert.md`
Skill file for building, debugging, migrating, and structuring Pine Script.

### `PineScript_Optimization_Expert.md`
Skill file for performance optimization while preserving logic and parity.

### `PineScript_Strategy_Converter_Expert.md`
Skill file for converting discretionary chart ideas into Pine strategy-ready rule sets.

---

## 3. Folder Guide

## `01_Trading_Profile_and_Objectives/`
Purpose:
Define the trader, objectives, constraints, and risk philosophy before any system work begins.

Files:
- `Trading_Profile_Master.md`
- `Finishers_Journal_Trading_Goals.md`
- `Risk_Philosophy.md`

---

## `02_Paid_Courses_Actionable_Extraction/`
Purpose:
Convert paid courses and education into structured, actionable trading rules.

Files:
- `Course_01_Extraction.md`

---

## `03_External_Strategy_Research/`
Purpose:
Collect and rank only the best external strategies after they are normalized.

Files:
- `Ranked_External_Ideas.md`

---

## `04_Current_System_and_Indicators/`
Purpose:
Map the current system and audit the indicators already being used.

Files:
- `System_Extraction_Template.md`
- `Indicator_Inventory.md`
- `Current_System_Map.md`

---

## `05_Synthesis_and_Candidate_Systems/`
Purpose:
Compare alternatives and decide what should become Version 1.

Files:
- `Candidate_System_Scorecard.md`
- `Version_1_Decision.md`

---

## `06_Backtesting_and_Validation/`
Purpose:
Track what happens once ideas become actual tested systems.

Files:
- `Backtest_Results.md`
- `Forward_Test_Notes.md`
- `TradeZella_Findings.md`
- `Change_Log.md`

---

## 4. Minimal Starting Checklist
- [ ] Trading profile
- [ ] Finisher’s Journal goals
- [ ] Risk philosophy
- [ ] Indicator inventory
- [ ] Current system map
- [ ] first paid course extraction
- [ ] first external strategy normalization
- [ ] first NotebookLM summary
- [ ] first Claude synthesis pass
- [ ] first candidate system scorecard


---

## `07_AI_Skills_and_Agents/`
Purpose:
Keep AI role files and prompt packs in one dedicated place.

Files:
- `README.md`
- `PineScript_Architect_Expert.md`
- `PineScript_Optimization_Expert.md`
- `PineScript_Strategy_Converter_Expert.md`
- `NotebookLM_Prompt_Pack.md`
- `Claude_Antigravity_Prompt_Pack.md`
