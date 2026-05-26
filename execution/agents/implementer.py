"""
Strategy Implementer — converts validated backtest into Alpaca paper live script.

Reads:
  - {run_dir}/5_backtest_plan.md
  - {run_dir}/6_backtest_report.md
  - {run_dir}/7_audit_report.md  (must show PASS)

Writes:
  - {run_dir}/8_live_implementation.py

Usage:
    from execution.agents.implementer import Implementer
    import asyncio

    path = asyncio.run(Implementer().implement(Path("output/my_run")))
"""

from __future__ import annotations

from pathlib import Path

from execution.agents._claude import call_claude
from execution.agents.audit.bias_checker import AuditReport

_PROMPT_FILE = Path(__file__).parent / "prompts" / "implementer.md"


class ImplementationBlocked(Exception):
    """Raised when audit report shows FAIL — implementation blocked."""


class Implementer:
    """Generates Alpaca paper live script from validated backtest."""

    def __init__(self) -> None:
        self._system = _PROMPT_FILE.read_text()

    async def implement(self, run_dir: Path) -> Path:
        """Generate 8_live_implementation.py.

        Args:
            run_dir: Directory containing plan, backtest report, and audit report

        Returns:
            Path to generated 8_live_implementation.py

        Raises:
            ImplementationBlocked: if 7_audit_report.md shows FAIL
        """
        # Verify audit passed
        audit_path = run_dir / "7_audit_report.md"
        if audit_path.exists():
            audit_text = audit_path.read_text()
            if "❌ FAIL" in audit_text or "FAIL" in audit_text.split("\n")[0]:
                raise ImplementationBlocked(
                    f"Audit FAILED — implementation blocked. Fix issues in {audit_path}"
                )
        else:
            raise ImplementationBlocked("No audit report found — run validator first")

        # Load context documents
        docs = {}
        for fname in ["5_backtest_plan.md", "6_backtest_report.md", "7_audit_report.md"]:
            fpath = run_dir / fname
            docs[fname] = fpath.read_text() if fpath.exists() else f"[{fname} not found]"

        context = (
            "## Backtest Plan\n\n" + docs["5_backtest_plan.md"] + "\n\n"
            "## Backtest Report\n\n" + docs["6_backtest_report.md"] + "\n\n"
            "## Audit Report\n\n" + docs["7_audit_report.md"]
        )

        live_code = await call_claude(
            system=self._system,
            user=f"Generate a live Alpaca paper trading script for:\n\n{context}",
            max_tokens=4096,
        )

        # Strip markdown code fences if Claude wrapped in them
        if live_code.startswith("```"):
            import re
            m = re.search(r"```(?:python)?\n(.*?)```", live_code, re.DOTALL)
            if m:
                live_code = m.group(1)

        out_path = run_dir / "8_live_implementation.py"
        out_path.write_text(live_code)
        out_path.chmod(0o755)
        print(f"  Live script written: {out_path}")
        return out_path
