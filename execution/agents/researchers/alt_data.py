"""
Alternative Data Researcher — earnings transcript → structured JSON signal.

Implements the EARNINGS_SIGNAL_PROMPT pattern from Man Group's AlphaGPT stack.
Converts SEC/earnings transcript text into quantified signal fields that feed
directly into position sizing and backtest_planner.

Writes: {run_dir}/2b_alt_data.md
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from execution.agents._claude import call_claude

_EARNINGS_SIGNAL_PROMPT = """\
You are a quantitative analyst extracting structured signals from an earnings transcript.

Transcript: {transcript}
Ticker: {ticker}
Quarter: {quarter}

Return ONLY a JSON object with these exact fields (no preamble, no explanation):
{{
  "sentiment_score": <float -1.0 to 1.0, where -1=strongly negative, 0=neutral, 1=strongly positive>,
  "management_confidence": <float 0.0 to 1.0>,
  "guidance_revision": <one of: "raised", "maintained", "lowered", "none">,
  "key_risk_factors": [<list of max 3 strings, most material risks mentioned>],
  "beat_miss": <one of: "beat", "inline", "miss", "not_reported">,
  "forward_commentary": <"positive", "neutral", "cautious", "negative">,
  "trading_signal": <one of: "strong_long", "mild_long", "neutral", "mild_short", "strong_short">
}}

JSON only. No markdown fence. No extra text.
"""

_SYSTEM = """\
You are a senior quantitative analyst specializing in earnings signal extraction.
Your output is machine-parsed. Return valid JSON exactly as specified. No exceptions."""


async def extract_earnings_signal(
    transcript: str,
    ticker: str,
    quarter: str = "",
) -> dict:
    """Extract quantified signal dict from earnings transcript text.

    Args:
        transcript: Raw earnings call transcript text (can be partial)
        ticker:     Equity ticker symbol
        quarter:    e.g. "Q1 2026" (optional, improves context)

    Returns:
        Parsed signal dict with keys matching EARNINGS_SIGNAL_PROMPT schema.
        Returns {"error": str} on parse failure.
    """
    prompt = _EARNINGS_SIGNAL_PROMPT.format(
        transcript=transcript[:8000],  # cap context
        ticker=ticker,
        quarter=quarter or "latest",
    )

    raw = await call_claude(system=_SYSTEM, user=prompt, max_tokens=512)

    try:
        # Strip any accidental markdown fences
        clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse failed: {e}", "raw": raw[:500]}


async def research_alt_data(
    strategy_keywords: list[str],
    run_dir: Path,
    ticker: Optional[str] = None,
    transcript: Optional[str] = None,
) -> Path:
    """Alt-data research step for the agents pipeline.

    If transcript provided: extract structured earnings signal.
    Otherwise: generate synthetic signal template for the strategy context.

    Args:
        strategy_keywords: From StrategyPlan (used when no transcript provided)
        run_dir:           Output directory for this pipeline run
        ticker:            Target ticker for earnings extraction
        transcript:        Raw transcript text (optional)

    Returns:
        Path to written 2b_alt_data.md
    """
    out_path = run_dir / "2b_alt_data.md"

    if transcript and ticker:
        print(f"  [AltData] Extracting earnings signal: {ticker}")
        signal = await extract_earnings_signal(transcript, ticker)
        content = f"# Alternative Data: Earnings Signal — {ticker}\n\n"
        content += "## Extracted Signal\n\n```json\n"
        content += json.dumps(signal, indent=2)
        content += "\n```\n\n"

        if "error" not in signal:
            ts = signal.get("trading_signal", "neutral")
            sent = signal.get("sentiment_score", 0.0)
            guidance = signal.get("guidance_revision", "none")
            content += f"## Summary\n\n"
            content += f"- **Signal**: `{ts}`\n"
            content += f"- **Sentiment**: {sent:+.2f}\n"
            content += f"- **Guidance**: {guidance}\n"
            content += f"- **Risks**: {', '.join(signal.get('key_risk_factors', []))}\n"
        else:
            content += f"> Parse error: {signal.get('error')}\n"

    else:
        # No transcript — emit guidance on what alt data would apply
        kw_str = ", ".join(strategy_keywords)
        print(f"  [AltData] No transcript provided. Generating alt-data context for: {kw_str}")
        context_prompt = (
            f"Strategy keywords: {kw_str}\n\n"
            "List the top 3 alternative data sources most relevant to this strategy, "
            "and for each: (1) data type, (2) expected signal direction, (3) how to obtain it. "
            "Be specific and quantitative. Format as a Markdown table."
        )
        _ctx_system = (
            "You are a quantitative researcher advising on alternative data sources "
            "for systematic trading strategies. Be concise and actionable."
        )
        table = await call_claude(system=_ctx_system, user=context_prompt, max_tokens=800)
        content = f"# Alternative Data Context: {kw_str}\n\n{table}\n"

    out_path.write_text(content)
    print(f"  [AltData] Written: {out_path}")
    return out_path
