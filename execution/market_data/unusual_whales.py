"""UnusualWhales API client.

Requires UNUSUAL_WHALES_API_KEY environment variable (paid subscription).
Fallback: use unusualwhales.com free UI manually.

API docs: https://unusualwhales.com/api/documentation
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from execution.market_data.interfaces import (
    DarkPoolPrint,
    MarketDataFeed,
    OptionsFlow,
    UnusualActivity,
)

_BASE_URL = "https://api.unusualwhales.com/api"
_CACHE_TTL = 60  # seconds


@dataclass
class _CachedResult:
    data: Any
    fetched_at: float


class UnusualWhalesClient(MarketDataFeed):
    """UnusualWhales API wrapper.

    Usage:
        client = UnusualWhalesClient()
        flows = client.get_options_flow("SPY", limit=50)
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key or os.environ.get("UNUSUAL_WHALES_API_KEY")
        if not self._api_key:
            raise EnvironmentError(
                "UNUSUAL_WHALES_API_KEY not set. "
                "Subscribe at unusualwhales.com and export the key."
            )
        if not HAS_REQUESTS:
            raise ImportError("pip install requests")
        self._session = requests.Session()
        self._session.headers.update({"Authorization": f"Bearer {self._api_key}"})
        self._cache: Dict[str, _CachedResult] = {}

    def _get(self, path: str, params: Optional[Dict] = None) -> Any:
        cache_key = f"{path}:{params}"
        cached = self._cache.get(cache_key)
        if cached and (time.time() - cached.fetched_at) < _CACHE_TTL:
            return cached.data

        resp = self._session.get(f"{_BASE_URL}{path}", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        self._cache[cache_key] = _CachedResult(data=data, fetched_at=time.time())
        return data

    def get_options_flow(self, ticker: str, limit: int = 50) -> List[OptionsFlow]:
        raw = self._get(f"/option-trades/{ticker}", params={"limit": limit})
        results = []
        for item in raw.get("data", []):
            try:
                results.append(OptionsFlow(
                    ticker=ticker,
                    strike=float(item.get("strike", 0)),
                    expiry=datetime.fromisoformat(item.get("expiry", "2099-01-01")),
                    option_type=item.get("put_call", "call").lower(),
                    size=int(item.get("volume", 0)),
                    premium=float(item.get("premium", 0)),
                    sentiment=item.get("sentiment", "neutral").lower(),
                    is_sweep=item.get("is_sweep", False),
                    timestamp=datetime.fromisoformat(item.get("timestamp", datetime.utcnow().isoformat())),
                    exchange=item.get("exchange", ""),
                ))
            except (KeyError, ValueError):
                continue
        return results

    def get_dark_pool_prints(self, ticker: str, limit: int = 20) -> List[DarkPoolPrint]:
        raw = self._get(f"/darkpool/{ticker}", params={"limit": limit})
        results = []
        for item in raw.get("data", []):
            try:
                size = int(item.get("size", 0))
                price = float(item.get("price", 0))
                results.append(DarkPoolPrint(
                    ticker=ticker,
                    price=price,
                    size=size,
                    notional=price * size,
                    timestamp=datetime.fromisoformat(item.get("timestamp", datetime.utcnow().isoformat())),
                    above_ask=item.get("above_ask", False),
                    adv_pct=float(item.get("adv_pct", 0)),
                ))
            except (KeyError, ValueError):
                continue
        return results

    def get_unusual_activity(self, ticker: str, limit: int = 20) -> List[UnusualActivity]:
        raw = self._get(f"/stock/{ticker}/unusual-options-activity", params={"limit": limit})
        results = []
        for item in raw.get("data", []):
            try:
                results.append(UnusualActivity(
                    ticker=ticker,
                    activity_type=item.get("type", "unusual_volume").lower(),
                    description=item.get("description", ""),
                    premium=float(item.get("premium", 0)) if item.get("premium") else None,
                    timestamp=datetime.fromisoformat(item.get("timestamp", datetime.utcnow().isoformat())),
                    confidence=float(item.get("confidence", 0.5)),
                ))
            except (KeyError, ValueError):
                continue
        return results

    def get_congressional_trades(self, ticker: str, limit: int = 10) -> List[Dict]:
        """Return recent congressional trades for ticker (best-effort)."""
        raw = self._get(f"/congress/trades", params={"ticker": ticker, "limit": limit})
        return raw.get("data", [])
