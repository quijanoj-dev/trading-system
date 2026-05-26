"""
Alpaca historical bar feed — 1m resolution, unlimited history (free tier).

Free-tier limitation: Alpaca covers US stocks/ETFs, not CME futures.
Proxy mapping used for the Silver Bullet backtester:
    ES=F  →  SPY  (S&P 500 ETF, ~0.999 corr with ES)
    NQ=F  →  QQQ  (Nasdaq-100 ETF, ~0.999 corr with NQ)

Signal logic (stop hunt, FVG, CHoCH) is timeframe/price-level agnostic —
identical patterns appear on SPY/QQQ. P&L config adjusts to stock params:
    point_value = 1.0   (1 share = $1/point, vs ES $50/point)
    tick_size   = 0.01  (penny increments, vs ES 0.25)

Requires env vars:
    ALPACA_API_KEY     — from Alpaca dashboard (paper or live account)
    ALPACA_SECRET_KEY  — from Alpaca dashboard

Free paper account at https://app.alpaca.markets suffices for data access.

Caches bars to JSON at:
    ~/.project-os/cache/alpaca/{symbol}_{start}_{end}_1m.json
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

_CACHE_DIR = Path.home() / ".project-os" / "cache" / "alpaca"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Futures → ETF proxy mapping
PROXY_MAP: dict[str, str] = {
    "ES=F": "SPY",
    "NQ=F": "QQQ",
    "YM=F": "DIA",
    "RTY=F": "IWM",
}


def _client() -> StockHistoricalDataClient:
    key    = os.environ.get("ALPACA_API_KEY", "")
    secret = os.environ.get("ALPACA_SECRET_KEY", "")
    if not key or not secret:
        raise EnvironmentError(
            "ALPACA_API_KEY and ALPACA_SECRET_KEY must be set.\n"
            "Get them from https://app.alpaca.markets (free paper account works)."
        )
    return StockHistoricalDataClient(key, secret)


def _cache_path(symbol: str, start: str, end: str) -> Path:
    safe = lambda s: s.replace(":", "-").replace(" ", "_")
    return _CACHE_DIR / f"{symbol}_{safe(start)}_{safe(end)}_1m.json"


def fetch_bars(
    symbol: str,
    start: str | datetime,
    end: str | datetime | None = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Fetch 1-minute OHLCV bars from Alpaca.

    Args:
        symbol:    Ticker or futures alias (ES=F auto-maps to SPY).
        start:     ISO date string or datetime, e.g. "2025-01-01".
        end:       ISO date string or datetime. Defaults to now.
        use_cache: Read/write JSON cache to avoid repeat API calls.

    Returns:
        DataFrame with UTC DatetimeIndex and columns [open, high, low, close, volume].
    """
    # Resolve proxy
    resolved = PROXY_MAP.get(symbol, symbol)
    if resolved != symbol:
        print(f"  [alpaca] {symbol} → {resolved} (ETF proxy)")

    if isinstance(start, str):
        start_dt = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
    else:
        start_dt = start.replace(tzinfo=timezone.utc) if start.tzinfo is None else start

    if end is None:
        end_dt = datetime.now(timezone.utc)
    elif isinstance(end, str):
        end_dt = datetime.fromisoformat(end).replace(tzinfo=timezone.utc)
    else:
        end_dt = end.replace(tzinfo=timezone.utc) if end.tzinfo is None else end

    cache_file = _cache_path(resolved, start_dt.date().isoformat(), end_dt.date().isoformat())

    if use_cache and cache_file.exists():
        print(f"  [alpaca] cache hit: {cache_file.name}")
        raw = pd.read_json(cache_file)
        raw.index = pd.to_datetime(raw.index, utc=True)
        raw.index.name = "timestamp"
        return raw.sort_index()

    print(f"  [alpaca] fetching {resolved} {start_dt.date()} → {end_dt.date()} @ 1m...")
    client = _client()

    request = StockBarsRequest(
        symbol_or_symbols=resolved,
        timeframe=TimeFrame(1, TimeFrameUnit.Minute),
        start=start_dt,
        end=end_dt,
        feed="iex",  # free tier; use "sip" for paid
    )

    bars = client.get_stock_bars(request)
    df = bars.df

    if df.empty:
        raise RuntimeError(f"No bars returned for {resolved} ({start_dt.date()} → {end_dt.date()})")

    # Flatten MultiIndex (symbol, timestamp) → timestamp only
    if isinstance(df.index, pd.MultiIndex):
        df = df.reset_index(level=0, drop=True)

    df.index = pd.to_datetime(df.index, utc=True)
    df.index.name = "timestamp"
    df.columns = [c.lower() for c in df.columns]

    cols = [c for c in ("open", "high", "low", "close", "volume") if c in df.columns]
    df = df[cols].sort_index()

    if use_cache:
        df.to_json(cache_file)
        print(f"  [alpaca] cached → {cache_file.name}")

    return df


def fetch_pair(
    es_symbol: str = "ES=F",
    nq_symbol: str = "NQ=F",
    start: str = "2024-01-01",
    end: str | None = None,
    use_cache: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fetch ES + NQ proxies aligned on common timestamps.

    Returns:
        (es_df, nq_df) — both filtered to market hours, common index.
    """
    es = fetch_bars(es_symbol, start, end, use_cache)
    nq = fetch_bars(nq_symbol, start, end, use_cache)

    # Align on common bars (both must have data)
    common = es.index.intersection(nq.index)
    return es.loc[common], nq.loc[common]
