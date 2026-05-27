"""
Pyth Network price validator — cross-checks CandleStore ES=F/NQ=F closes
against Pyth oracle via Hermes REST API (no API key required).

Usage:
    python -m execution.market_data.pyth_feed --check
    python -m execution.market_data.pyth_feed --check --threshold 0.005
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_HERMES_BASE = "https://hermes.pyth.network/v2"

# Pyth doesn't carry CME futures; use SPY/QQQ ETF oracle feeds as proxies.
# Discovered via /v2/price_feeds?query=SPY/USD&asset_type=equity (2026-05-27).
# Symbols: Equity.US.SPY/USD, Equity.US.QQQ/USD (regular market hours)
_DEFAULT_IDS: dict[str, str] = {
    "ES=F": "19e09bb805456ada3979a7d1cbb4b6d63babc3a0f8e8a9509f68afa5c4c11cd5",  # SPY proxy
    "NQ=F": "9695e2b96ea7b3859da9ed25b7a46a920a776e2fdae19a7bcfdf2b219230452d",  # QQQ proxy
}


@dataclass
class PythPrice:
    symbol: str
    price: float
    conf: float
    publish_time: int
    feed_id: str


@dataclass
class ValidationResult:
    symbol: str
    alpaca_proxy: str
    candle_close: float
    pyth_price: float
    divergence_pct: float
    flagged: bool
    pyth_age_s: int


class PythFeed:
    def __init__(self, price_ids: Optional[dict[str, str]] = None) -> None:
        self._ids: dict[str, str] = dict(_DEFAULT_IDS)
        if price_ids:
            self._ids.update(price_ids)

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{_HERMES_BASE}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params, doseq=True)
        req = urllib.request.Request(url, headers={
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; trading-system/1.0)",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())

    def _discover_id(self, symbol: str) -> str:
        query = symbol.replace("=F", "").replace("=", "")
        results = self._get("/price_feeds", {"query": query, "asset_type": "crypto"})
        # Hermes returns a list; try equity asset type if crypto returns nothing
        if not results:
            results = self._get("/price_feeds", {"query": query, "asset_type": "equity"})
        if not results:
            results = self._get("/price_feeds", {"query": query})
        if not results:
            raise ValueError(f"No Pyth feed found for {symbol!r}")
        return results[0]["id"]

    def _ensure_id(self, symbol: str) -> str:
        if symbol not in self._ids:
            self._ids[symbol] = self._discover_id(symbol)
        return self._ids[symbol]

    def get_price(self, symbol: str) -> PythPrice:
        feed_id = self._ensure_id(symbol)
        # Hermes v2: prefix with 0x if missing
        hex_id = feed_id if feed_id.startswith("0x") else f"0x{feed_id}"
        data = self._get("/updates/price/latest", {"ids[]": hex_id, "encoding": "hex"})
        parsed = data["parsed"][0]
        price_data = parsed["price"]
        expo = price_data["expo"]
        raw = int(price_data["price"])
        conf_raw = int(price_data["conf"])
        price = raw * (10 ** expo)
        conf = conf_raw * (10 ** expo)
        return PythPrice(
            symbol=symbol,
            price=price,
            conf=conf,
            publish_time=parsed["price"]["publish_time"],
            feed_id=hex_id,
        )

    def get_prices(self, symbols: list[str]) -> dict[str, PythPrice]:
        ids = [self._ensure_id(s) for s in symbols]
        hex_ids = [i if i.startswith("0x") else f"0x{i}" for i in ids]
        params = {"ids[]": hex_ids, "encoding": "hex"}
        data = self._get("/updates/price/latest", params)
        result: dict[str, PythPrice] = {}
        for i, parsed in enumerate(data["parsed"]):
            sym = symbols[i]
            price_data = parsed["price"]
            expo = price_data["expo"]
            raw = int(price_data["price"])
            conf_raw = int(price_data["conf"])
            price = raw * (10 ** expo)
            conf = conf_raw * (10 ** expo)
            result[sym] = PythPrice(
                symbol=sym,
                price=price,
                conf=conf,
                publish_time=price_data["publish_time"],
                feed_id=hex_ids[i],
            )
        return result


# Alpaca proxy map (mirrors alpaca_feed.py)
_PROXY_MAP = {"ES=F": "SPY", "NQ=F": "QQQ", "YM=F": "DIA", "RTY=F": "IWM"}


def validate_candle_store(
    threshold: float = 0.003,
    symbols: Optional[list[str]] = None,
    feed: Optional[PythFeed] = None,
) -> list[ValidationResult]:
    """Compare latest Alpaca proxy (SPY/QQQ) close vs Pyth oracle price.

    Pyth doesn't carry CME futures directly; both sides use the ETF proxy
    so the price scale matches. Flags if |divergence| > threshold (default 0.3%).
    Falls back to CandleStore if Alpaca feed unavailable.
    """
    import time

    if symbols is None:
        symbols = list(_DEFAULT_IDS.keys())
    if feed is None:
        feed = PythFeed()

    now = int(time.time())
    results: list[ValidationResult] = []

    pyth_prices = feed.get_prices(symbols)

    for sym in symbols:
        proxy = _PROXY_MAP.get(sym, sym)

        # Prefer Alpaca proxy bars (same ETF as Pyth feed)
        close = _fetch_alpaca_close(proxy)

        # Fallback: CandleStore (futures price — scale will differ)
        if close is None:
            try:
                from execution.market_data.candle_store import CandleStore
                store = CandleStore()
                df = store.get_candles(sym, "1d", limit=1)
                if not df.empty:
                    close = float(df["close"].iloc[-1])
            except Exception:
                pass

        if close is None:
            continue

        pp = pyth_prices.get(sym)
        if pp is None:
            continue

        div = (close - pp.price) / pp.price
        age_s = now - pp.publish_time

        results.append(
            ValidationResult(
                symbol=sym,
                alpaca_proxy=proxy,
                candle_close=close,
                pyth_price=pp.price,
                divergence_pct=round(div * 100, 4),
                flagged=abs(div) > threshold,
                pyth_age_s=age_s,
            )
        )

    return results


def _fetch_alpaca_close(proxy_symbol: str) -> Optional[float]:
    """Return latest close for an Alpaca proxy symbol (SPY/QQQ). Returns None on error."""
    try:
        from execution.market_data.alpaca_feed import fetch_bars
        # Recent window only — avoid pulling full 1m history just for a price check
        df = fetch_bars(proxy_symbol, start="2026-05-01", end=None)
        if df.empty:
            return None
        return float(df["close"].iloc[-1])
    except EnvironmentError:
        # Keys not in env — caller falls back to CandleStore
        return None
    except Exception:
        return None


def _main() -> None:
    import argparse, sys

    parser = argparse.ArgumentParser(description="Pyth price feed validator")
    parser.add_argument("--check", action="store_true", help="Run candle store validation")
    parser.add_argument("--threshold", type=float, default=0.003, help="Divergence threshold (default 0.3%%)")
    parser.add_argument("--symbols", nargs="+", default=None, help="Symbols to check (default: ES=F NQ=F)")
    parser.add_argument("--price", metavar="SYMBOL", help="Fetch live Pyth price for a symbol")
    args = parser.parse_args()

    feed = PythFeed()

    if args.price:
        p = feed.get_price(args.price)
        print(f"{p.symbol}: {p.price:.4f} ± {p.conf:.4f}  (age: live)")
        return

    if args.check:
        results = validate_candle_store(threshold=args.threshold, symbols=args.symbols, feed=feed)
        if not results:
            print("No results — candle store may be empty. Run candle_store.py first.")
            sys.exit(1)
        header = f"{'Symbol':<8} {'Proxy':<6} {'Candle':>10} {'Pyth':>10} {'Div%':>7} {'Age(s)':>7} {'Flag'}"
        print(header)
        print("-" * len(header))
        any_flagged = False
        for r in results:
            flag = "⚠ FLAGGED" if r.flagged else "OK"
            if r.flagged:
                any_flagged = True
            print(
                f"{r.symbol:<8} {r.alpaca_proxy:<6} {r.candle_close:>10.2f} "
                f"{r.pyth_price:>10.2f} {r.divergence_pct:>7.3f}% {r.pyth_age_s:>7}s  {flag}"
            )
        if any_flagged:
            sys.exit(2)
        return

    parser.print_help()


if __name__ == "__main__":
    _main()
