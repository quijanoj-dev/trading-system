---
name: extract-course
description: >
  Extract actionable trading rules from a paid course. Trigger when the user says
  "extract course", "normalize course", "process course", or provides course material
  to be structured.
allowed-tools: Read, Write, Glob, Grep, Bash, Agent
---

# Course Extraction Skill

Extract only actionable trading content from paid courses into the standardized System Extraction Template format.

## Process

1. **Read context files:**
   - `04_Current_System_and_Indicators/System_Extraction_Template.md` (the 22-section template)
   - `01_Trading_Profile_and_Objectives/Trading_Profile_Master.md` (for fit assessment)
   - `01_Trading_Profile_and_Objectives/Risk_Philosophy.md`

2. **Scan for existing extractions:**
   - Glob `02_Paid_Courses_Actionable_Extraction/Course_*.md` to determine the next number

3. **Process the course material** the user provides (pasted text, file path, or summary):
   - Extract ONLY actionable rules: setups, entries, exits, stops, invalidation, session filters
   - Ignore storytelling, mindset advice, motivational content, theory unless it directly changes execution
   - Classify each concept as mechanical, semi-mechanical, or discretionary
   - Flag vague or ambiguous rules explicitly
   - Rate fit for ES/NQ 1-minute scalping

4. **Write the extraction file:**
   - Save to `02_Paid_Courses_Actionable_Extraction/Course_NN_[CourseName].md`
   - Use the full 22-section template format
   - Set status fields: Source uploaded: yes, Extraction complete: yes

5. **Update Course Index** if `02_Paid_Courses_Actionable_Extraction/Course_Index.md` exists

## Quality Standards

- Every setup must have: name, preconditions, entry, stop, exit, session filter
- Flag any claim without evidence as "unverified"
- Note repaint/delay/hindsight risks explicitly
- Rate evidence quality as Strong / Medium / Weak
- Provide a Final Verdict: Test now / Save for later / Reject / Needs clarification
