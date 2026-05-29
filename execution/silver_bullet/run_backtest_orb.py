"""
Opening Range Breakout (ORB) Backtester — SPY/QQQ 1m via Alpaca.

Strategy:
  1. Opening range = first 30 min (9:30–10:00 ET): record OR_HIGH and OR_LOW
  2. First bar that closes ABOVE OR_HIGH → LONG entry at close
     First bar that closes BELOW OR_LOW  → SHORT entry at close
     Only ONE trade per day (first breakout wins)
  3. Stop: OR boundary (OR_LOW for long, OR_HIGH for short)
     Optional: ATR-based stop (entry ± N×ATR14)
  4. Target: R × risk
  5. HTF EMA bias gate: 15m EMA on SPY; skip longs below, skip shorts above
  6. ATR flat-day filter (same as SBV1)
  7. Max hold: trade_end_hour (default 16:00 ET) — exit at close if not hit
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, time
from pathlib import Path
from typing import Optional

import pandas as pd
import pytz

# ── path setup ────────────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from execution.backtester import Signal, Backtester, BacktestConfig
from execution.risk_manager import RiskConfig
from execution.silver_bullet.run_backtest import _fetch_alpaca   # reuse fetcher

_ET = pytz.timezone("America/New_York")

# ── ORB signal generator ──────────────────────────────────────────────────────

def _compute_atr(highs: pd.Series, lows: pd.Series, closes: pd.Series, period: int = 14) -> pd.Series:
    hl  = highs - lows
    hpc = (highs - closes.shift(1)).abs()
    lpc = (lows  - closes.shift(1)).abs()
    tr  = pd.concat([hl, hpc, lpc], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()


def _compute_htf_ema(es_1m: pd.DataFrame, period: int) -> pd.Series:
    """Resample 1m to 15m, compute EMA, forward-fill back onto 1m index."""
    es_15m = es_1m["close"].resample("15min").last().dropna()
    ema_15m = es_15m.ewm(span=period, adjust=False).mean()
    return ema_15m.reindex(es_1m.index, method="ffill")


def generate_orb_signals(
    es: pd.DataFrame,
    range_start: time = time(9, 30),
    range_end: time   = time(10, 0),
    trade_until: time = time(16, 0),
    r_multiple: float = 2.0,
    atr_stop_mult: float = 0.0,
    htf_ema_period: int = 20,
    atr_flat_mult: float = 0.70,
    atr_flat_period: int = 20,
) -> list[Signal]:
    """Generate ORB signals from 1m ES/SPY DataFrame."""

    atr = _compute_atr(es["high"], es["low"], es["close"])
    htf_ema = _compute_htf_ema(es, htf_ema_period) if htf_ema_period > 0 else None

    # ATR flat-day filter: yesterday's ATR vs 20d avg
    daily_atr = atr.resample("1D").last().dropna()
    daily_atr_ma = daily_atr.rolling(atr_flat_period).mean()

    def _is_flat_day(today_date: date) -> bool:
        yesterday = pd.Timestamp(today_date) - pd.Timedelta(days=1)
        # Find most recent prior trading day
        prior = daily_atr[daily_atr.index.date < today_date]
        if len(prior) < atr_flat_period:
            return False
        yesterday_atr = prior.iloc[-1]
        avg = daily_atr_ma[daily_atr_ma.index.date < today_date]
        if avg.empty:
            return False
        return yesterday_atr < atr_flat_mult * avg.iloc[-1]

    # Group by trading day
    es_et = es.copy()
    es_et.index = es_et.index.tz_convert(_ET)

    signals: list[Signal] = []
    for day, day_bars in es_et.groupby(es_et.index.date):
        if _is_flat_day(day):
            continue

        # Opening range bars
        or_bars = day_bars[
            (day_bars.index.time >= range_start) &
            (day_bars.index.time < range_end)
        ]
        if len(or_bars) < 5:
            continue

        or_high = or_bars["high"].max()
        or_low  = or_bars["low"].min()
        or_range = or_high - or_low
        if or_range < 0.05:
            continue  # degenerate day

        # Trade window bars (after range_end, before trade_until)
        trade_bars = day_bars[
            (day_bars.index.time >= range_end) &
            (day_bars.index.time < trade_until)
        ]

        for i, (ts, bar) in enumerate(trade_bars.iterrows()):
            ts_utc = ts.tz_convert("UTC")
            close = bar["close"]

            # HTF EMA bias gate
            if htf_ema is not None:
                ts_utc_idx = ts_utc
                ema_val = htf_ema.asof(ts_utc_idx) if not htf_ema.empty else None
            else:
                ema_val = None

            # LONG breakout
            if close > or_high:
                if ema_val is not None and close < ema_val:
                    break  # HTF says bearish — skip longs today
                entry = close
                if atr_stop_mult > 0:
                    atr_val = atr.asof(ts_utc)
                    stop = entry - atr_stop_mult * atr_val
                else:
                    stop = or_low
                risk = entry - stop
                if risk <= 0:
                    break
                target = entry + r_multiple * risk
                signals.append(Signal(
                    timestamp=ts_utc,
                    direction="long",
                    entry_price=entry,
                    stop_price=stop,
                    target_price=target,
                    fvg_mid=entry,
                ))
                break  # one trade per day

            # SHORT breakout
            if close < or_low:
                if ema_val is not None and close > ema_val:
                    break  # HTF says bullish — skip shorts today
                entry = close
                if atr_stop_mult > 0:
                    atr_val = atr.asof(ts_utc)
                    stop = entry + atr_stop_mult * atr_val
                else:
                    stop = or_high
                risk = stop - entry
                if risk <= 0:
                    break
                target = entry - r_multiple * risk
                signals.append(Signal(
                    timestamp=ts_utc,
                    direction="short",
                    entry_price=entry,
                    stop_price=stop,
                    target_price=target,
                    fvg_mid=entry,
                ))
                break  # one trade per day

    return signals


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description="ORB Backtester — SPY/QQQ 1m Alpaca")

    p.add_argument("--start",       default="2024-01-01")
    p.add_argument("--end",         default=None)
    p.add_argument("--no-cache",    action="store_true")
    p.add_argument("--r",           type=float, default=2.0,   help="R multiple (default: 2.0)")
    p.add_argument("--range-end",   default="10:00",           help="End of opening range HH:MM ET (default: 10:00)")
    p.add_argument("--trade-until", default="16:00",           help="Stop trading after HH:MM ET (default: 16:00)")
    p.add_argument("--atr-stop",    type=float, default=0.0,   help="ATR stop mult (0=use OR boundary)")
    p.add_argument("--htf-ema",     type=int,   default=20,    help="15m EMA period for HTF gate (0=off)")
    p.add_argument("--equity",      type=float, default=25_000.0)
    p.add_argument("--save",        action="store_true")

    args = p.parse_args()

    def _parse_time(s: str) -> time:
        h, m = s.split(":")
        return time(int(h), int(m))

    range_end   = _parse_time(args.range_end)
    trade_until = _parse_time(args.trade_until)

    print(f"Fetching SPY via Alpaca | {args.start} → {args.end or 'today'} @ 1m...")
    es = _fetch_alpaca("ES=F", args.start, args.end)
    print(f"  {len(es):,} bars  |  {es.index[0]}  →  {es.index[-1]}")

    print(f"\nGenerating ORB signals | OR: 09:30–{args.range_end} ET | trade until: {args.trade_until} ET...")
    signals = generate_orb_signals(
        es,
        range_end=range_end,
        trade_until=trade_until,
        r_multiple=args.r,
        atr_stop_mult=args.atr_stop,
        htf_ema_period=args.htf_ema,
    )
    print(f"  Signals found: {len(signals)}")

    if not signals:
        print("No signals — done.")
        return

    for s in signals:
        arrow = "↑" if s.direction == "long" else "↓"
        rr = abs(s.target_price - s.entry_price) / abs(s.entry_price - s.stop_price)
        print(f"  {s.timestamp}  {arrow}  entry={s.entry_price:.2f}  stop={s.stop_price:.2f}  target={s.target_price:.2f}  ({rr:.1f}R)")

    config = BacktestConfig(
        initial_equity=args.equity,
        risk_config=RiskConfig(
            risk_per_trade_pct=0.5,
            max_position_size=100,
            daily_loss_limit_pct=10.0,
            max_drawdown_pct=20.0,
            point_value=1.0,
            tick_size=0.01,
        ),
        max_holding_bars=390,
    )
    bt = Backtester(config)
    result = bt.run(signals, es)
    print(result.summary())


if __name__ == "__main__":
    main()
