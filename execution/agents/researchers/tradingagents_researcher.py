"""
TradingAgents multi-analyst researcher.

Wraps TauricResearch/TradingAgents v0.7.0+ — runs technical, news, and
fundamentals analysts in parallel, then writes a summary to run_dir.

Install: pip install tradingagents  (requires Python >=3.12)
GitHub:  https://github.com/TauricResearch/TradingAgents

If not installed, writes a stub file and returns gracefully so the
orchestrator asyncio.gather() is never blocked.
"""

from __future__ import annotations

import asyncio
from datetime import date
from pathlib import Path
from typing import Optional

_INSTRUMENT_TICKER: dict[str, str] = {
    "ES=F": "SPY",
    "NQ=F": "QQQ",
    "YM=F": "DIA",
    "RTY=F": "IWM",
}


async def research_tradingagents(
    keywords: list[str],
    run_dir: Path,
    ticker: Optional[str] = None,
) -> Path:
    """Run TradingAgents multi-analyst pipeline and write 4_tradingagents.md."""
    out_path = run_dir / "4_tradingagents.md"
    resolved = _INSTRUMENT_TICKER.get(ticker or "", ticker or "SPY")
    analysis_date = date.today().isoformat()

    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG

        config = {
            **DEFAULT_CONFIG,
            "llm_provider": "anthropic",
            "deep_think_llm": "claude-sonnet-4-6",
            "quick_think_llm": "claude-haiku-4-5-20251001",
        }
        ta = TradingAgentsGraph(
            selected_analysts=["technical", "news", "fundamentals"],
            config=config,
        )

        # propagate() is synchronous — run in executor to avoid blocking gather()
        loop = asyncio.get_event_loop()
        state, decision = await loop.run_in_executor(
            None, lambda: ta.propagate(resolved, analysis_date)
        )

        lines: list[str] = [
            f"# TradingAgents Research — {resolved} ({analysis_date})\n",
            f"**Keywords:** {', '.join(keywords)}\n",
        ]
        analyst_reports: dict = state.get("analyst_reports", {})
        for analyst_name, report in analyst_reports.items():
            lines.append(f"## {analyst_name.replace('_', ' ').title()} Analyst\n")
            lines.append(f"{report}\n")
        lines.append(f"## Final Decision\n{decision}\n")
        out_path.write_text("\n".join(lines))

    except ImportError:
        out_path.write_text(
            f"# TradingAgents Research — {resolved} ({analysis_date})\n\n"
            "[Unavailable: `tradingagents` not installed. "
            "Install with: pip install tradingagents  (requires Python >=3.12)]\n"
        )
    except Exception as e:
        out_path.write_text(
            f"# TradingAgents Research — {resolved} ({analysis_date})\n\n"
            f"[Error during analysis: {e}]\n"
        )

    return out_path
