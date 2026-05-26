"""
Code Researcher — searches GitHub repos and Kaggle notebooks for implementations.

Uses Tavily to find open-source code implementing the target strategy.
Summarizes key patterns via Claude.
Writes: {run_dir}/3_code.md
"""

from __future__ import annotations

from pathlib import Path

from execution.agents._claude import call_claude
from execution.agents._tavily import tavily_search, _fmt_results

_SYSTEM = """You are a quantitative trading code researcher.
Summarize open-source code implementations found for the given strategy.
Focus on:
- Core signal/indicator logic and formulas
- Data pipeline (sources, frequency, preprocessing)
- Backtest framework used (Backtrader, VBT, custom, etc.)
- Key parameters and their typical values
- Bugs, gotchas, or improvements noted in comments/issues
Be concise. Extract concrete formulas and parameter values where visible.
Format as clean Markdown with code snippets where helpful."""


async def research_code(keywords: list[str], run_dir: Path) -> Path:
    """Search GitHub/Kaggle and summarize code implementations.

    Args:
        keywords: Strategy keywords from StrategyPlan.code_keywords
        run_dir:  Output directory for this pipeline run

    Returns:
        Path to written 3_code.md
    """
    query = " ".join(keywords) + " Python implementation GitHub"
    print(f"  [Code] Searching: {query}")

    results = await tavily_search(
        query=query,
        search_depth="advanced",
        max_results=8,
        include_domains=["github.com", "kaggle.com", "colab.research.google.com", "gist.github.com"],
    )

    if not results:
        # Fallback: broader search without domain restriction
        results = await tavily_search(
            query=query,
            search_depth="basic",
            max_results=5,
        )

    if not results:
        out = f"# Code/Implementation Research\n\nNo code implementations found for: {query}\n"
        out_path = run_dir / "3_code.md"
        out_path.write_text(out)
        return out_path

    raw_text = _fmt_results(results)
    user_msg = (
        f"Strategy keywords: {', '.join(keywords)}\n\n"
        f"Search results:\n\n{raw_text}\n\n"
        "Summarize the key implementation patterns, formulas, and parameters."
    )

    summary = await call_claude(system=_SYSTEM, user=user_msg, max_tokens=3000)

    out_path = run_dir / "3_code.md"
    out_path.write_text(f"# Code/Implementation Research: {query}\n\n{summary}")
    print(f"  [Code] Written: {out_path}")
    return out_path
