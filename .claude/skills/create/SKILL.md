---
name: create
description: >
  Create new skills or agents for the trading system. Trigger when the user says
  "make a skill", "create an agent", "turn this into a skill", "automate this",
  "save this workflow", or "I keep doing this".
allowed-tools: Read, Write, Grep, Glob, Bash
---

# Skill & Agent Creator — Trading System

Create reusable skills and agents for the Trading System Framework.
The core job is making the right orchestration decisions: type, placement,
tools, model, scope, then writing a clean artifact that fits the project.

## Phase 1: Understand Context

1. Read `CLAUDE.md` for project identity, architecture, and conventions
2. Scan existing skills: `Glob .claude/skills/*/SKILL.md`
3. Check if a similar skill already exists — prefer enhancing over duplicating

## Phase 2: Skill or Agent?

Count how many agent signals are present. If 2+ match, create an agent.
If 0-1 match, create a skill.

Agent signals:
- Needs to run autonomously in the background
- Requires its own isolated context
- Would benefit from a specific model selection (haiku for speed, opus for reasoning)
- Needs to spawn further sub-agents

## Phase 3: Design Decisions

**Placement:** Always `.claude/skills/` (project-specific) unless explicitly cross-project.

**Structure:** Create as `skill-name/SKILL.md` folder pattern. Add reference files in the same folder if the skill needs them (templates, examples, prompts).

**Tools:** Apply least-privilege — only include tools the skill actually needs.

**Trading context to inject:**
- Read the trader profile (`01_Trading_Profile_and_Objectives/Trading_Profile_Master.md`)
- Reference the indicator inventory if the skill touches Pine Script or signals
- Reference the System Extraction Template if the skill processes strategies or courses
- Point to `Framework_Working_Principles.md` for decision-making guardrails

## Phase 4: Write the Skill

Include frontmatter:
```yaml
---
name: skill-name
description: >
  What it does. Trigger phrases the user would say.
argument-hint: <optional hint for arguments>
allowed-tools: Tool1, Tool2
---
```

Body structure:
1. Context reading phase (which project files to read first)
2. Core work phases
3. Quality standards specific to the trading system
4. Output format

## Naming Convention

Trading-specific skills use descriptive kebab-case: `extract-course`, `pine-architect`, `audit-indicators`.
General-purpose skills keep short names: `research`, `swarm`, `create`.

## After Creation

- Verify the skill appears in the skill list
- Test it with a simple invocation if possible
- Consider whether `/log-change` should record this addition
