"""
Silver Bullet V1 — signal generator (Python port of Pine v2 logic).

Rules:
  - Session gate:  10:00–11:00 ET only
  - Stop hunt:     ES sweeps recent low/high, closes back inside (bullish/bearish)
  - SMT divergence: ES makes new low/high while NQ makes opposite extreme (confirmed only)
  - FVG:           3-bar gap on ES >= fvg_min points
  - CHoCH:         Close crosses the most recent confirmed opposite swing pivot (entry trigger)

State tracking (v2 logic):
  Each of hunt/SMT/FVG sets a flag that stays active for `expiry_bars` bars.
  CHoCH fires the entry only when all three prior flags are active.
"""

from __future__ import annotations

from datetime import time
from typing import Optional

import pandas as pd
import pytz

from execution.backtester import Signal


def _compute_atr(highs: pd.Series, lows: pd.Series, closes: pd.Series, period: int = 14) -> pd.Series:
    hl  = highs - lows
    hpc = (highs - closes.shift(1)).abs()
    lpc = (lows  - closes.shift(1)).abs()
    tr  = pd.concat([hl, hpc, lpc], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

_ET = pytz.timezone("America/New_York")
_SESSION_START = time(10, 0)
_SESSION_END = time(11, 0)


def _in_session(ts: pd.Timestamp) -> bool:
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    et = ts.tz_convert(_ET)
    t = et.time()
    return _SESSION_START <= t < _SESSION_END


def _check_pivot_high(highs: pd.Series, idx: int, length: int) -> Optional[float]:
    """Return the high at idx if it is the pivot high over [idx-length, idx+length]."""
    start = max(0, idx - length)
    end = idx + length
    if end >= len(highs):
        return None
    window = highs.iloc[start:end + 1]
    if highs.iloc[idx] >= window.max():
        return highs.iloc[idx]
    return None


def _check_pivot_low(lows: pd.Series, idx: int, length: int) -> Optional[float]:
    """Return the low at idx if it is the pivot low over [idx-length, idx+length]."""
    start = max(0, idx - length)
    end = idx + length
    if end >= len(lows):
        return None
    window = lows.iloc[start:end + 1]
    if lows.iloc[idx] <= window.min():
        return lows.iloc[idx]
    return None


def generate_signals(
    es: pd.DataFrame,
    nq: pd.DataFrame,
    swing_length: int = 5,
    sh_lookback: int = 20,
    fvg_min: float = 1.0,
    expiry_bars: int = 6,
    r_multiple: float = 3.0,
    require_smt: bool = False,
    atr_mult: float = 0.5,
    atr_stop_mult: float = 0.0,
    htf_ema_period: int = 20,
) -> list[Signal]:
    """
    Generate Silver Bullet V1 trade signals.

    Args:
        es:             5m OHLCV DataFrame for ES=F (columns: open, high, low, close, volume).
                        DatetimeIndex must be UTC-aware, sorted ascending.
        nq:             5m OHLCV DataFrame for NQ=F, same format.
        swing_length:   Pivot confirmation lookback/lookforward (bars each side).
        sh_lookback:    Bars to scan for recent high/low when detecting stop hunt.
        fvg_min:        Minimum FVG gap in points to qualify.
        expiry_bars:    Bars each signal flag stays active after firing.
        r_multiple:     Risk-reward multiple for target calculation.
        atr_mult:       ATR(14) buffer added below/above the hunt-candle extreme for stop.
                        0.0 = stop exactly at the hunt wick; 0.5 (default) = 0.5×ATR buffer.
                        Ignored when atr_stop_mult > 0.
        atr_stop_mult:  When > 0, overrides hunt-wick stop with pure ATR stop:
                        long  → entry - atr_stop_mult × ATR14
                        short → entry + atr_stop_mult × ATR14
                        Recommended value: 2.0 for 1m bars (wider, noise-resistant).
                        Default 0.0 preserves original hunt-wick behaviour.
        htf_ema_period: EMA period for 15m HTF bias gate (Gate 2).
                        Long entries only when 15m close > 15m EMA; short entries only
                        when 15m close < 15m EMA. Set to 0 to disable.

    Returns:
        List of Signal objects, one per qualifying setup.
    """
    common = es.index.intersection(nq.index)
    es = es.loc[common].copy()
    nq = nq.loc[common].copy()

    atr = _compute_atr(es["high"], es["low"], es["close"])

    # HTF bias: resample 1m → 15m, compute EMA, forward-fill back to 1m index.
    # htf_bullish[i] = True when 15m close > 15m EMA at bar i (long bias).
    if htf_ema_period > 0:
        htf = es["close"].resample("15min").last().dropna()
        htf_ema = htf.ewm(span=htf_ema_period, adjust=False).mean()
        htf_bull_15m = (htf > htf_ema)
        htf_bullish: pd.Series | None = htf_bull_15m.reindex(es.index, method="ffill").fillna(False)
    else:
        htf_bullish = None  # disabled: both directions always allowed

    n = len(es)
    signals: list[Signal] = []

    # State flags (mirrors Pine v2 state variables)
    bull_hunt_on  = False;  bull_hunt_bar  = -9999;  bull_hunt_low  = 0.0
    bear_hunt_on  = False;  bear_hunt_bar  = -9999;  bear_hunt_high = 0.0
    bull_fvg_on  = False;  bull_fvg_bar  = -9999
    bear_fvg_on  = False;  bear_fvg_bar  = -9999
    bull_smt_on  = False;  bull_smt_bar  = -9999
    bear_smt_on  = False;  bear_smt_bar  = -9999

    last_ph: Optional[float] = None
    last_pl: Optional[float] = None

    min_start = max(swing_length * 2 + 1, sh_lookback + 1, 3)

    for i in range(min_start, n):
        ts = es.index[i]
        in_sess = _in_session(ts)

        # ── Expire stale flags ──────────────────────────────────────────
        if bull_hunt_on and i - bull_hunt_bar > expiry_bars:
            bull_hunt_on = False
        if bear_hunt_on and i - bear_hunt_bar > expiry_bars:
            bear_hunt_on = False
        if bull_fvg_on and i - bull_fvg_bar > expiry_bars:
            bull_fvg_on = False
        if bear_fvg_on and i - bear_fvg_bar > expiry_bars:
            bear_fvg_on = False
        if bull_smt_on and i - bull_smt_bar > expiry_bars:
            bull_smt_on = False
        if bear_smt_on and i - bear_smt_bar > expiry_bars:
            bear_smt_on = False

        # ── Update pivot levels (confirmed swing_length bars ago) ───────
        conf = i - swing_length
        if conf >= swing_length:
            ph = _check_pivot_high(es["high"], conf, swing_length)
            if ph is not None:
                last_ph = ph
            pl = _check_pivot_low(es["low"], conf, swing_length)
            if pl is not None:
                last_pl = pl

        if not in_sess:
            continue

        # ── Raw signal detection ────────────────────────────────────────
        # Stop hunt
        recent_low  = es["low"].iloc[i - sh_lookback:i].min()
        recent_high = es["high"].iloc[i - sh_lookback:i].max()

        bull_hunt_raw = es["low"].iloc[i] < recent_low and es["close"].iloc[i] > recent_low
        bear_hunt_raw = es["high"].iloc[i] > recent_high and es["close"].iloc[i] < recent_high

        if bull_hunt_raw:
            bull_hunt_on = True;  bull_hunt_bar = i;  bull_hunt_low  = es["low"].iloc[i]
        if bear_hunt_raw:
            bear_hunt_on = True;  bear_hunt_bar = i;  bear_hunt_high = es["high"].iloc[i]

        # FVG (3-bar gap)
        bull_fvg_raw = (
            es["low"].iloc[i] > es["high"].iloc[i - 2]
            and (es["low"].iloc[i] - es["high"].iloc[i - 2]) >= fvg_min
        )
        bear_fvg_raw = (
            es["high"].iloc[i] < es["low"].iloc[i - 2]
            and (es["low"].iloc[i - 2] - es["high"].iloc[i]) >= fvg_min
        )

        if bull_fvg_raw:
            bull_fvg_on = True;  bull_fvg_bar = i
        if bear_fvg_raw:
            bear_fvg_on = True;  bear_fvg_bar = i

        # SMT divergence (confirmed variant)
        bull_smt_raw = (
            es["low"].iloc[i] < es["low"].iloc[i - 1]
            and nq["low"].iloc[i] > nq["low"].iloc[i - 1]
        )
        bear_smt_raw = (
            es["high"].iloc[i] > es["high"].iloc[i - 1]
            and nq["high"].iloc[i] < nq["high"].iloc[i - 1]
        )

        if bull_smt_raw:
            bull_smt_on = True;  bull_smt_bar = i
        if bear_smt_raw:
            bear_smt_on = True;  bear_smt_bar = i

        # ── CHoCH entry trigger ─────────────────────────────────────────
        bull_choch = (
            last_ph is not None
            and es["close"].iloc[i] > last_ph
            and es["close"].iloc[i - 1] <= last_ph
        )
        bear_choch = (
            last_pl is not None
            and es["close"].iloc[i] < last_pl
            and es["close"].iloc[i - 1] >= last_pl
        )

        # ── Entry conditions ────────────────────────────────────────────
        smt_ok_long  = bull_smt_on if require_smt else True
        smt_ok_short = bear_smt_on if require_smt else True
        htf_ok_long  = htf_bullish is None or bool(htf_bullish.iloc[i])
        htf_ok_short = htf_bullish is None or not bool(htf_bullish.iloc[i])
        go_long  = bull_choch and bull_hunt_on and bull_fvg_on and smt_ok_long  and htf_ok_long
        go_short = bear_choch and bear_hunt_on and bear_fvg_on and smt_ok_short and htf_ok_short

        if go_long:
            entry  = es["close"].iloc[i]
            if atr_stop_mult > 0:
                stop = entry - atr_stop_mult * atr.iloc[i]
            else:
                buf  = atr_mult * atr.iloc[i] if atr_mult > 0 else 0.0
                stop = bull_hunt_low - buf
            risk   = entry - stop
            if risk < 0.25:
                continue
            target = entry + risk * r_multiple
            grade  = "A+" if bull_smt_on else "A"
            signals.append(Signal(
                timestamp=ts,
                direction="long",
                entry_price=entry,
                stop_price=stop,
                target_price=target,
                label=f"SBV1-long-{grade}",
            ))
            bull_hunt_on = False
            bull_fvg_on  = False
            bull_smt_on  = False

        elif go_short:
            entry  = es["close"].iloc[i]
            if atr_stop_mult > 0:
                stop = entry + atr_stop_mult * atr.iloc[i]
            else:
                buf  = atr_mult * atr.iloc[i] if atr_mult > 0 else 0.0
                stop = bear_hunt_high + buf
            risk   = stop - entry
            if risk < 0.25:
                continue
            target = entry - risk * r_multiple
            grade  = "A+" if bear_smt_on else "A"
            signals.append(Signal(
                timestamp=ts,
                direction="short",
                entry_price=entry,
                stop_price=stop,
                target_price=target,
                label=f"SBV1-short-{grade}",
            ))
            bear_hunt_on = False
            bear_fvg_on  = False
            bear_smt_on  = False

    return signals
