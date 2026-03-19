---
name: sync-notebooklm
description: >
  Upload or update framework documents to NotebookLM. Trigger when the user says
  "sync notebook", "update notebooklm", "push to notebook", or "upload to notebooklm".
allowed-tools: Read, Glob, Bash, mcp__notebooklm__notebook_list, mcp__notebooklm__notebook_get, mcp__notebooklm__source_add, mcp__notebooklm__source_delete, mcp__notebooklm__source_get_content
---

# NotebookLM Sync Skill

Upload or update key framework documents as sources in the Trading System NotebookLM notebook.

## Target Notebook

- Name: "Trading System - NotebookLM"
- ID: `ef97cc40-896f-4d2d-b7b8-6dea75274e69`

## Process

1. **Check current notebook state:**
   - Use `mcp__notebooklm__notebook_get` to see existing sources

2. **Determine what needs uploading:**
   - Compare existing sources against priority file list below
   - Identify new or updated files that should be synced

3. **Upload priority files** (in order):
   - `01_Trading_Profile_and_Objectives/Trading_Profile_Master.md`
   - `01_Trading_Profile_and_Objectives/Risk_Philosophy.md`
   - `01_Trading_Profile_and_Objectives/Finishers_Journal_Trading_Goals.md`
   - `04_Current_System_and_Indicators/Current_System_Map.md`
   - `04_Current_System_and_Indicators/Indicator_Inventory.md`
   - `Framework_Working_Principles.md`
   - `Research_Questions_Master.md`

4. **Upload completed extractions** (if any exist):
   - Glob `02_Paid_Courses_Actionable_Extraction/Course_*.md` (skip README)
   - Glob `03_External_Strategy_Research/Strategy_*.md`

5. **Use `source_add` with `source_type=text`:**
   - Read each file's content
   - Upload as text source with the filename as title

6. **Report** what was uploaded and the total source count

## Notes

- NotebookLM works best with prose and structured documents, not raw code
- Do NOT upload .pine files directly — the Indicator Inventory describes them better
- Maximum ~50 sources per notebook — be selective
