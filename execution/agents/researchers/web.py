"""
Web Researcher — searches practitioner blogs, forums, and quant communities.

Uses Tavily with domain restriction to practitioner sources.
Summarizes findings via Claude.
Writes: {run_dir}/2_web.md
"""

from __future__ import annotations

from pathlib import Path

from execution.agents._claude import call_claude
from execution.agents._tavily import tavily_search, _fmt_results

_SYSTEM = """You are a quantitative trading practitioner researcher.
Summarize practical implementation insights from web sources.
Focus on:
- Actual backtest results reported by practitioners
- Implementation gotchas and pitfalls
- Parameter sensitivity and robustness notes
- Community consensus on what works vs what's overfitted
- Python/pandas implementation patterns
Be concise. Format as clean Markdown with source attribution."""

_PRACTITIONER_DOMAINS = [
    "quantconnect.com",
    "quantopian.com",
    "quant.stackexchange.com",
    "alpaca.markets",
    "blog.quantinsti.com",
    "robotwealth.com",
    "macrosynergy.com",
    "breakingthemarket.com",
    "financial-hacker.com",
]


async def research_web(keywords: list[str], run_dir: Path) -> Path:
    """Search practitioner sources and summarize findings.

    Args:
        keywords: Strategy keywords from StrategyPlan.web_keywords
        run_dir:  Output directory for this pipeline run

    Returns:
        Path to written 2_web.md
    """
    query = " ".join(keywords) + " trading strategy backtest Python"
    print(f"  [Web] Searching: {query}")

    results = await tavily_search(
        query=query,
        search_depth="advanced",
        max_results=8,
        exclude_domains=["arxiv.org", "ssrn.com", "papers.ssrn.com"],
    )

    if not results:
        out = f"# Web/Practitioner Research\n\nNo practitioner results found for: {query}\n"
        out_path = run_dir / "2_web.md"
        out_path.write_text(out)
        return out_path

    raw_text = _fmt_results(results)
    user_msg = (
        f"Strategy keywords: {', '.join(keywords)}\n\n"
        f"Search results:\n\n{raw_text}\n\n"
        "Summarize the key practitioner insights and implementation details."
    )

    summary = await call_claude(system=_SYSTEM, user=user_msg, max_tokens=3000)

    out_path = run_dir / "2_web.md"
    out_path.write_text(f"# Web/Practitioner Research: {query}\n\n{summary}")
    print(f"  [Web] Written: {out_path}")
    return out_path
