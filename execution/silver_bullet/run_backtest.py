"""
Silver Bullet V1 — Python Backtester CLI

Two data sources:
  --source yfinance  (default) — ES=F + NQ=F futures, 5m, max 60d
  --source alpaca               — SPY + QQQ proxies, 1m, unlimited history
                                  Requires ALPACA_API_KEY + ALPACA_SECRET_KEY

Usage:
    # yfinance (5m, 60 days, quick check)
    python -m execution.silver_bullet.run_backtest

    # Alpaca (1m, full history, proper backtest)
    python -m execution.silver_bullet.run_backtest --source alpaca --start 2024-01-01

    # Relaxed params (5m-rescaled; SMT optional by default)
    python -m execution.silver_bullet.run_backtest --sh-bars 4 --swing 1 --expiry 2 --fvg-min 0.25

    # Save metrics to Backtest_Results.md
    python -m execution.silver_bullet.run_backtest --source alpaca --start 2024-01-01 --save
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


# ─── yfinance source ──────────────────────────────────────────────────────────

def _fetch_yfinance(symbol: str, period: str, interval: str) -> pd.DataFrame:
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


# ─── Alpaca source ────────────────────────────────────────────────────────────

def _fetch_alpaca(symbol: str, start: str, end: str | None) -> pd.DataFrame:
    from execution.market_data.alpaca_feed import fetch_bars
    return fetch_bars(symbol, start=start, end=end)


# ─── Metrics injection ────────────────────────────────────────────────────────

def _extract(metrics_str: str, label: str) -> str:
    for line in metrics_str.splitlines():
        if label in line:
            return line.split(":")[-1].strip()
    return "—"


def _update_results_md(metrics_str: str, n_signals: int, source: str, label: str) -> None:
    if not _BACKTEST_RESULTS.exists():
        print(f"[warn] {_BACKTEST_RESULTS} not found — skipping save")
        return

    content = _BACKTEST_RESULTS.read_text()

    replacements = {
        r"\| Net profit \| .+ \|":        f"| Net profit | {_extract(metrics_str, 'Net P&L')} |",
        r"\| Profit factor \| .+ \|":     f"| Profit factor | {_extract(metrics_str, 'Profit Factor')} |",
        r"\| Win rate \| .+ \|":          f"| Win rate | {_extract(metrics_str, 'Win Rate')} |",
        r"\| Average win \| .+ \|":       f"| Average win | {_extract(metrics_str, 'Avg Win')} |",
        r"\| Average loss \| .+ \|":      f"| Average loss | {_extract(metrics_str, 'Avg Loss')} |",
        r"\| Expectancy \(R\) \| .+ \|":  f"| Expectancy (R) | {_extract(metrics_str, 'Expectancy')} |",
        r"\| Max drawdown \| .+ \|":      f"| Max drawdown | {_extract(metrics_str, 'Max Drawdown')} |",
        r"\| Max losing streak \| .+ \|": f"| Max losing streak | {_extract(metrics_str, 'Max Consec. Losses')} |",
        r"\| Total trades \| .+ \|":      f"| Total trades | {_extract(metrics_str, 'Trades')} |",
    }
    for pattern, replacement in replacements.items():
        content = re.sub(pattern, replacement, content)

    note = f"\n**Python backtest run ({label}):** source={source}, {n_signals} signals. "
    if "**Python backtest run" not in content:
        content = content.replace("### Notes", note + "\n### Notes")

    _BACKTEST_RESULTS.write_text(content)
    print(f"\nMetrics written to {_BACKTEST_RESULTS}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description="Silver Bullet V1 Python Backtester")

    # Data source
    src = p.add_argument_group("Data source")
    src.add_argument("--source",   default="yfinance", choices=["yfinance", "alpaca"],
                     help="Data provider (default: yfinance)")
    # yfinance options
    src.add_argument("--period",   default="60d",  help="[yfinance] period, e.g. 60d")
    src.add_argument("--interval", default="5m",   help="[yfinance] interval, e.g. 5m")
    # Alpaca options
    src.add_argument("--start",    default="2024-01-01",
                     help="[alpaca] start date ISO, e.g. 2024-01-01")
    src.add_argument("--end",      default=None,
                     help="[alpaca] end date ISO (default: today)")
    src.add_argument("--no-cache", action="store_true",
                     help="[alpaca] bypass JSON cache, re-fetch from API")

    # Signal parameters
    sig = p.add_argument_group("Signal parameters")
    sig.add_argument("--r",        type=float, default=3.0,  help="R multiple target (default: 3.0 per Finishers Journal)")
    sig.add_argument("--expiry",   type=int,   default=6,    help="Signal expiry bars (default: 6)")
    sig.add_argument("--fvg-min",  type=float, default=1.0,  help="Min FVG gap in points (default: 1.0)")
    sig.add_argument("--swing",    type=int,   default=5,    help="Pivot swing length (default: 5)")
    sig.add_argument("--sh-bars",  type=int,   default=20,   help="Stop hunt lookback bars (default: 20)")
    sig.add_argument("--atr-mult", type=float, default=0.5,
                     help="ATR(14) buffer below/above hunt-wick for stop (default: 0.5; 0=no buffer)")
    sig.add_argument("--atr-stop", type=float, default=0.0,
                     help="Pure ATR stop: entry ± N×ATR14 (default: 0=use hunt-wick; recommended 2.0 for 1m)")
    sig.add_argument("--smt",      action="store_true",      help="Require SMT divergence (booster-only by default per Finishers Journal)")
    sig.add_argument("--htf-ema",  type=int,   default=20,   help="15m EMA period for HTF bias gate (0=disabled, default: 20)")
    sig.add_argument("--no-po3-gate", action="store_true", help="Disable PO3 open bias gate (default: enabled)")
    sig.add_argument("--no-ifvg",     action="store_true", help="Disable iFVG as FVG substitute (default: enabled)")
    sig.add_argument("--session-start", default="10:00", help="Session start time HH:MM ET (default: 10:00)")
    sig.add_argument("--session-end",   default="11:00", help="Session end time HH:MM ET (default: 11:00)")
    sig.add_argument("--no-dead-zone",  action="store_true", help="Disable dead zone filter (default: 10:30–10:45 for SBV1)")
    sig.add_argument("--ema-fan-gate",  action="store_true", help="Skip signals when 13/48/200 EMA on 2m is braided (spread < 0.2%% of price)")

    # Risk / output
    out = p.add_argument_group("Risk / output")
    out.add_argument("--equity",  type=float, default=25_000.0, help="Starting equity (default: 25000)")
    out.add_argument("--save",    action="store_true", help="Write metrics to Backtest_Results.md")

    args = p.parse_args()

    # Parse session window times
    from datetime import time as _time
    def _parse_time(s: str) -> _time:
        h, m = s.split(":")
        return _time(int(h), int(m))

    sess_start = _parse_time(args.session_start)
    sess_end   = _parse_time(args.session_end)
    # Dead zone: SBV1 default 10:30–10:45; disabled for other windows or via flag
    if args.no_dead_zone or sess_start != _time(10, 0):
        dead_s, dead_e = None, None
    else:
        dead_s, dead_e = _time(10, 30), _time(10, 45)

    # ── Fetch data ───────────────────────────────────────────────────────
    if args.source == "alpaca":
        # Alpaca: 1m SPY/QQQ proxies, stock risk config
        print(f"Fetching ES=F proxy (SPY) via Alpaca | {args.start} → {args.end or 'today'} @ 1m...")
        es = _fetch_alpaca("ES=F", args.start, args.end)
        print(f"  {len(es):,} bars  |  {es.index[0]}  →  {es.index[-1]}")

        print(f"Fetching NQ=F proxy (QQQ) via Alpaca | {args.start} → {args.end or 'today'} @ 1m...")
        nq = _fetch_alpaca("NQ=F", args.start, args.end)
        print(f"  {len(nq):,} bars  |  {nq.index[0]}  →  {nq.index[-1]}")

        # Align on common timestamps
        common = es.index.intersection(nq.index)
        es, nq = es.loc[common], nq.loc[common]

        # Stock-adjusted risk config (SPY: $1/point, 1-cent tick)
        rc = RiskConfig(
            risk_per_trade_pct=0.5,
            max_position_size=100,      # shares, not contracts
            daily_loss_limit_pct=10.0,
            max_drawdown_pct=20.0,
            point_value=1.0,            # 1 share × $1/point
            tick_size=0.01,
        )
        max_hold = 60                   # 60 min of 1m bars = 1 session
        source_label = f"Alpaca 1m SPY/QQQ {args.start}→{args.end or 'today'}"
        # Hunt-wick stop is too tight for 1m noise — default to 2×ATR14 unless user overrides
        if args.atr_stop == 0.0:
            args.atr_stop = 2.0
            print("  [auto] 1m bars: defaulting --atr-stop 2.0 (hunt-wick stop too tight for 1m noise)")

    else:
        # yfinance: 5m ES=F/NQ=F futures
        print(f"Fetching ES=F ({args.period} @ {args.interval}) via yfinance...")
        es = _fetch_yfinance("ES=F", args.period, args.interval)
        print(f"  {len(es):,} bars  |  {es.index[0]}  →  {es.index[-1]}")

        print(f"Fetching NQ=F ({args.period} @ {args.interval}) via yfinance...")
        nq = _fetch_yfinance("NQ=F", args.period, args.interval)
        print(f"  {len(nq):,} bars  |  {nq.index[0]}  →  {nq.index[-1]}")

        # Futures risk config (ES: $50/point, 0.25 tick)
        rc = RiskConfig(
            risk_per_trade_pct=0.5,
            max_position_size=2,
            daily_loss_limit_pct=10.0,
            max_drawdown_pct=20.0,
            point_value=50.0,
            tick_size=0.25,
        )
        max_hold = 24                   # 2 hours of 5m bars
        source_label = f"yfinance 5m ES=F/NQ=F {args.period}"

    # ── Signals ──────────────────────────────────────────────────────────
    window_label = f"{args.session_start}–{args.session_end} ET"
    print(f"\nGenerating signals | window: {window_label}...")
    signals = generate_signals(
        es, nq,
        swing_length=args.swing,
        sh_lookback=args.sh_bars,
        fvg_min=args.fvg_min,
        expiry_bars=args.expiry,
        r_multiple=args.r,
        require_smt=args.smt,
        atr_mult=args.atr_mult,
        atr_stop_mult=args.atr_stop,
        htf_ema_period=args.htf_ema,
        po3_gate=not args.no_po3_gate,
        ifvg=not args.no_ifvg,
        session_start=sess_start,
        session_end=sess_end,
        dead_start=dead_s,
        dead_end=dead_e,
        ema_fan_gate=args.ema_fan_gate,
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
            "\n  No signals generated.\n"
            "  Alpaca: try --sh-bars 20 --swing 5 --expiry 6 --fvg-min 0.50\n"
            "  yfinance: try --sh-bars 4 --swing 1 --expiry 2 --fvg-min 0.25"
        )
        sys.exit(0)

    # ── Backtest ─────────────────────────────────────────────────────────
    config = BacktestConfig(
        initial_equity=args.equity,
        risk_config=rc,
        slippage_ticks=1.0,
        commission_per_contract=2.50 if args.source == "yfinance" else 0.0,
        max_holding_bars=max_hold,
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
        _update_results_md(result.summary(), len(signals), args.source, source_label)


if __name__ == "__main__":
    main()
