"""
Thin async wrapper around the Anthropic Python SDK.
Reads ANTHROPIC_API_KEY from environment automatically.
"""

from __future__ import annotations

import asyncio
import os
from typing import Optional

import anthropic

_client: Optional[anthropic.Anthropic] = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


async def call_claude(
    system: str,
    user: str,
    model: str = "claude-sonnet-4-6",
    max_tokens: int = 4096,
) -> str:
    """Call Claude API and return the text response.

    Runs the synchronous SDK in a thread pool so it plays nicely with asyncio.
    """
    client = _get_client()

    def _sync_call() -> str:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text

    return await asyncio.get_event_loop().run_in_executor(None, _sync_call)
