---
name: research
description: >
  Deep research for trading strategies, indicators, Pine Script techniques,
  market microstructure, or platform tooling. Synthesizes findings into
  actionable recommendations grounded in the trader's profile.
  Use when the user says "research this", "look into", "compare options for",
  "what's the best way to", "find out about", or "investigate".
argument-hint: <strategy, indicator concept, Pine technique, platform feature, or market question>
allowed-tools: Read, Grep, Glob, Bash, WebSearch, WebFetch, Agent
---

# Deep Research — Trading System

Technical research analyst for the Trading System Framework. Find the truth,
verify across multiple sources, deliver clear recommendations backed by evidence
and grounded in this specific trader's context (ES/NQ, 1-min, ICT/SMC, Apex).

## Phase 1: Load Context

1. Read `CLAUDE.md` for project identity and current state
2. Read `01_Trading_Profile_and_Objectives/Trading_Profile_Master.md` for fit assessment
3. Read `04_Current_System_and_Indicators/Indicator_Inventory.md` for current tools
4. Read `Framework_Working_Principles.md` for decision guardrails

## Phase 2: Decompose the Question

Break the topic into 3-5 specific sub-questions. Consider:

**If researching a strategy/setup:**
- What are the exact rules? (entry, exit, stop, invalidation)
- What markets/timeframes does it work on?
- Does it fit ES/NQ 1-minute scalping?
- Is there credible evidence (not just marketing)?
- Does it overlap with existing indicators?

**If researching a Pine Script technique:**
- Is it Pine v6 compatible?
- Does it repaint?
- What are the computation costs?
- Are there existing implementations to learn from?

**If researching a platform/tool:**
- Does it integrate with the current stack (TradingView/NinjaTrader/TradeZella)?
- What does it cost?
- Is it compatible with Apex Trader Funding rules?

## Phase 3: Parallel Discovery

Launch parallel search tracks:

**Track 1 — Web Intelligence:**
- 2+ queries per sub-question
- Prioritize: official docs, TradingView docs, NinjaTrader docs, reputable trading research
- Filter for recent content (2024-2026)
- Flag marketing content vs independent analysis

**Track 2 — Codebase Analysis:**
- Search existing Pine scripts for related patterns
- Check if the concept is already implemented (or partially)
- Identify what would need to change

**Track 3 — Alternatives & Comparisons:**
- Find competing approaches to the same problem
- Compare complexity, reliability, automation feasibility

## Phase 4: Verify and Cross-Reference

- Every claim needs 2+ independent sources
- Flag conflicts between sources
- Performance claims get skeptical treatment (Principle #7)
- Verify version compatibility and pricing against official docs

## Phase 5: Synthesize Report

Structure the output as:

```
## Summary
[1-3 sentences: the answer and confidence level]

## Key Findings
[Bulleted findings with confidence ratings: High/Medium/Low]

## Fit Assessment
[How this fits ES/NQ 1-min scalping, the current indicator suite, and Apex constraints]

## Overlap Analysis
[Does this duplicate or conflict with existing indicators/system?]

## Recommendation
[Clear action: adopt / test / save for later / reject]
[If adopt/test: specific next steps]

## Sources
[Numbered list with descriptions]
```

## Quality Standards

- Never summarize a single source — cross-reference everything
- Apply Framework Working Principles, especially #3 (simplicity) and #7 (skepticism)
- Always assess fit against the trader profile, not just general viability
- If research reveals the topic is not worth pursuing, say so clearly
