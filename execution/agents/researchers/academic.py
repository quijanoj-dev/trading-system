"""
Academic Researcher — searches arXiv and SSRN for strategy papers.

Uses Tavily with domain restriction to academic sources.
Summarizes findings via Claude.
Writes: {run_dir}/1_academic.md
"""

from __future__ import annotations

from pathlib import Path

from execution.agents._claude import call_claude
from execution.agents._tavily import tavily_search, _fmt_results

_SYSTEM = """You are a quantitative finance academic researcher.
Summarize research findings relevant to the given trading strategy.
Focus on:
- Core hypothesis and statistical evidence (Sharpe, alpha, t-stats)
- Factor decay and capacity
- Implementation considerations from academic perspective
- Contradictory evidence or limitations
Be concise and cite paper titles/authors. Format as clean Markdown."""


async def research_academic(keywords: list[str], run_dir: Path) -> Path:
    """Search arXiv/SSRN and summarize findings.

    Args:
        keywords: Strategy keywords from StrategyPlan.academic_keywords
        run_dir:  Output directory for this pipeline run

    Returns:
        Path to written 1_academic.md
    """
    query = " ".join(keywords)
    print(f"  [Academic] Searching: {query}")

    results = await tavily_search(
        query=query,
        search_depth="advanced",
        max_results=8,
        include_domains=["arxiv.org", "ssrn.com", "papers.ssrn.com", "nber.org", "aqr.com"],
    )

    if not results:
        out = f"# Academic Research\n\nNo academic results found for: {query}\n"
        out_path = run_dir / "1_academic.md"
        out_path.write_text(out)
        return out_path

    raw_text = _fmt_results(results)
    user_msg = (
        f"Strategy keywords: {', '.join(keywords)}\n\n"
        f"Search results:\n\n{raw_text}\n\n"
        "Summarize the key academic findings relevant to this strategy."
    )

    summary = await call_claude(system=_SYSTEM, user=user_msg, max_tokens=3000)

    out_path = run_dir / "1_academic.md"
    out_path.write_text(f"# Academic Research: {query}\n\n{summary}")
    print(f"  [Academic] Written: {out_path}")
    return out_path
