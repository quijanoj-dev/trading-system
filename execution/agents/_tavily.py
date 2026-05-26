"""
Async Tavily search wrapper.
Reads TAVILY_API_KEY from environment.
"""

from __future__ import annotations

import os
from typing import Optional

import httpx

_TAVILY_BASE = "https://api.tavily.com"
_DEFAULT_TIMEOUT = 30.0


def _api_key() -> str:
    key = os.environ.get("TAVILY_API_KEY", "")
    if not key:
        raise RuntimeError("TAVILY_API_KEY not set in environment")
    return key


async def tavily_search(
    query: str,
    search_depth: str = "advanced",
    max_results: int = 10,
    include_domains: Optional[list[str]] = None,
    exclude_domains: Optional[list[str]] = None,
    include_raw_content: bool = False,
) -> list[dict]:
    """Search via Tavily and return list of result dicts.

    Each result dict contains: title, url, content, score.
    """
    payload: dict = {
        "api_key": _api_key(),
        "query": query,
        "search_depth": search_depth,
        "max_results": max_results,
        "include_raw_content": include_raw_content,
    }
    if include_domains:
        payload["include_domains"] = include_domains
    if exclude_domains:
        payload["exclude_domains"] = exclude_domains

    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
        resp = await client.post(f"{_TAVILY_BASE}/search", json=payload)
        resp.raise_for_status()
        data = resp.json()

    return data.get("results", [])


def _fmt_results(results: list[dict], max_chars: int = 800) -> str:
    """Format Tavily results as a markdown list for LLM consumption."""
    lines = []
    for i, r in enumerate(results, 1):
        content = (r.get("content") or "")[:max_chars]
        lines.append(f"### {i}. {r.get('title', 'Untitled')}\n**URL:** {r.get('url', '')}\n\n{content}\n")
    return "\n---\n".join(lines)
