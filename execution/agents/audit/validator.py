"""
Backtest Validation Gate — wraps Backtester with audit check.

Mirrors PQN's "HALT on dirty run" pattern:
  - Run backtest
  - Run 90-item bias audit
  - Write audit report
  - Raise BacktestHalted if any FAIL items found

Usage:
    python -m execution.agents.audit.validator \\
        --source yfinance --period 60d \\
        --output execution/agents/output/test_run/

    # Or import:
    from execution.agents.audit.validator import BacktestValidator
    validator = BacktestValidator(output_dir=Path("output/run1"))
    report = validator.run_and_audit()
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from execution.agents.audit.bias_checker import AuditReport, BiasChecker
from execution.backtester import BacktestResult


class BacktestHalted(Exception):
    """Raised when audit finds FAIL items — mirrors PQN HALT on dirty run."""
    def __init__(self, report: AuditReport) -> None:
        super().__init__(f"Backtest halted: {len(report.failures)} failure(s)\n" + "\n".join(f"  ✗ {f}" for f in report.failures))
        self.report = report


class BacktestValidator:
    """Runs a backtest and validates it against the 90-item bias checklist.

    Args:
        output_dir: Directory where 6_backtest_report.md and 7_audit_report.md are written.
        halt_on_fail: If True (default), raises BacktestHalted on any FAIL item.
    """

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        halt_on_fail: bool = True,
    ) -> None:
        self.output_dir = output_dir or Path("execution/agents/output/default")
        self.halt_on_fail = halt_on_fail
        self._checker = BiasChecker()

    def audit_result(
        self,
        result: BacktestResult,
        source_code: str = "",
        config_meta: Optional[dict] = None,
    ) -> AuditReport:
        """Audit an existing BacktestResult and write reports.

        Args:
            result:      BacktestResult from Backtester.run()
            source_code: Source code string of the strategy file
            config_meta: Optional metadata dict

        Returns:
            AuditReport

        Raises:
            BacktestHalted: if audit fails and halt_on_fail=True
        """
        report = self._checker.full_audit(result, source_code, config_meta)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Write backtest report
        backtest_md = self.output_dir / "6_backtest_report.md"
        with open(backtest_md, "w") as f:
            f.write("# Backtest Report\n\n")
            f.write(f"**Trades:** {result.metrics.total_trades}  \n")
            f.write(f"**Win Rate:** {result.metrics.win_rate*100:.1f}%  \n")
            f.write(f"**Net P&L:** ${result.metrics.net_pnl:,.2f}  \n")
            f.write(f"**Profit Factor:** {result.metrics.profit_factor:.2f}  \n")
            f.write(f"**Max Drawdown:** {result.metrics.max_drawdown_pct:.2f}%  \n")
            f.write(f"**Sharpe Ratio:** {result.metrics.sharpe_ratio:.2f}  \n\n")
            f.write("```\n" + result.summary() + "\n```\n\n")
            if result.trades:
                f.write("## Trade Log\n\n")
                f.write("| Timestamp | Dir | Entry | Stop | Exit | P&L | Outcome |\n")
                f.write("|-----------|-----|-------|------|------|-----|--------|\n")
                for t in result.trades:
                    f.write(
                        f"| {t.signal.timestamp} | {t.signal.direction} "
                        f"| {t.signal.entry_price:.2f} | {t.signal.stop_price:.2f} "
                        f"| {t.exit_price:.2f} | ${t.pnl_dollars:,.2f} | {t.outcome} |\n"
                    )

        # Write audit report
        audit_md = self.output_dir / "7_audit_report.md"
        with open(audit_md, "w") as f:
            f.write(report.to_markdown())

        print(f"\n{report}")
        print(f"\nBacktest report: {backtest_md}")
        print(f"Audit report:    {audit_md}")

        if self.halt_on_fail and not report.passed:
            raise BacktestHalted(report)

        return report

    def audit_source_only(self, source_code: str) -> AuditReport:
        """Run code-only audit (no BacktestResult needed).

        Useful for catching bugs before running a backtest.
        """
        report = self._checker.full_audit(result=None, source_code=source_code)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        audit_md = self.output_dir / "7_audit_report_code_only.md"
        with open(audit_md, "w") as f:
            f.write(report.to_markdown())
        print(report)
        if self.halt_on_fail and not report.passed:
            raise BacktestHalted(report)
        return report


def main() -> None:
    p = argparse.ArgumentParser(description="Audit a backtest for common biases")
    p.add_argument("--source-file", type=Path, help="Path to strategy source file to audit")
    p.add_argument("--output", type=Path, default=Path("execution/agents/output/audit"),
                   help="Output directory for reports")
    p.add_argument("--no-halt", action="store_true", help="Continue even if audit fails")
    args = p.parse_args()

    validator = BacktestValidator(output_dir=args.output, halt_on_fail=not args.no_halt)

    source_code = ""
    if args.source_file and args.source_file.exists():
        source_code = args.source_file.read_text()
        print(f"Auditing source: {args.source_file}")

    report = validator.audit_source_only(source_code)
    sys.exit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
