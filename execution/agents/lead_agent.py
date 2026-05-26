"""
Lead Agent — parses one-sentence strategy prompt into a structured StrategyPlan.

Usage:
    from execution.agents.lead_agent import LeadAgent
    import asyncio

    plan = asyncio.run(LeadAgent().parse("Cross-sectional momentum S&P 500 top quintile"))
    print(plan.strategy_name)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from execution.agents._claude import call_claude

_PROMPT_FILE = Path(__file__).parent / "prompts" / "lead_agent.md"


@dataclass
class BacktestParams:
    period: str = "60d"
    start: str = "2024-01-01"
    swing: int = 5
    sh_bars: int = 20
    fvg_min: float = 1.0
    expiry: int = 6
    r_multiple: float = 2.0
    atr_mult: float = 0.5
    require_smt: bool = True


@dataclass
class StrategyPlan:
    strategy_name: str
    strategy_slug: str
    signal_type: str
    instrument: str
    data_source: str
    timeframe: str
    academic_keywords: list[str] = field(default_factory=list)
    web_keywords: list[str] = field(default_factory=list)
    code_keywords: list[str] = field(default_factory=list)
    backtest_params: BacktestParams = field(default_factory=BacktestParams)
    rationale: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2))


class LeadAgent:
    """Parses a strategy prompt into a StrategyPlan."""

    def __init__(self) -> None:
        self._system = _PROMPT_FILE.read_text()

    async def parse(self, prompt: str) -> StrategyPlan:
        """Parse a one-sentence strategy prompt and return a StrategyPlan.

        Args:
            prompt: e.g. "Cross-sectional momentum on S&P 500 top quintile, monthly rebalance"

        Returns:
            StrategyPlan dataclass
        """
        raw = await call_claude(
            system=self._system,
            user=f"Parse this strategy prompt into a JSON plan:\n\n{prompt}",
            max_tokens=1024,
        )

        # Extract JSON from response (handle wrapped markdown)
        json_str = _extract_json(raw)
        data = json.loads(json_str)

        bp_raw = data.get("backtest_params", {})
        bp = BacktestParams(
            period=bp_raw.get("period", "60d"),
            start=bp_raw.get("start", "2024-01-01"),
            swing=bp_raw.get("swing", 5),
            sh_bars=bp_raw.get("sh_bars", 20),
            fvg_min=bp_raw.get("fvg_min", 1.0),
            expiry=bp_raw.get("expiry", 6),
            r_multiple=bp_raw.get("r_multiple", 2.0),
            atr_mult=bp_raw.get("atr_mult", 0.5),
            require_smt=bp_raw.get("require_smt", True),
        )

        return StrategyPlan(
            strategy_name=data.get("strategy_name", "Unknown Strategy"),
            strategy_slug=data.get("strategy_slug", "unknown_strategy"),
            signal_type=data.get("signal_type", "other"),
            instrument=data.get("instrument", "ES=F"),
            data_source=data.get("data_source", "yfinance"),
            timeframe=data.get("timeframe", "5m"),
            academic_keywords=data.get("academic_keywords", []),
            web_keywords=data.get("web_keywords", []),
            code_keywords=data.get("code_keywords", []),
            backtest_params=bp,
            rationale=data.get("rationale", ""),
        )


def _extract_json(text: str) -> str:
    """Extract JSON object from text that may contain markdown fences."""
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return m.group(1)
    m2 = re.search(r"(\{.*\})", text, re.DOTALL)
    if m2:
        return m2.group(1)
    return text.strip()
