"""Polymarket CLOB API connector.

Requires:
    pip install poly-clob-client
    POLYMARKET_API_KEY and POLYMARKET_SECRET environment variables.

Docs: https://docs.polymarket.com
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    from py_clob_client.client import ClobClient
    from py_clob_client.clob_types import ApiCreds, OrderType
    HAS_CLOB = True
except ImportError:
    HAS_CLOB = False


@dataclass
class PolymarketMarket:
    market_id: str
    question: str
    description: str
    yes_price: float    # probability: 0.0-1.0
    no_price: float
    volume: float       # USD
    end_date: str
    spread: float       # yes_price + no_price - 1.0 (ideally ~0)
    active: bool


@dataclass
class PolymarketOrder:
    market_id: str
    side: str           # "YES" or "NO"
    size: float         # USD
    price: float        # limit price (probability)
    order_id: Optional[str] = None
    status: str = "pending"


class PolymarketConnector:
    """Polymarket CLOB API wrapper.

    Default: dry-run mode (logs orders but does not submit).
    Pass live=True to enable real order submission.

    Usage:
        pm = PolymarketConnector()
        markets = pm.get_markets(min_volume=10000)
        pm.place_order("market-id-123", side="YES", size=100, price=0.72)
    """

    def __init__(self, live: bool = False) -> None:
        self._live = live
        self._client: Optional[Any] = None

        if live:
            if not HAS_CLOB:
                raise ImportError("pip install poly-clob-client")
            api_key = os.environ.get("POLYMARKET_API_KEY")
            secret = os.environ.get("POLYMARKET_SECRET")
            passphrase = os.environ.get("POLYMARKET_PASSPHRASE", "")
            if not api_key or not secret:
                raise EnvironmentError(
                    "POLYMARKET_API_KEY and POLYMARKET_SECRET required for live mode."
                )
            creds = ApiCreds(api_key=api_key, api_secret=secret, api_passphrase=passphrase)
            self._client = ClobClient(
                host="https://clob.polymarket.com",
                chain_id=137,  # Polygon mainnet
                creds=creds,
            )

    def get_markets(
        self,
        active: bool = True,
        min_volume: float = 0,
        max_spread: float = 1.0,
    ) -> List[PolymarketMarket]:
        """Fetch open markets. Filters by volume and spread thresholds."""
        if not HAS_CLOB:
            raise ImportError("pip install poly-clob-client")

        client = self._client or ClobClient(host="https://clob.polymarket.com", chain_id=137)
        raw_markets = client.get_markets()

        results = []
        for m in raw_markets:
            try:
                tokens = m.get("tokens", [])
                yes_token = next((t for t in tokens if t.get("outcome") == "Yes"), {})
                no_token = next((t for t in tokens if t.get("outcome") == "No"), {})

                yes_price = float(yes_token.get("price", 0.5))
                no_price = float(no_token.get("price", 0.5))
                volume = float(m.get("volume", 0))
                spread = abs(yes_price + no_price - 1.0)

                if active and not m.get("active", True):
                    continue
                if volume < min_volume:
                    continue
                if spread > max_spread:
                    continue

                results.append(PolymarketMarket(
                    market_id=m.get("condition_id", ""),
                    question=m.get("question", ""),
                    description=m.get("description", ""),
                    yes_price=yes_price,
                    no_price=no_price,
                    volume=volume,
                    end_date=m.get("end_date_iso", ""),
                    spread=spread,
                    active=m.get("active", True),
                ))
            except (KeyError, TypeError, ValueError):
                continue

        return results

    def get_orderbook(self, market_id: str) -> Dict[str, Any]:
        """Fetch orderbook for a market."""
        if not HAS_CLOB:
            raise ImportError("pip install poly-clob-client")
        client = self._client or ClobClient(host="https://clob.polymarket.com", chain_id=137)
        return client.get_order_book(market_id)

    def get_position(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Return current open position in a market (requires live credentials)."""
        if not self._live or not self._client:
            return None
        positions = self._client.get_positions()
        for p in positions:
            if p.get("condition_id") == market_id:
                return p
        return None

    def place_order(
        self,
        market_id: str,
        side: str,
        size: float,
        price: float,
    ) -> PolymarketOrder:
        """Place a limit order.

        Args:
            market_id: Polymarket condition ID.
            side: "YES" or "NO".
            size: USD size.
            price: Limit price as probability (0.0-1.0).

        Returns:
            PolymarketOrder with status="dry_run" if not live.
        """
        order = PolymarketOrder(
            market_id=market_id,
            side=side,
            size=size,
            price=price,
        )

        if not self._live:
            order.status = "dry_run"
            print(
                f"[DRY RUN] Order: {side} ${size:.2f} @ {price:.3f} "
                f"on market {market_id[:16]}..."
            )
            return order

        if not HAS_CLOB or not self._client:
            raise RuntimeError("Live mode requires py-clob-client and credentials.")

        resp = self._client.create_order({
            "condition_id": market_id,
            "token_id": side,
            "price": price,
            "size": size,
            "side": "BUY",
            "order_type": OrderType.GTC,
        })
        order.order_id = resp.get("orderID")
        order.status = "submitted"
        return order
