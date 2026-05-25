"""
Candle Store — downloads and caches OHLCV bars to JSON files.

Storage: execution/market_data/data/<symbol>/<timeframe>.json
Interface designed for future swap to PostgreSQL (replace _read/_write methods).

Usage:
    python -m execution.market_data.candle_store --refresh          # fetch all
    python -m execution.market_data.candle_store --refresh --quiet  # no output
    python -m execution.market_data.candle_store --get ES=F 1d      # print bars
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

_CONFIG_PATH = Path(__file__).parent / "candle_store_config.yaml"
_SITE_PACKAGES = "/Users/apple/Library/Python/3.9/lib/python/site-packages"


def _ensure_site_packages() -> None:
    if _SITE_PACKAGES not in sys.path:
        sys.path.insert(0, _SITE_PACKAGES)


def _load_config() -> dict:
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)


def _yf_interval_to_key(interval: str) -> str:
    return interval.replace(" ", "")


class CandleStore:
    def __init__(self) -> None:
        self.config = _load_config()
        self.data_dir = Path(self.config["data_dir"])
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _store_path(self, symbol: str, interval: str) -> Path:
        safe_sym = symbol.replace("=", "_").replace("/", "_")
        sym_dir = self.data_dir / safe_sym
        sym_dir.mkdir(parents=True, exist_ok=True)
        return sym_dir / f"{_yf_interval_to_key(interval)}.json"

    def _fetch(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        _ensure_site_packages()
        import yfinance as yf  # noqa: PLC0415

        df = yf.download(symbol, period=period, interval=interval,
                         progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0).str.lower()
        else:
            df.columns = [c.lower() for c in df.columns]
        return df.dropna()

    def fetch_and_store(self, symbol: str, period: str, interval: str) -> int:
        df = self._fetch(symbol, period, interval)
        limit = self.config.get("retention_bars", 200)
        df = df.tail(limit)

        records = []
        for ts, row in df.iterrows():
            records.append({
                "timestamp": ts.isoformat(),
                "open":   float(row["open"]),
                "high":   float(row["high"]),
                "low":    float(row["low"]),
                "close":  float(row["close"]),
                "volume": float(row["volume"]),
            })

        path = self._store_path(symbol, interval)
        path.write_text(json.dumps({"symbol": symbol, "interval": interval,
                                    "bars": records}, indent=2))
        return len(records)

    def get_candles(self, symbol: str, interval: str, limit: int = 200) -> pd.DataFrame:
        path = self._store_path(symbol, interval)
        if not path.exists():
            raise FileNotFoundError(f"No cached data for {symbol}/{interval}. Run --refresh first.")

        data = json.loads(path.read_text())
        df = pd.DataFrame(data["bars"])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
        return df.tail(limit)

    def refresh_all(self, quiet: bool = False) -> dict:
        results: dict[str, int] = {}
        for sym in self.config.get("symbols", []):
            for tf_entry in self.config.get("timeframes", []):
                interval = tf_entry["interval"]
                period   = tf_entry["period"]
                key = f"{sym}/{interval}"
                try:
                    n = self.fetch_and_store(sym, period, interval)
                    results[key] = n
                    if not quiet:
                        print(f"  {key}: {n} bars")
                except Exception as e:
                    results[key] = -1
                    if not quiet:
                        print(f"  {key}: ERROR — {e}", file=sys.stderr)
        return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Candle Store CLI")
    parser.add_argument("--refresh", action="store_true", help="Fetch and store all configured symbols/timeframes")
    parser.add_argument("--quiet",   action="store_true", help="Suppress per-bar output")
    parser.add_argument("--get",     nargs=2, metavar=("SYMBOL", "INTERVAL"), help="Print cached bars for symbol/interval")
    args = parser.parse_args()

    store = CandleStore()

    if args.refresh:
        if not args.quiet:
            print("Refreshing candle store...")
        results = store.refresh_all(quiet=args.quiet)
        if not args.quiet:
            ok = sum(1 for v in results.values() if v > 0)
            print(f"Done: {ok}/{len(results)} succeeded")

    elif args.get:
        sym, interval = args.get
        df = store.get_candles(sym, interval)
        print(df.to_string())

    else:
        parser.print_help()
