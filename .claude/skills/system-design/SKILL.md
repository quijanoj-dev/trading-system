---
name: system-design
description: >
  Design trading system architecture — signal pipelines, execution flows,
  automation layouts, or platform integration maps. Use when the user says
  "system design", "map this system", "how should we build this",
  "architect this", "lay out the pipeline", or "design the automation".
argument-hint: <system-type or specific architecture question>
allowed-tools: Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Agent
---

# System Design — Trading System

Design clear, buildable architectures for trading system components.
Output a document with pipeline visualization, named tools, realistic
constraints, and implementation sequence.

## Phase 1: Load Context

1. Read `CLAUDE.md` for project identity and platform stack
2. Read `01_Trading_Profile_and_Objectives/Trading_Profile_Master.md`
3. Read `04_Current_System_and_Indicators/Current_System_Map.md`
4. Read `04_Current_System_and_Indicators/Indicator_Inventory.md`
5. Read `Framework_Working_Principles.md`

## Phase 2: Requirements

Parse what system is being designed. Common patterns for this project:

**Signal Detection Pipeline:**

- Input: market data (1-min ES/NQ bars)
- Process: indicator calculations → signal generation → confluence scoring
- Output: trade signal with direction, confidence, entry zone, stop, target

**Execution Pipeline:**

- Input: trade signal from TradingView
- Process: alert → webhook/bridge → NinjaTrader order
- Output: executed trade with fill confirmation

**Validation Pipeline:**

- Input: trade results from NinjaTrader
- Process: journal in TradeZella → metrics extraction → performance analysis
- Output: system performance report, rule adherence score

**Automation Architecture:**

- TradingView (signals) → NinjaTrader (execution) → TradeZella (journal)
- Replikanto or alternative for copy-trading
- Kill switches, daily loss limits, session filters

**Indicator Consolidation Architecture:**

- Current: 8 indicators (4 redundant SMT variants)
- Target: consolidated suite with mode selectors
- Migration path preserving all capabilities

## Phase 3: Architecture Design

For each pipeline stage define:

- **What tool/platform handles it**
- **What data flows in and out**
- **What constraints exist** (TradingView indicator limits, NinjaTrader API, Apex rules)
- **What can fail** and how to handle it
- **What is manual vs automated today** and what could be automated

Apply the platform stack constraints:

- TradingView: max ~25 indicators per chart, Pine v6, no direct order execution
- NinjaTrader: ATM strategies, market replay, can receive webhooks
- Apex Trader Funding: daily drawdown limits, trailing threshold, specific contract limits
- TradeZella: manual or API journaling, performance analytics

## Phase 4: Output

Structure the deliverable as:

```markdown
## System Overview
[1-paragraph description of what this system does]

## Pipeline Diagram
[Text-based flow diagram using arrows and boxes]

## Stage Details
[Per-stage: tool, inputs, outputs, constraints, failure modes]

## Platform Constraints
[What the current stack can and cannot do]

## Implementation Sequence
[Ordered steps to build this, with dependencies]

## Risks and Mitigations
[What could go wrong, how to prevent or handle it]

## Cost Considerations
[If applicable: platform fees, data fees, API costs]
```

## Quality Standards

- Every design must respect Apex Trader Funding constraints
- Prefer simplicity (Principle #3) — don't over-engineer
- Automation comes last (Principle #11) — design for manual-first, automatable-later
- Flag what requires custom development vs what exists out of the box
- Include kill switches and risk controls in every execution design
