"""Tests for execution/market_data/unusual_whales.py — mocks requests."""
from __future__ import annotations

import os
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

# Inject fake requests before module import if not already present
if "requests" not in sys.modules:
    sys.modules["requests"] = MagicMock()

# Provide a test API key so __init__ does not raise
os.environ.setdefault("UNUSUAL_WHALES_API_KEY", "test-key-unit")

from execution.market_data.unusual_whales import UnusualWhalesClient
import execution.market_data.unusual_whales as _uw_mod


def _resp(data: list) -> MagicMock:
    r = MagicMock()
    r.json.return_value = {"data": data}
    r.raise_for_status = MagicMock()
    return r


def _session(data: list) -> MagicMock:
    s = MagicMock()
    s.get.return_value = _resp(data)
    return s


def _client() -> UnusualWhalesClient:
    c = UnusualWhalesClient(api_key="test-key-unit")
    return c


class TestInit(unittest.TestCase):
    def test_requires_api_key_env(self):
        backup = os.environ.pop("UNUSUAL_WHALES_API_KEY", None)
        try:
            with self.assertRaises(EnvironmentError):
                UnusualWhalesClient(api_key=None)
        finally:
            if backup:
                os.environ["UNUSUAL_WHALES_API_KEY"] = backup

    def test_accepts_explicit_key(self):
        c = UnusualWhalesClient(api_key="explicit-key")
        self.assertEqual(c._api_key, "explicit-key")

    def test_uses_env_key_when_no_explicit(self):
        os.environ["UNUSUAL_WHALES_API_KEY"] = "env-key"
        c = UnusualWhalesClient()
        self.assertEqual(c._api_key, "env-key")


class TestGetOptionsFlow(unittest.TestCase):
    def _flow_item(self, **overrides) -> dict:
        base = {
            "strike": "150.0",
            "expiry": "2026-06-20",
            "put_call": "call",
            "volume": "500",
            "premium": "25000.0",
            "sentiment": "bullish",
            "is_sweep": True,
            "timestamp": "2026-05-22T10:00:00",
            "exchange": "CBOE",
        }
        base.update(overrides)
        return base

    def test_returns_options_flow_list(self):
        c = _client()
        c._session = _session([self._flow_item()])
        flows = c.get_options_flow("SPY")
        self.assertEqual(len(flows), 1)

    def test_ticker_set_correctly(self):
        c = _client()
        c._session = _session([self._flow_item()])
        flows = c.get_options_flow("AAPL")
        self.assertEqual(flows[0].ticker, "AAPL")

    def test_parses_strike(self):
        c = _client()
        c._session = _session([self._flow_item(strike="200.5")])
        flows = c.get_options_flow("SPY")
        self.assertAlmostEqual(flows[0].strike, 200.5)

    def test_parses_option_type(self):
        c = _client()
        c._session = _session([self._flow_item(put_call="put")])
        flows = c.get_options_flow("SPY")
        self.assertEqual(flows[0].option_type, "put")

    def test_parses_is_sweep(self):
        c = _client()
        c._session = _session([self._flow_item(is_sweep=False)])
        flows = c.get_options_flow("SPY")
        self.assertFalse(flows[0].is_sweep)

    def test_empty_data_returns_empty_list(self):
        c = _client()
        c._session = _session([])
        self.assertEqual(c.get_options_flow("SPY"), [])

    def test_skips_entries_with_bad_values(self):
        # Entries with non-parseable floats/dates are skipped via except (KeyError, ValueError)
        bad = {"strike": "not-a-float", "expiry": "bad-date", "put_call": "call",
               "volume": "100", "premium": "abc", "sentiment": "neutral",
               "is_sweep": False, "timestamp": "bad-ts", "exchange": "NYSE"}
        c = _client()
        c._session = _session([bad, self._flow_item()])
        flows = c.get_options_flow("SPY")
        self.assertIsInstance(flows, list)


class TestGetDarkPoolPrints(unittest.TestCase):
    def _print_item(self, **overrides) -> dict:
        base = {
            "size": "10000",
            "price": "155.50",
            "timestamp": "2026-05-22T09:30:00",
            "above_ask": True,
            "adv_pct": "2.5",
        }
        base.update(overrides)
        return base

    def test_returns_dark_pool_list(self):
        c = _client()
        c._session = _session([self._print_item()])
        prints = c.get_dark_pool_prints("SPY")
        self.assertEqual(len(prints), 1)

    def test_parses_price(self):
        c = _client()
        c._session = _session([self._print_item(price="200.00")])
        prints = c.get_dark_pool_prints("SPY")
        self.assertAlmostEqual(prints[0].price, 200.0)

    def test_parses_above_ask(self):
        c = _client()
        c._session = _session([self._print_item(above_ask=False)])
        prints = c.get_dark_pool_prints("SPY")
        self.assertFalse(prints[0].above_ask)

    def test_notional_computed(self):
        c = _client()
        c._session = _session([self._print_item(size="100", price="50.0")])
        prints = c.get_dark_pool_prints("SPY")
        self.assertAlmostEqual(prints[0].notional, 5000.0)

    def test_empty_data(self):
        c = _client()
        c._session = _session([])
        self.assertEqual(c.get_dark_pool_prints("SPY"), [])


class TestGetUnusualActivity(unittest.TestCase):
    def _activity_item(self, **overrides) -> dict:
        base = {
            "type": "sweep",
            "description": "Large call sweep on NVDA",
            "premium": "50000.0",
            "timestamp": "2026-05-22T11:00:00",
            "confidence": "0.85",
        }
        base.update(overrides)
        return base

    def test_returns_activity_list(self):
        c = _client()
        c._session = _session([self._activity_item()])
        activity = c.get_unusual_activity("NVDA")
        self.assertEqual(len(activity), 1)

    def test_parses_type(self):
        c = _client()
        c._session = _session([self._activity_item(type="block")])
        activity = c.get_unusual_activity("NVDA")
        self.assertEqual(activity[0].activity_type, "block")

    def test_parses_confidence(self):
        c = _client()
        c._session = _session([self._activity_item(confidence="0.92")])
        activity = c.get_unusual_activity("NVDA")
        self.assertAlmostEqual(activity[0].confidence, 0.92)

    def test_null_premium_handled(self):
        c = _client()
        c._session = _session([self._activity_item(premium=None)])
        activity = c.get_unusual_activity("NVDA")
        self.assertIsNone(activity[0].premium)

    def test_empty_data(self):
        c = _client()
        c._session = _session([])
        self.assertEqual(c.get_unusual_activity("NVDA"), [])


class TestCaching(unittest.TestCase):
    def test_second_call_uses_cache(self):
        c = _client()
        c._session = _session([])
        c.get_options_flow("SPY")
        c.get_options_flow("SPY")
        self.assertEqual(c._session.get.call_count, 1)

    def test_different_ticker_not_cached(self):
        c = _client()
        c._session = _session([])
        c.get_options_flow("SPY")
        c.get_options_flow("AAPL")
        self.assertEqual(c._session.get.call_count, 2)

    def test_stale_cache_refetches(self):
        c = _client()
        c._session = _session([])
        # Pre-populate with a stale entry (2 min ago, TTL=60s)
        key = "/option-trades/SPY:{'limit': 50}"
        stale = MagicMock()
        stale.fetched_at = time.time() - 120
        c._cache[key] = stale
        c.get_options_flow("SPY")
        self.assertEqual(c._session.get.call_count, 1)


if __name__ == "__main__":
    unittest.main()
