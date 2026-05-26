"""
Backtest Planner — translates research synthesis into a concrete backtest run plan.

Reads:  {run_dir}/4_synthesis.md
Writes: {run_dir}/5_backtest_plan.md

Usage:
    from execution.agents.backtest_planner import BacktestPlanner
    import asyncio

    planner = BacktestPlanner()
    path, cmd = asyncio.run(planner.plan(Path("output/my_run"), plan))
    print(cmd)  # Ready-to-run CLI command
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from execution.agents._claude import call_claude
from execution.agents.lead_agent import StrategyPlan

_PROMPT_FILE = Path(__file__).parent / "prompts" / "backtest_planner.md"


class BacktestPlanner:
    """Generates a backtest implementation plan from research synthesis."""

    def __init__(self) -> None:
        self._system = _PROMPT_FILE.read_text()

    async def plan(
        self,
        run_dir: Path,
        strategy_plan: Optional[StrategyPlan] = None,
    ) -> tuple[Path, str]:
        """Generate 5_backtest_plan.md and return (path, cli_command).

        Args:
            run_dir:       Directory containing 4_synthesis.md
            strategy_plan: StrategyPlan from lead agent (for default params)

        Returns:
            (path_to_plan_md, cli_command_string)
        """
        synthesis_path = run_dir / "4_synthesis.md"
        synthesis = synthesis_path.read_text() if synthesis_path.exists() else "[No synthesis available]"

        context = synthesis
        if strategy_plan:
            context = (
                f"## Strategy Plan from Lead Agent\n\n"
                f"Name: {strategy_plan.strategy_name}\n"
                f"Instrument: {strategy_plan.instrument}\n"
                f"Data Source: {strategy_plan.data_source}\n"
                f"Timeframe: {strategy_plan.timeframe}\n"
                f"Default params: swing={strategy_plan.backtest_params.swing}, "
                f"sh_bars={strategy_plan.backtest_params.sh_bars}, "
                f"fvg_min={strategy_plan.backtest_params.fvg_min}, "
                f"r={strategy_plan.backtest_params.r_multiple}\n\n"
                f"## Research Synthesis\n\n{synthesis}"
            )

        plan_text = await call_claude(
            system=self._system,
            user=f"Generate a backtest implementation plan for:\n\n{context}",
            max_tokens=3000,
        )

        out_path = run_dir / "5_backtest_plan.md"
        out_path.write_text(plan_text)
        print(f"  Backtest plan written: {out_path}")

        # Extract the run command from the plan
        cli_cmd = _extract_run_command(plan_text)
        return out_path, cli_cmd


def _extract_run_command(plan_text: str) -> str:
    """Extract the CLI run command from the plan markdown."""
    m = re.search(r"```bash\n(python -m execution\.silver_bullet\.run_backtest.*?)```", plan_text, re.DOTALL)
    if m:
        return m.group(1).strip().replace("\\\n  ", " ").replace("\\", "")
    return "python -m execution.silver_bullet.run_backtest --source yfinance --period 60d --save"
