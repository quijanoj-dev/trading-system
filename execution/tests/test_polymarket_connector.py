"""Tests for execution/polymarket/connector.py — mocks py_clob_client."""
from __future__ import annotations

import sys
import unittest
from unittest.mock import MagicMock, patch

# Inject fake py_clob_client before connector module is first imported.
# If it's already cached (imported by another test), patch HAS_CLOB + ClobClient directly.
_fake_clob = MagicMock()
for _mod in ("py_clob_client", "py_clob_client.client", "py_clob_client.clob_types"):
    sys.modules.setdefault(_mod, _fake_clob)

from execution.polymarket.connector import PolymarketConnector, PolymarketMarket
import execution.polymarket.connector as _conn_mod


def _raw(
    condition_id: str = "abc123",
    question: str = "Will X happen?",
    active: bool = True,
    volume: float = 20_000,
    yes_price: float = 0.60,
    no_price: float = 0.40,
    end_date: str = "2026-08-01T00:00:00Z",
) -> dict:
    return {
        "condition_id": condition_id,
        "question": question,
        "description": "",
        "active": active,
        "volume": str(volume),
        "end_date_iso": end_date,
        "tokens": [
            {"outcome": "Yes", "price": str(yes_price)},
            {"outcome": "No", "price": str(no_price)},
        ],
    }


def _connector_with(raw_data: list) -> tuple:
    mock_client = MagicMock()
    mock_client.get_markets.return_value = {"data": raw_data}
    connector = PolymarketConnector(live=False)
    connector._client = mock_client
    return connector, mock_client


class TestGetMarkets(unittest.TestCase):
    def _get(self, raw_data, **kwargs):
        connector, _ = _connector_with(raw_data)
        with patch.object(_conn_mod, "HAS_CLOB", True):
            return connector.get_markets(**kwargs)

    def test_returns_market_objects(self):
        markets = self._get([_raw()])
        self.assertEqual(len(markets), 1)
        self.assertIsInstance(markets[0], PolymarketMarket)

    def test_parses_question(self):
        markets = self._get([_raw(question="Will Bitcoin hit 100k?")])
        self.assertEqual(markets[0].question, "Will Bitcoin hit 100k?")

    def test_parses_prices(self):
        markets = self._get([_raw(yes_price=0.72, no_price=0.28)])
        self.assertAlmostEqual(markets[0].yes_price, 0.72)
        self.assertAlmostEqual(markets[0].no_price, 0.28)

    def test_filters_inactive_when_active_true(self):
        markets = self._get([_raw(active=False)], active=True)
        self.assertEqual(len(markets), 0)

    def test_passes_inactive_when_active_false(self):
        markets = self._get([_raw(active=False)], active=False)
        self.assertEqual(len(markets), 1)

    def test_filters_below_min_volume(self):
        markets = self._get([_raw(volume=5_000)], min_volume=10_000)
        self.assertEqual(len(markets), 0)

    def test_passes_above_min_volume(self):
        markets = self._get([_raw(volume=15_000)], min_volume=10_000)
        self.assertEqual(len(markets), 1)

    def test_filters_wide_spread(self):
        # yes=0.6, no=0.6 → spread=|1.2-1|=0.2
        markets = self._get([_raw(yes_price=0.6, no_price=0.6)], max_spread=0.1)
        self.assertEqual(len(markets), 0)

    def test_skips_none_entries(self):
        markets = self._get([None, _raw()])
        self.assertEqual(len(markets), 1)

    def test_empty_dict_creates_default_market(self):
        # Connector fills in defaults for missing fields rather than skipping
        markets = self._get([{}])
        self.assertEqual(len(markets), 1)
        self.assertAlmostEqual(markets[0].yes_price, 0.5)  # default

    def test_multiple_markets(self):
        markets = self._get([_raw("id1"), _raw("id2"), _raw("id3")])
        self.assertEqual(len(markets), 3)

    def test_spread_computed_correctly(self):
        # yes=0.55, no=0.45 → spread=|1.0-1.0|=0.0
        markets = self._get([_raw(yes_price=0.55, no_price=0.45)])
        self.assertAlmostEqual(markets[0].spread, 0.0, places=5)


class TestPlaceOrder(unittest.TestCase):
    def test_dry_run_status(self):
        with patch.object(_conn_mod, "HAS_CLOB", True):
            connector = PolymarketConnector(live=False)
            order = connector.place_order("mkt-123", side="YES", size=100, price=0.65)
        self.assertEqual(order.status, "dry_run")

    def test_dry_run_preserves_market_id(self):
        with patch.object(_conn_mod, "HAS_CLOB", True):
            connector = PolymarketConnector(live=False)
            order = connector.place_order("mkt-456", side="NO", size=50, price=0.40)
        self.assertEqual(order.market_id, "mkt-456")

    def test_dry_run_does_not_call_api(self):
        mock_client = MagicMock()
        with patch.object(_conn_mod, "HAS_CLOB", True):
            connector = PolymarketConnector(live=False)
            connector._client = mock_client
            connector.place_order("mkt-789", side="YES", size=25, price=0.5)
        mock_client.create_order.assert_not_called()

    def test_dry_run_no_credentials_needed(self):
        with patch.object(_conn_mod, "HAS_CLOB", True):
            connector = PolymarketConnector(live=False)
            # should not raise even without API key env vars
            order = connector.place_order("m1", side="YES", size=10, price=0.5)
        self.assertIsNotNone(order)


if __name__ == "__main__":
    unittest.main()
