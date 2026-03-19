---
name: brainstorming
description: >
  You MUST use this before any creative work — designing strategies, building
  indicators, modifying trading logic, or adding system components. Explores
  intent, requirements, and design before implementation.
allowed-tools: Read, Write, Grep, Glob, Bash, Agent, WebSearch, WebFetch
---

# Brainstorming — Trading System

Turn trading ideas into fully formed designs and specs through collaborative dialogue.
Understand the trader's intent, assess fit for the system, and design before building.

<HARD-GATE>
Do NOT write any Pine Script, modify any indicator, change any system rule, or take any
implementation action until you have presented a design and the user has approved it.
This applies to EVERY change regardless of perceived simplicity.
</HARD-GATE>

## Anti-Pattern: "This Is Too Simple To Need A Design"

A "simple" indicator tweak or filter addition can introduce repaint risk, break signal
timing, or conflict with existing logic. The design can be short (a few sentences for
truly simple changes), but you MUST present it and get approval.

## Checklist

Complete in order:

1. **Load project context** — read CLAUDE.md, indicator inventory, system map, working principles
2. **Ask clarifying questions** — one at a time, understand purpose/constraints/success criteria
3. **Assess fit** — does this fit ES/NQ 1-min scalping? Does it conflict with existing indicators?
4. **Propose 2-3 approaches** — with trade-offs and your recommendation
5. **Present design** — scaled to complexity, get user approval after each section
6. **Write design doc** — save to `05_Synthesis_and_Candidate_Systems/` or a spec file
7. **User reviews design** — ask user to review before proceeding
8. **Transition** — invoke writing-plans skill to create implementation plan

## Phase 1: Load Context

Before asking any questions, read:
- `CLAUDE.md` — project identity, architecture, current state
- `04_Current_System_and_Indicators/Indicator_Inventory.md` — what already exists
- `04_Current_System_and_Indicators/Current_System_Map.md` — how indicators connect
- `Framework_Working_Principles.md` — decision guardrails

## Phase 2: Understand the Idea

Ask questions one at a time. Focus on:

**For strategy/setup ideas:**
- What market condition does this target? (trend/range/breakout/reversal)
- What is the entry trigger? What confirms it?
- What invalidates the setup?
- How does this differ from what you already have?
- Is this mechanical, semi-mechanical, or discretionary?

**For indicator ideas:**
- What signal does this produce?
- Does an existing indicator already measure this? (check inventory)
- Is this leading, coincident, or lagging?
- Does it repaint? What causes it?
- How does it fit into the decision flow?

**For system architecture ideas:**
- What problem does this solve?
- Does this add complexity? Is it justified? (Principle #3)
- What would the minimum viable version look like? (Principle #12)

## Phase 3: Assess Fit

Before proposing approaches, evaluate against the trader's profile:
- ES/NQ futures compatibility
- 1-minute timeframe suitability
- Apex Trader Funding constraint compatibility
- Overlap with existing 8 indicators
- Automation feasibility
- Complexity budget (Principle #3: simplicity over complexity)

## Phase 4: Propose Approaches

Present 2-3 options with trade-offs:
- Lead with your recommendation and why
- For each option: what it adds, what it costs, what it risks
- Apply YAGNI ruthlessly — remove unnecessary features
- Consider: can this be tested before being built? (Principle #6)

## Phase 5: Present Design

Scale each section to its complexity. Cover:

**For Pine Script indicators:**
- What signals it produces (direction, strength, timing)
- Input parameters and defaults
- Repaint risk assessment
- Delay/lag assessment
- Resource usage estimate
- How it connects to the decision flow
- Non-repainting enforcement strategy

**For system changes:**
- What changes in the decision flow
- What indicators are affected
- What rules change
- How to validate the change

**For strategy candidates:**
- Full rule set (entry, exit, stop, invalidation, session filter)
- Mechanical vs discretionary classification
- Scorecard assessment (use `/score-candidate` pattern)

## After the Design

1. Save design to appropriate location:
   - Strategy designs → `05_Synthesis_and_Candidate_Systems/`
   - Indicator designs → alongside the indicator inventory
   - System architecture → root level or `04_Current_System_and_Indicators/`
2. Commit the design document
3. Invoke `writing-plans` to create implementation plan

## Key Principles

- **One question at a time** — don't overwhelm
- **Assess fit first** — don't design something that doesn't fit the system
- **YAGNI ruthlessly** — remove unnecessary features
- **Check overlap** — always compare against existing indicators before adding new ones
- **Simplicity over complexity** (Principle #3) — a simpler design that captures the core edge is better
- **Evidence before belief** (Principle #7) — skepticism on performance claims
