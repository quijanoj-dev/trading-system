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

# SBV1 defaults (10:00–11:00 ET, dead zone 10:30–10:45)
_SESSION_START = time(10, 0)
_SESSION_END   = time(11, 0)
_DEAD_START    = time(10, 30)  # AMD transition dead zone — 0 wins in backtest
_DEAD_END      = time(10, 45)


def _in_session(
    ts: pd.Timestamp,
    session_start: time = _SESSION_START,
    session_end: time = _SESSION_END,
    dead_start: Optional[time] = _DEAD_START,
    dead_end: Optional[time] = _DEAD_END,
) -> bool:
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    et = ts.tz_convert(_ET)
    t = et.time()
    if dead_start and dead_end and dead_start <= t < dead_end:
        return False
    return session_start <= t < session_end


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
    po3_gate: bool = True,
    ifvg: bool = True,
    session_start: time = _SESSION_START,
    session_end: time = _SESSION_END,
    dead_start: Optional[time] = _DEAD_START,
    dead_end: Optional[time] = _DEAD_END,
    ema_fan_gate: bool = False,
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
        po3_gate:       PO3 open bias gate (Gate 3). When True, long entries require
                        entry_price < 15m candle open (price still in discount/manipulation
                        zone); short entries require entry_price > 15m candle open.
                        Disabled when htf_ema_period == 0 (no 15m context available).
        ifvg:           When True, a mitigated prior FVG (iFVG) can substitute for a fresh
                        FVG. A bullish FVG that price has since traded through inverts and
                        acts as resistance (bearish iFVG), and vice versa.

    Returns:
        List of Signal objects, one per qualifying setup.
    """
    common = es.index.intersection(nq.index)
    es = es.loc[common].copy()
    nq = nq.loc[common].copy()

    atr = _compute_atr(es["high"], es["low"], es["close"])

    # HTF bias: resample 1m → 15m, compute EMA + open, forward-fill back to 1m index.
    # htf_bullish[i] = True when 15m close > 15m EMA at bar i (long bias).
    # htf_open_1m[i]  = open of the 15m candle containing bar i (PO3 gate).
    if htf_ema_period > 0:
        htf = es["close"].resample("15min").last().dropna()
        htf_ema = htf.ewm(span=htf_ema_period, adjust=False).mean()
        htf_bull_15m = (htf > htf_ema)
        htf_bullish: pd.Series | None = htf_bull_15m.reindex(es.index, method="ffill").fillna(False)
        htf_open_1m: pd.Series | None = (
            es["open"].resample("15min").first()
            .reindex(es.index, method="ffill")
            .fillna(0.0)
        )
    else:
        htf_bullish = None   # disabled: both directions always allowed
        htf_open_1m = None   # no 15m context → PO3 gate disabled

    # EMA fan (Gate 2b — optional): 13/48/200 EMA on 2m chart.
    # Braided = EMAs tightly stacked (spread < 0.2% of ema200) → skip.
    # Spreading = momentum present → allow entry.
    if ema_fan_gate:
        closes_2m = es["close"].resample("2min").last().dropna()
        _ema13  = closes_2m.ewm(span=13,  adjust=False).mean()
        _ema48  = closes_2m.ewm(span=48,  adjust=False).mean()
        _ema200 = closes_2m.ewm(span=200, adjust=False).mean()
        # Bullish fan: EMAs aligned ascending (13>48>200) — allow longs
        # Bearish fan: EMAs aligned descending (13<48<200) — allow shorts
        # Braided (any other order) — skip both
        _bull_fan_2m: pd.Series = (_ema13 > _ema48) & (_ema48 > _ema200)
        _bear_fan_2m: pd.Series = (_ema13 < _ema48) & (_ema48 < _ema200)
        fan_bull: pd.Series = _bull_fan_2m.reindex(es.index, method="ffill").fillna(False)
        fan_bear: pd.Series = _bear_fan_2m.reindex(es.index, method="ffill").fillna(False)
    else:
        fan_bull = None
        fan_bear = None

    # PDH/PDL + pre-market H/L context (annotation, not a gate).
    # Marks signals within 1 ATR of key levels as level_confluence=True.
    es_et = es.copy()
    es_et.index = es_et.index.tz_convert(_ET)
    _pdh: dict[object, float] = {}  # date → prior day high
    _pdl: dict[object, float] = {}  # date → prior day low
    _pmh: dict[object, float] = {}  # date → pre-market high
    _pml: dict[object, float] = {}  # date → pre-market low

    import datetime as _dt
    for _day, _bars in es_et.groupby(es_et.index.date):
        # regular session bars (9:30–16:00) become the PDH/PDL for the next day
        _sess = _bars[
            (_bars.index.time >= _dt.time(9, 30)) &
            (_bars.index.time < _dt.time(16, 0))
        ]
        if len(_sess):
            _pdh[_day] = float(_sess["high"].max())
            _pdl[_day] = float(_sess["low"].min())
        # pre-market bars (4:00–9:30) for same day
        _pm = _bars[
            (_bars.index.time >= _dt.time(4, 0)) &
            (_bars.index.time < _dt.time(9, 30))
        ]
        if len(_pm):
            _pmh[_day] = float(_pm["high"].max())
            _pml[_day] = float(_pm["low"].min())

    n = len(es)
    signals: list[Signal] = []

    # State flags (mirrors Pine v2 state variables)
    bull_hunt_on  = False;  bull_hunt_bar  = -9999;  bull_hunt_low  = 0.0
    bear_hunt_on  = False;  bear_hunt_bar  = -9999;  bear_hunt_high = 0.0
    bull_fvg_on  = False;  bull_fvg_bar  = -9999;  bull_fvg_mid = 0.0
    bear_fvg_on  = False;  bear_fvg_bar  = -9999;  bear_fvg_mid = 0.0
    bull_smt_on  = False;  bull_smt_bar  = -9999
    bear_smt_on  = False;  bear_smt_bar  = -9999

    # iFVG state — prior FVG zones awaiting mitigation
    prior_bull_fvg_zones: list[tuple[float, float]] = []  # (zone_high=low[i], zone_low=high[i-2])
    prior_bear_fvg_zones: list[tuple[float, float]] = []  # (zone_high=high[i], zone_low=low[i-2])
    bull_ifvg_on = False;  bull_ifvg_bar = -9999;  bull_ifvg_mid = 0.0
    bear_ifvg_on = False;  bear_ifvg_bar = -9999;  bear_ifvg_mid = 0.0

    last_ph: Optional[float] = None
    last_pl: Optional[float] = None

    min_start = max(swing_length * 2 + 1, sh_lookback + 1, 3)

    for i in range(min_start, n):
        ts = es.index[i]
        in_sess = _in_session(ts, session_start, session_end, dead_start, dead_end)

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
        if bull_ifvg_on and i - bull_ifvg_bar > expiry_bars:
            bull_ifvg_on = False
        if bear_ifvg_on and i - bear_ifvg_bar > expiry_bars:
            bear_ifvg_on = False

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
            bull_fvg_mid = (es["low"].iloc[i] + es["high"].iloc[i - 2]) / 2.0
            prior_bull_fvg_zones.append((es["low"].iloc[i], es["high"].iloc[i - 2]))
        if bear_fvg_raw:
            bear_fvg_on = True;  bear_fvg_bar = i
            bear_fvg_mid = (es["high"].iloc[i] + es["low"].iloc[i - 2]) / 2.0
            prior_bear_fvg_zones.append((es["high"].iloc[i], es["low"].iloc[i - 2]))

        # iFVG mitigation: price trades through a prior FVG zone → zone inverts
        if ifvg:
            for zone_high, zone_low in prior_bull_fvg_zones:
                if es["low"].iloc[i] < zone_low:
                    bull_ifvg_on = True;  bull_ifvg_bar = i
                    bull_ifvg_mid = (zone_high + zone_low) / 2.0
                    prior_bull_fvg_zones.clear()
                    break
            for zone_high, zone_low in prior_bear_fvg_zones:
                if es["high"].iloc[i] > zone_high:
                    bear_ifvg_on = True;  bear_ifvg_bar = i
                    bear_ifvg_mid = (zone_high + zone_low) / 2.0
                    prior_bear_fvg_zones.clear()
                    break

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

        # PO3 gate: verify the stop hunt (manipulation) swept into the correct AMD zone.
        # Long  → hunt must have swept below the 15m open active at hunt time (discount).
        # Short → hunt must have swept above the 15m open active at hunt time (premium).
        # Checking the hunt bar (not CHoCH bar) because by CHoCH time price has already
        # crossed the structural level — the discount/premium check belongs at the hunt.
        if po3_gate and htf_open_1m is not None:
            if bull_hunt_on and 0 <= bull_hunt_bar < len(htf_open_1m):
                o15_hunt = float(htf_open_1m.iloc[bull_hunt_bar])
                po3_ok_long = o15_hunt > 0 and bull_hunt_low < o15_hunt
            else:
                po3_ok_long = False
            if bear_hunt_on and 0 <= bear_hunt_bar < len(htf_open_1m):
                o15_hunt = float(htf_open_1m.iloc[bear_hunt_bar])
                po3_ok_short = o15_hunt > 0 and bear_hunt_high > o15_hunt
            else:
                po3_ok_short = False
        else:
            po3_ok_long  = True
            po3_ok_short = True

        bull_fvg_or_ifvg = bull_fvg_on or (ifvg and bull_ifvg_on)
        bear_fvg_or_ifvg = bear_fvg_on or (ifvg and bear_ifvg_on)

        # EMA fan gate: directional — long only when fan bullish, short only when fan bearish
        ema_long_ok  = fan_bull is None or bool(fan_bull.iloc[i])
        ema_short_ok = fan_bear is None or bool(fan_bear.iloc[i])

        go_long  = bull_choch and bull_hunt_on and bull_fvg_or_ifvg and smt_ok_long  and htf_ok_long  and po3_ok_long  and ema_long_ok
        go_short = bear_choch and bear_hunt_on and bear_fvg_or_ifvg and smt_ok_short and htf_ok_short and po3_ok_short and ema_short_ok

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
            fvg_mid_long = bull_fvg_mid if bull_fvg_on else bull_ifvg_mid
            # Level confluence: within 1 ATR of PDH/PDL or pre-market H/L
            _et_date = ts.tz_convert(_ET).date()
            _atr_val = float(atr.iloc[i])
            _levels = []
            _prev = _et_date - _dt.timedelta(days=1)
            if _prev in _pdh: _levels.append(_pdh[_prev])
            if _prev in _pdl: _levels.append(_pdl[_prev])
            if _et_date in _pmh: _levels.append(_pmh[_et_date])
            if _et_date in _pml: _levels.append(_pml[_et_date])
            _lvl_conf = any(abs(entry - lvl) <= _atr_val for lvl in _levels)
            signals.append(Signal(
                timestamp=ts,
                direction="long",
                entry_price=entry,
                stop_price=stop,
                target_price=target,
                label=f"SBV1-long-{grade}",
                fvg_mid=fvg_mid_long,
                level_confluence=_lvl_conf,
            ))
            bull_hunt_on = False
            bull_fvg_on  = False
            bull_smt_on  = False
            bull_ifvg_on = False
            prior_bull_fvg_zones.clear()

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
            fvg_mid_short = bear_fvg_mid if bear_fvg_on else bear_ifvg_mid
            # Level confluence: within 1 ATR of PDH/PDL or pre-market H/L
            _et_date = ts.tz_convert(_ET).date()
            _atr_val = float(atr.iloc[i])
            _levels = []
            _prev = _et_date - _dt.timedelta(days=1)
            if _prev in _pdh: _levels.append(_pdh[_prev])
            if _prev in _pdl: _levels.append(_pdl[_prev])
            if _et_date in _pmh: _levels.append(_pmh[_et_date])
            if _et_date in _pml: _levels.append(_pml[_et_date])
            _lvl_conf = any(abs(entry - lvl) <= _atr_val for lvl in _levels)
            signals.append(Signal(
                timestamp=ts,
                direction="short",
                entry_price=entry,
                stop_price=stop,
                target_price=target,
                label=f"SBV1-short-{grade}",
                fvg_mid=fvg_mid_short,
                level_confluence=_lvl_conf,
            ))
            bear_hunt_on = False
            bear_fvg_on  = False
            bear_smt_on  = False
            bear_ifvg_on = False
            prior_bear_fvg_zones.clear()

    return signals
