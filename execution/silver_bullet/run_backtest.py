"""
Silver Bullet V1 — Python Backtester CLI

Fetches up to 60 days of 5m ES=F + NQ=F data via yfinance and runs the SBV1
signal generator through the existing Backtester engine.

Usage:
    python -m execution.silver_bullet.run_backtest
    python -m execution.silver_bullet.run_backtest --period 60d --save
    python -m execution.silver_bullet.run_backtest --fvg-min 0.5 --expiry 8
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd
import yfinance as yf

from execution.backtester import Backtester, BacktestConfig
from execution.risk_manager import RiskConfig
from execution.silver_bullet.signals import generate_signals

_TS_ROOT = Path(__file__).resolve().parent.parent.parent
_BACKTEST_RESULTS = (
    _TS_ROOT / "06_Backtesting_and_Validation" / "Backtest_Results.md"
)


# ─── Data fetching ────────────────────────────────────────────────────────────

def _fetch(symbol: str, period: str, interval: str) -> pd.DataFrame:
    raw = yf.download(
        symbol, period=period, interval=interval,
        auto_adjust=True, progress=False, multi_level_index=False,
    )
    if raw.empty:
        raise RuntimeError(f"yfinance returned no data for {symbol} ({period} @ {interval})")

    raw.columns = [c.lower() for c in raw.columns]

    if raw.index.tzinfo is None:
        raw.index = raw.index.tz_localize("UTC")
    else:
        raw.index = raw.index.tz_convert("UTC")

    cols = [c for c in ("open", "high", "low", "close", "volume") if c in raw.columns]
    return raw[cols].sort_index()


# ─── Metrics injection ────────────────────────────────────────────────────────

def _extract(metrics_str: str, label: str) -> str:
    for line in metrics_str.splitlines():
        if label in line:
            return line.split(":")[-1].strip()
    return "—"


def _update_results_md(metrics_str: str, n_signals: int, period: str) -> None:
    if not _BACKTEST_RESULTS.exists():
        print(f"[warn] {_BACKTEST_RESULTS} not found — skipping save")
        return

    content = _BACKTEST_RESULTS.read_text()

    net_profit    = _extract(metrics_str, "Net P&L")
    profit_factor = _extract(metrics_str, "Profit Factor")
    win_rate      = _extract(metrics_str, "Win Rate")
    avg_win       = _extract(metrics_str, "Avg Win")
    avg_loss      = _extract(metrics_str, "Avg Loss")
    expectancy    = _extract(metrics_str, "Expectancy")
    max_dd        = _extract(metrics_str, "Max Drawdown")
    max_streak    = _extract(metrics_str, "Max Consec. Losses")
    total_trades  = _extract(metrics_str, "Trades")

    replacements = {
        r"\| Net profit \| .+ \|":        f"| Net profit | {net_profit} |",
        r"\| Profit factor \| .+ \|":     f"| Profit factor | {profit_factor} |",
        r"\| Win rate \| .+ \|":          f"| Win rate | {win_rate} |",
        r"\| Average win \| .+ \|":       f"| Average win | {avg_win} |",
        r"\| Average loss \| .+ \|":      f"| Average loss | {avg_loss} |",
        r"\| Expectancy \(R\) \| .+ \|":  f"| Expectancy (R) | {expectancy} |",
        r"\| Max drawdown \| .+ \|":      f"| Max drawdown | {max_dd} |",
        r"\| Max losing streak \| .+ \|": f"| Max losing streak | {max_streak} |",
        r"\| Total trades \| .+ \|":      f"| Total trades | {total_trades} |",
    }

    for pattern, replacement in replacements.items():
        content = re.sub(pattern, replacement, content)

    # Note on run parameters
    note = (
        f"\n**Python backtest run:** {period} @ 5m, {n_signals} signals generated. "
        f"Data source: yfinance ES=F + NQ=F.\n"
    )
    if "**Python backtest run:**" not in content:
        content = content.replace("### Notes", note + "\n### Notes")

    _BACKTEST_RESULTS.write_text(content)
    print(f"\nMetrics written to {_BACKTEST_RESULTS}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description="Silver Bullet V1 Python Backtester")
    p.add_argument("--period",   default="60d",  help="yfinance period (max 60d for 5m)")
    p.add_argument("--interval", default="5m",   help="yfinance interval")
    p.add_argument("--r",        type=float, default=2.0, help="R multiple target")
    p.add_argument("--expiry",   type=int,   default=6,   help="Signal expiry bars")
    p.add_argument("--fvg-min",  type=float, default=1.0, help="Minimum FVG gap (points)")
    p.add_argument("--swing",    type=int,   default=5,   help="Pivot swing length")
    p.add_argument("--sh-bars",  type=int,   default=20,  help="Stop hunt lookback bars")
    p.add_argument("--equity",   type=float, default=25_000.0, help="Starting equity")
    p.add_argument("--save",     action="store_true", help="Write metrics to Backtest_Results.md")
    args = p.parse_args()

    # ── Fetch ────────────────────────────────────────────────────────────
    print(f"Fetching ES=F ({args.period} @ {args.interval})...")
    es = _fetch("ES=F", args.period, args.interval)
    print(f"  {len(es):,} bars  |  {es.index[0]}  →  {es.index[-1]}")

    print(f"Fetching NQ=F ({args.period} @ {args.interval})...")
    nq = _fetch("NQ=F", args.period, args.interval)
    print(f"  {len(nq):,} bars  |  {nq.index[0]}  →  {nq.index[-1]}")

    # ── Signals ──────────────────────────────────────────────────────────
    print("\nGenerating SBV1 signals...")
    signals = generate_signals(
        es, nq,
        swing_length=args.swing,
        sh_lookback=args.sh_bars,
        fvg_min=args.fvg_min,
        expiry_bars=args.expiry,
        r_multiple=args.r,
    )
    print(f"  Signals found: {len(signals)}")

    if signals:
        for s in signals:
            arrow = "↑" if s.direction == "long" else "↓"
            rr = abs(s.target_price - s.entry_price) / abs(s.entry_price - s.stop_price)
            print(
                f"  {s.timestamp}  {arrow}  "
                f"entry={s.entry_price:.2f}  stop={s.stop_price:.2f}  "
                f"target={s.target_price:.2f}  ({rr:.1f}R)"
            )
    else:
        print(
            "\n  No signals — 4-signal confluence is rare in a 60-min daily window.\n"
            "  Try --fvg-min 0.25 or --expiry 10 to relax constraints,\n"
            "  or check that ES=F session data covers 10:00–11:00 ET bars."
        )
        sys.exit(0)

    # ── Backtest ─────────────────────────────────────────────────────────
    config = BacktestConfig(
        initial_equity=args.equity,
        risk_config=RiskConfig(
            risk_per_trade_pct=0.5,
            max_position_size=2,
            daily_loss_limit_pct=10.0,   # relaxed for backtest — no daily halt
            max_drawdown_pct=20.0,       # relaxed for backtest
            point_value=50.0,            # ES = $50/point
            tick_size=0.25,
        ),
        slippage_ticks=1.0,
        commission_per_contract=2.50,
        max_holding_bars=24,             # 2 hours of 5m bars before force-close
    )

    bt = Backtester(config)
    result = bt.run(signals, es)

    # ── Output ───────────────────────────────────────────────────────────
    print(f"\n{result.summary()}")

    if result.trades:
        print("\nTrade log:")
        hdr = f"  {'Timestamp':<32} {'Dir':<6} {'Entry':>8} {'Stop':>8} {'Exit':>8} {'P&L $':>10}  Outcome"
        print(hdr)
        print("  " + "─" * (len(hdr) - 2))
        for t in result.trades:
            d = "long" if t.signal.direction == "long" else "short"
            print(
                f"  {str(t.signal.timestamp):<32} {d:<6} "
                f"{t.signal.entry_price:>8.2f} {t.signal.stop_price:>8.2f} "
                f"{t.exit_price:>8.2f} {t.pnl_dollars:>10.2f}  {t.outcome}"
            )

    if args.save:
        _update_results_md(result.summary(), len(signals), args.period)


if __name__ == "__main__":
    main()
