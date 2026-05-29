"""
Silver Bullet V1 — Live Paper Trading Signal Monitor

Polls Alpaca 1m bars every 60 s during 10:00–11:00 ET (excluding 10:30–10:45 dead zone).
Fires a console alert and appends to Forward_Test_Notes.md when a new signal triggers.

Usage:
    python -m execution.silver_bullet.monitor

    # or with optional overrides:
    python -m execution.silver_bullet.monitor --poll 30 --lookback 300

Env vars required:
    ALPACA_API_KEY
    ALPACA_SECRET_KEY
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytz
import yfinance as yf

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

from execution.silver_bullet.signals import (
    generate_signals,
    _ET,
    _SESSION_START,
    _SESSION_END,
    _DEAD_START,
    _DEAD_END,
)
from execution.silver_bullet.executor import submit_paper_order

# ── Final validated SBV1 params (Alpaca 1m SPY/QQQ scale) ────────────────────

_PARAMS = dict(
    swing_length=10,
    sh_lookback=60,
    fvg_min=0.05,
    expiry_bars=20,
    r_multiple=3.0,
    require_smt=False,
    atr_mult=0.0,
    atr_stop_mult=2.0,
    htf_ema_period=20,
    po3_gate=True,
)

_TS_ROOT = Path(__file__).resolve().parent.parent.parent
_FORWARD_TEST = _TS_ROOT / "Forward_Test_Notes.md"

# Ensure Forward_Test_Notes.md exists
if not _FORWARD_TEST.exists():
    _FORWARD_TEST.write_text("# Forward Test Notes\n\n")


# ── Alpaca live-data helpers ──────────────────────────────────────────────────

def _client() -> StockHistoricalDataClient:
    key    = os.environ.get("ALPACA_API_KEY", "")
    secret = os.environ.get("ALPACA_SECRET_KEY", "")
    if not key or not secret:
        raise EnvironmentError(
            "Set ALPACA_API_KEY and ALPACA_SECRET_KEY env vars before running the monitor."
        )
    return StockHistoricalDataClient(key, secret)


def _fetch_live(symbol: str, lookback_bars: int) -> pd.DataFrame:
    """Fetch the most recent `lookback_bars` 1-minute bars (no cache)."""
    now    = datetime.now(timezone.utc)
    start  = now - timedelta(minutes=lookback_bars + 30)  # buffer for gaps

    client  = _client()
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame(1, TimeFrameUnit.Minute),
        start=start,
        end=now,
        feed="iex",
    )
    bars = client.get_stock_bars(request)
    df   = bars.df

    if df.empty:
        return pd.DataFrame()

    if isinstance(df.index, pd.MultiIndex):
        df = df.reset_index(level=0, drop=True)

    df.index = pd.to_datetime(df.index, utc=True)
    df.index.name = "timestamp"
    df.columns = [c.lower() for c in df.columns]
    cols = [c for c in ("open", "high", "low", "close", "volume") if c in df.columns]
    return df[cols].sort_index().tail(lookback_bars)


# ── Session / market clock helpers ───────────────────────────────────────────

def _now_et() -> datetime:
    return datetime.now(pytz.utc).astimezone(_ET)


def _in_dead_zone(t: datetime) -> bool:
    lt = t.time()
    return _DEAD_START <= lt < _DEAD_END


def _in_session(t: datetime) -> bool:
    lt = t.time()
    if _DEAD_START <= lt < _DEAD_END:
        return False
    return _SESSION_START <= lt < _SESSION_END


def _seconds_until_session() -> float:
    """Seconds until the next 10:00 ET open (or 0 if already in session)."""
    now = _now_et()
    if _in_session(now):
        return 0.0
    today_open = now.replace(hour=10, minute=0, second=0, microsecond=0)
    if now >= today_open:
        # past today's window — wait until tomorrow
        import calendar
        tomorrow = now + timedelta(days=1)
        next_open = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        return max(0.0, (next_open - now).total_seconds())
    return max(0.0, (today_open - now).total_seconds())


# ── Pre-session ATR flat-day filter ──────────────────────────────────────────

def _is_flat_day(threshold: float = 0.70) -> bool:
    """
    Return True when yesterday's daily ATR(14) is below `threshold` × 20-day avg ATR.
    Uses yfinance daily SPY bars — no auth required.

    threshold=0.70 → skip if yesterday's ATR < 70% of 20-day average.
    """
    try:
        raw = yf.download("SPY", period="30d", interval="1d",
                          auto_adjust=True, progress=False, multi_level_index=False)
        if len(raw) < 15:
            return False  # not enough history — don't skip

        raw.columns = [c.lower() for c in raw.columns]
        hl  = raw["high"] - raw["low"]
        hpc = (raw["high"] - raw["close"].shift(1)).abs()
        lpc = (raw["low"]  - raw["close"].shift(1)).abs()
        tr  = pd.concat([hl, hpc, lpc], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()

        yesterday_atr = float(atr.iloc[-1])
        avg_atr_20d   = float(atr.iloc[-20:].mean())

        ratio = yesterday_atr / avg_atr_20d if avg_atr_20d > 0 else 1.0
        flat  = ratio < threshold

        label = "FLAT — skipping session" if flat else "normal"
        print(
            f"  [ATR filter] yesterday={yesterday_atr:.3f}  "
            f"20d-avg={avg_atr_20d:.3f}  ratio={ratio:.2f}  → {label}",
            flush=True,
        )
        return flat

    except Exception as exc:
        print(f"  [ATR filter] error ({exc}) — proceeding anyway", flush=True)
        return False  # fail open: never skip due to data error


# ── Alert / log ──────────────────────────────────────────────────────────────

def _log_signal(sig, grade: str) -> None:
    arrow   = "↑ LONG" if sig.direction == "long" else "↓ SHORT"
    rr      = abs(sig.target_price - sig.entry_price) / abs(sig.entry_price - sig.stop_price)
    ts_et   = sig.timestamp.astimezone(_ET).strftime("%Y-%m-%d %H:%M ET")

    banner = "=" * 60
    alert  = (
        f"\n{banner}\n"
        f"  SBV1 SIGNAL — {grade}\n"
        f"  {arrow}  {ts_et}\n"
        f"  Entry  : {sig.entry_price:.2f}\n"
        f"  Stop   : {sig.stop_price:.2f}\n"
        f"  Target : {sig.target_price:.2f}  ({rr:.1f}R)\n"
        f"{banner}\n"
    )
    print(alert, flush=True)

    # Append to Forward_Test_Notes.md
    note = (
        f"\n## {ts_et}  —  SBV1 {sig.direction.upper()} ({grade})\n\n"
        f"| Field | Value |\n"
        f"|-------|-------|\n"
        f"| Entry | {sig.entry_price:.2f} |\n"
        f"| Stop  | {sig.stop_price:.2f} |\n"
        f"| Target | {sig.target_price:.2f} |\n"
        f"| RR | {rr:.1f}R |\n"
        f"| Signal | {sig.label} |\n\n"
        f"**Result:** — (fill in after trade closes)\n"
    )
    with _FORWARD_TEST.open("a") as fh:
        fh.write(note)
    print(f"  Logged → {_FORWARD_TEST.name}", flush=True)


# ── Main loop ─────────────────────────────────────────────────────────────────

def _run(poll_interval: int, lookback_bars: int, atr_threshold: float) -> None:
    seen: set[pd.Timestamp] = set()  # dedup by signal timestamp
    last_atr_check_date: object = None  # date of last flat-day check

    print("SBV1 Monitor — live signal detection")
    print(f"  Session  : 10:00–11:00 ET (dead zone 10:30–10:45 excluded)")
    print(f"  Symbols  : SPY (ES proxy) + QQQ (NQ proxy)")
    print(f"  Params   : fvg={_PARAMS['fvg_min']} sh={_PARAMS['sh_lookback']} "
          f"swing={_PARAMS['swing_length']} expiry={_PARAMS['expiry_bars']} "
          f"R={_PARAMS['r_multiple']} atr-stop={_PARAMS['atr_stop_mult']}")
    print(f"  ATR gate : skip if yesterday ATR < {atr_threshold:.0%} of 20d avg")
    print(f"  Poll     : every {poll_interval}s")
    print(f"  Log      : {_FORWARD_TEST}")
    print()

    while True:
        now_et = _now_et()

        if not _in_session(now_et):
            wait = _seconds_until_session()
            if wait > 300:
                print(
                    f"[{now_et.strftime('%H:%M ET')}] Outside session — "
                    f"sleeping {wait/60:.0f} min until 10:00 ET...",
                    flush=True,
                )
                time.sleep(min(wait - 60, 3600))  # wake 1 min early to re-sync
                continue
            if _in_dead_zone(now_et):
                print(
                    f"[{now_et.strftime('%H:%M ET')}] Dead zone 10:30–10:45 — sleeping 60s",
                    flush=True,
                )
                time.sleep(60)
                continue
            # Just outside session but close — short sleep
            time.sleep(30)
            continue

        # In session — run flat-day check once per calendar day
        today = now_et.date()
        if last_atr_check_date != today:
            last_atr_check_date = today
            print(f"[{now_et.strftime('%H:%M ET')}] Pre-session ATR check...", flush=True)
            if _is_flat_day(threshold=atr_threshold):
                wait = _seconds_until_session()  # recalculates for next day
                print(
                    f"[{now_et.strftime('%H:%M ET')}] Flat day — session skipped. "
                    f"Next check in ~{(wait+86400)/3600:.0f}h",
                    flush=True,
                )
                time.sleep(23 * 3600)  # sleep ~23h, recheck tomorrow
                continue

        # In session — fetch and scan
        print(
            f"[{now_et.strftime('%H:%M:%S ET')}] Fetching last {lookback_bars} bars...",
            end=" ",
            flush=True,
        )
        try:
            spy = _fetch_live("SPY", lookback_bars)
            qqq = _fetch_live("QQQ", lookback_bars)
        except Exception as exc:
            print(f"fetch error: {exc}", flush=True)
            time.sleep(poll_interval)
            continue

        if spy.empty or qqq.empty:
            print("no data", flush=True)
            time.sleep(poll_interval)
            continue

        # Align on common timestamps
        common = spy.index.intersection(qqq.index)
        spy = spy.loc[common]
        qqq = qqq.loc[common]

        print(f"{len(spy)} bars", flush=True)

        try:
            signals = generate_signals(spy, qqq, **_PARAMS)
        except Exception as exc:
            print(f"  signal error: {exc}", flush=True)
            time.sleep(poll_interval)
            continue

        for sig in signals:
            if sig.timestamp in seen:
                continue
            seen.add(sig.timestamp)
            grade = "A+" if "A+" in sig.label else "A"
            _log_signal(sig, grade)
            submit_paper_order(sig, grade)

        time.sleep(poll_interval)


def main() -> None:
    p = argparse.ArgumentParser(description="SBV1 Live Paper Trading Monitor")
    p.add_argument("--poll",          type=int,   default=60,   help="Poll interval in seconds (default: 60)")
    p.add_argument("--lookback",      type=int,   default=250,  help="Rolling bar window (default: 250)")
    p.add_argument("--atr-threshold", type=float, default=0.70, help="Skip session if yesterday ATR < N × 20d avg (default: 0.70)")
    args = p.parse_args()

    try:
        _run(args.poll, args.lookback, args.atr_threshold)
    except KeyboardInterrupt:
        print("\nMonitor stopped.", flush=True)
        sys.exit(0)


if __name__ == "__main__":
    main()
