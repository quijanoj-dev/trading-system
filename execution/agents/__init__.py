"""
Agentic Quant System — 9-agent pipeline for strategy research → live deployment.

Entry point:
    python -m execution.agents --prompt "..."

Pipeline stages:
    1. Lead Agent      — parse prompt → strategy plan
    2. Researchers     — academic (arXiv/SSRN), web (blogs/forums), code (GitHub)
    3. Synthesizer     — merge 3 research docs → strategy spec
    4. Backtest Planner — spec → implementation plan
    5. Backtester      — run existing execution.backtester
    6. Audit Validator — 90-item bias check → HALT if fail
    7. Implementer     — validated backtest → Alpaca live script
"""
