---
name: swarm
description: >
  Decompose a complex trading analysis or development task into parallel subagents.
  Invoke when: "create agents for this", "spin up a swarm", "parallel agents",
  "swarm this", "break this into subagents", or when a task has 3+ independent
  workstreams that can run simultaneously.
argument-hint: <endstate or full task description>
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Agent
---

# Swarm — Trading System

Decompose complex trading system tasks into parallel subagents, design each agent,
create all agent files, and deliver a ready-to-execute orchestration plan.

## Phase 1: Context Capture

1. Read `CLAUDE.md` for project architecture and current state
2. Scan existing skills: `Glob .claude/skills/*/SKILL.md`
3. Parse the user's requested endstate
4. Identify what project files are relevant

## Phase 2: Workstream Decomposition

Identify parallel workstreams. Each produces one independent deliverable.
Target 2-6 agents. Common trading system decompositions:

**Strategy analysis swarm:**

- Agent per strategy source (each extracts and normalizes independently)
- Merge agent compares and ranks results

**Indicator audit swarm:**

- Agent per indicator (reads Pine script, produces inventory entry)
- Analysis agent identifies overlaps and gaps across all entries

**Pine development swarm:**

- Research agent (finds patterns, references, existing solutions)
- Architect agent (designs the code structure)
- Builder agent (writes the Pine Script)
- Validator agent (checks for repaint, delay, resource usage)

**System synthesis swarm:**

- Agent per candidate system (scores against scorecard independently)
- Comparison agent ranks candidates and recommends V1

Map wave structure before writing files — agents in the same wave run in parallel,
later waves depend on earlier wave outputs.

## Phase 3: Agent Specification

For each workstream define:

- **Name:** descriptive kebab-case
- **Model:** haiku (fast search/extraction), sonnet (balanced analysis), opus (complex reasoning/synthesis)
- **Tools:** least-privilege — only what the agent needs
- **Output:** what file or data the agent produces
- **Context:** which project files the agent should read first

## Phase 4: Create Agent Files

Write each agent prompt with:

- **Mission:** one sentence, what this agent delivers
- **Context files:** specific paths to read
- **Protocol:** setup → core work → verification → output
- **Quality standards:** trading-system-specific (non-repainting, evidence-based, fit for ES/NQ 1-min)

## Phase 5: Orchestration Plan

Output the wave map with exact Agent tool invocations:

```markdown
## Wave 1 (parallel)
- Agent A: [description] → produces [output]
- Agent B: [description] → produces [output]

## Wave 2 (depends on Wave 1)
- Agent C: [description] → reads Wave 1 outputs → produces [final deliverable]
```

## Rules

- Never create more than 6 agents — complexity kills value
- Every agent must produce a concrete artifact (file, report, code)
- Include a merge/synthesis agent if Wave 1 has 3+ parallel agents
- Apply Framework Working Principle #3: prefer simplicity over complexity
- If the task can be done well with 2 agents, don't use 4
