"""
Agentic Quant System — Main Pipeline Orchestrator

Takes a one-sentence strategy prompt and runs the full 7-phase pipeline:
  1. Lead Agent      — parse prompt → strategy plan
  2. Researchers     — academic + web + code (parallel)
  3. Synthesizer     — merge research → strategy spec
  4. Backtest Planner — spec → implementation plan
  5. Backtester      — run existing backtester CLI
  6. Audit Validator — 90-item bias check → HALT if fail
  7. Implementer     — validated → Alpaca paper script

Usage:
    # Full pipeline
    python -m execution.agents --prompt "Silver Bullet momentum ES futures 10am-11am"

    # Skip researcher phase (use existing research in output dir)
    python -m execution.agents --prompt "..." --skip-research --run-dir output/my_run

    # Dry run (no backtest, no implementation)
    python -m execution.agents --prompt "..." --dry-run

    # Code-only audit (no backtest)
    python -m execution.agents --audit-only --source-file execution/silver_bullet/signals.py
"""

from __future__ import annotations

import argparse
import asyncio
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Pipeline stages
from execution.agents.lead_agent import LeadAgent, StrategyPlan
from execution.agents.researchers.academic import research_academic
from execution.agents.researchers.web import research_web
from execution.agents.researchers.code import research_code
from execution.agents.synthesizer import Synthesizer
from execution.agents.backtest_planner import BacktestPlanner
from execution.agents.audit.validator import BacktestValidator, BacktestHalted
from execution.agents.implementer import Implementer, ImplementationBlocked

_TS_ROOT = Path(__file__).resolve().parent.parent.parent
_OUTPUT_ROOT = _TS_ROOT / "execution" / "agents" / "output"


def _make_run_dir(slug: str) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = _OUTPUT_ROOT / f"{slug}_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _run_backtest_subprocess(cli_cmd: str, run_dir: Path) -> Optional[object]:
    """Run backtest CLI in subprocess and return BacktestResult if possible."""
    print(f"\n[5/7] Running backtest...")
    print(f"  Command: {cli_cmd}")

    result_file = run_dir / "6_backtest_report.md"
    # Run the CLI command
    proc = subprocess.run(
        cli_cmd + " --save",
        shell=True,
        capture_output=True,
        text=True,
        cwd=str(_TS_ROOT),
    )

    if proc.returncode != 0:
        print(f"  [WARN] Backtest exited with code {proc.returncode}")
        print(proc.stderr[-2000:] if proc.stderr else "")

    stdout = proc.stdout or ""
    # Write raw output to report
    result_file.write_text(f"# Backtest Report\n\n```\n{stdout}\n```\n")
    print(f"  Backtest output: {result_file}")
    return stdout


async def run_pipeline(
    prompt: str,
    run_dir: Optional[Path] = None,
    skip_research: bool = False,
    dry_run: bool = False,
    no_halt: bool = False,
) -> Path:
    """Run the full 9-agent pipeline.

    Args:
        prompt:        One-sentence strategy description
        run_dir:       Use existing run dir (skips creating new one)
        skip_research: Skip researcher phase, use existing 1/2/3_*.md
        dry_run:       Skip backtest and implementation (planning only)
        no_halt:       Don't halt on audit failures (report only)

    Returns:
        Path to the run directory containing all artifacts
    """
    print("\n" + "=" * 60)
    print("  AGENTIC QUANT SYSTEM — PIPELINE START")
    print("=" * 60)
    print(f"  Prompt: {prompt}")

    # ── Phase 1: Lead Agent ──────────────────────────────────────────────
    print("\n[1/7] Lead Agent — parsing prompt...")
    lead = LeadAgent()
    plan: StrategyPlan = await lead.parse(prompt)
    print(f"  Strategy: {plan.strategy_name} ({plan.strategy_slug})")
    print(f"  Instrument: {plan.instrument} | Source: {plan.data_source} | Timeframe: {plan.timeframe}")

    if run_dir is None:
        run_dir = _make_run_dir(plan.strategy_slug)

    # Save plan
    import json
    (run_dir / "0_plan.json").write_text(json.dumps(plan.to_dict(), indent=2))
    (run_dir / "0_plan.md").write_text(
        f"# Strategy Plan\n\n"
        f"**Name:** {plan.strategy_name}  \n"
        f"**Signal:** {plan.signal_type}  \n"
        f"**Instrument:** {plan.instrument} | {plan.data_source} | {plan.timeframe}  \n\n"
        f"**Rationale:** {plan.rationale}  \n\n"
        f"**Academic keywords:** {', '.join(plan.academic_keywords)}  \n"
        f"**Web keywords:** {', '.join(plan.web_keywords)}  \n"
        f"**Code keywords:** {', '.join(plan.code_keywords)}  \n"
    )
    print(f"  Run directory: {run_dir}")

    # ── Phase 2: Parallel Research ───────────────────────────────────────
    if not skip_research:
        print("\n[2/7] Research Phase — 3 agents in parallel...")
        await asyncio.gather(
            research_academic(plan.academic_keywords, run_dir),
            research_web(plan.web_keywords, run_dir),
            research_code(plan.code_keywords, run_dir),
        )
        print("  Research complete.")
    else:
        print("\n[2/7] Skipping research (--skip-research)")

    if dry_run:
        print("\n[DRY RUN] Stopping after research phase.")
        print(f"  Artifacts in: {run_dir}")
        return run_dir

    # ── Phase 3: Synthesize ──────────────────────────────────────────────
    print("\n[3/7] Synthesizer — merging research...")
    synthesizer = Synthesizer()
    await synthesizer.synthesize(run_dir)

    # ── Phase 4: Backtest Planner ────────────────────────────────────────
    print("\n[4/7] Backtest Planner — generating implementation plan...")
    planner = BacktestPlanner()
    _, cli_cmd = await planner.plan(run_dir, plan)
    print(f"  CLI command: {cli_cmd}")

    # ── Phase 5: Backtest ────────────────────────────────────────────────
    _run_backtest_subprocess(cli_cmd, run_dir)

    # ── Phase 6: Audit ───────────────────────────────────────────────────
    print("\n[6/7] Audit Validator — running 90-item bias check...")
    source_code = ""
    signals_file = _TS_ROOT / "execution" / "silver_bullet" / "signals.py"
    if signals_file.exists():
        source_code = signals_file.read_text()

    validator = BacktestValidator(output_dir=run_dir, halt_on_fail=not no_halt)

    try:
        report = validator.audit_source_only(source_code)
        print(f"  Audit: {'PASS ✓' if report.passed else 'FAIL ✗'}  Score: {report.score}/100")
    except BacktestHalted as e:
        print(f"\n  ❌ PIPELINE HALTED: {e}")
        print(f"  Fix audit failures, then re-run with: --run-dir {run_dir} --skip-research")
        return run_dir

    # ── Phase 7: Implement ───────────────────────────────────────────────
    print("\n[7/7] Implementer — generating Alpaca paper live script...")
    implementer = Implementer()
    try:
        live_path = await implementer.implement(run_dir)
        print(f"\n{'='*60}")
        print("  PIPELINE COMPLETE ✓")
        print(f"  Live script: {live_path}")
        print(f"  Run it: python {live_path}")
        print(f"{'='*60}\n")
    except ImplementationBlocked as e:
        print(f"\n  ❌ IMPLEMENTATION BLOCKED: {e}")

    return run_dir


async def run_audit_only(source_file: Path, output: Path, no_halt: bool) -> None:
    """Run code-only audit on a source file."""
    print(f"\nAuditing: {source_file}")
    source_code = source_file.read_text() if source_file.exists() else ""
    validator = BacktestValidator(output_dir=output, halt_on_fail=not no_halt)
    try:
        report = validator.audit_source_only(source_code)
        sys.exit(0 if report.passed else 1)
    except BacktestHalted:
        sys.exit(1)


def main() -> None:
    p = argparse.ArgumentParser(
        description="Agentic Quant System — strategy research to live deployment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--prompt", type=str, help="One-sentence strategy description")
    p.add_argument("--run-dir", type=Path, help="Use existing run directory (skip creating new)")
    p.add_argument("--skip-research", action="store_true", help="Skip researcher phase")
    p.add_argument("--dry-run", action="store_true", help="Run lead + research only, no backtest/implementation")
    p.add_argument("--no-halt", action="store_true", help="Don't halt on audit failures (report only)")
    p.add_argument("--audit-only", action="store_true", help="Run code audit only")
    p.add_argument("--source-file", type=Path, help="Source file to audit (with --audit-only)")
    p.add_argument("--output", type=Path, default=_OUTPUT_ROOT / "audit", help="Output dir for audit reports")
    args = p.parse_args()

    if args.audit_only:
        source = args.source_file or (_TS_ROOT / "execution" / "silver_bullet" / "signals.py")
        asyncio.run(run_audit_only(source, args.output, args.no_halt))
        return

    if not args.prompt:
        p.error("--prompt is required (or use --audit-only)")

    asyncio.run(run_pipeline(
        prompt=args.prompt,
        run_dir=args.run_dir,
        skip_research=args.skip_research,
        dry_run=args.dry_run,
        no_halt=args.no_halt,
    ))


if __name__ == "__main__":
    main()
