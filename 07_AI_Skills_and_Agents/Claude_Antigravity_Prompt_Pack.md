# Claude / Antigravity Prompt Pack

> **Legacy Reference** — These prompts are now superseded by Claude Code skills (`/extract-course`, `/extract-strategy`, `/score-candidate`, `/pine-architect`), which execute with full project context. Keep this file as reference for manual Claude use outside of Claude Code.

## Master Synthesis Prompt
You are my trading systems architect.

Use the attached knowledge base as the source of truth.

My profile:
- ES/NQ intraday scalper
- 1-minute execution
- TradingView for charting and strategy development
- NinjaTrader for execution
- TradeZella for journaling
- Apex funding context
- goal is to pass evals, build consistency, reduce discretion, and eventually automate a robust strategy

Your tasks:
1. Rank the strategy concepts that best fit my profile
2. Separate mechanical, semi-mechanical, and discretionary ideas
3. Identify which rules can already be coded in Pine Script strategy format
4. Remove redundant indicators and duplicate logic
5. Design 3 candidate systems
6. Recommend which system should become Version 1.0 first
7. Highlight all missing data, assumptions, and overfitting risks

## Prompt to Convert Discretion Into Rules
Review the candidate systems and identify all discretionary concepts and propose objective proxies.

## Simplification Prompt
Simplify my system.

## Validation Roadmap Prompt
Create a validation roadmap for my System V1.

## Pine-Ready Rules Prompt
Convert the chosen System V1 into Pine Script strategy-ready logic.
