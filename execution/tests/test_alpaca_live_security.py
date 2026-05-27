"""
BugHunter Security Tests — AlpacaLiveBroker
Covers: F1 (paper=False escalation), F2 (side validation), F3 (qty range)
"""

from __future__ import annotations

import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


def _make_alpaca_sdk_mock():
    """Build a minimal mock of the alpaca-py SDK so tests run without the package."""
    alpaca = types.ModuleType("alpaca")
    trading = types.ModuleType("alpaca.trading")
    client_mod = types.ModuleType("alpaca.trading.client")
    requests_mod = types.ModuleType("alpaca.trading.requests")
    enums_mod = types.ModuleType("alpaca.trading.enums")

    mock_client = MagicMock()
    mock_order = MagicMock()
    mock_order.id = "test-order-id"
    mock_order.status = "accepted"
    mock_client.return_value.submit_order.return_value = mock_order
    mock_client.return_value.get_account.return_value = MagicMock(
        id="PA33WGN2JSU4",
        equity="100000",
        cash="100000",
        buying_power="200000",
        pattern_day_trader=False,
        trading_blocked=False,
    )

    client_mod.TradingClient = mock_client

    class _Side:
        BUY = "buy"
        SELL = "sell"

    class _TIF:
        DAY = "day"

    class _OC:
        BRACKET = "bracket"

    enums_mod.OrderSide = _Side
    enums_mod.TimeInForce = _TIF
    enums_mod.OrderClass = _OC

    # Request classes — accept any kwargs
    for name in ("MarketOrderRequest", "LimitOrderRequest", "TakeProfitRequest", "StopLossRequest"):
        setattr(requests_mod, name, MagicMock(return_value=MagicMock()))

    alpaca.trading = trading
    trading.client = client_mod
    trading.requests = requests_mod
    trading.enums = enums_mod

    sys.modules.setdefault("alpaca", alpaca)
    sys.modules.setdefault("alpaca.trading", trading)
    sys.modules.setdefault("alpaca.trading.client", client_mod)
    sys.modules.setdefault("alpaca.trading.requests", requests_mod)
    sys.modules.setdefault("alpaca.trading.enums", enums_mod)

    return mock_client


class TestAlpacaLiveBrokerSecurity(unittest.TestCase):

    def setUp(self):
        self.mock_client_cls = _make_alpaca_sdk_mock()
        os.environ["ALPACA_API_KEY"] = "test-key"
        os.environ["ALPACA_SECRET_KEY"] = "test-secret"

    def tearDown(self):
        os.environ.pop("ALPACA_API_KEY", None)
        os.environ.pop("ALPACA_SECRET_KEY", None)

    # ── F1: paper=False escalation ───────────────────────────────────────────

    def test_paper_mode_default_is_true(self):
        """Default must be paper=True — live trading must be explicit."""
        from execution.broker_automation.alpaca_live import AlpacaLiveBroker
        broker = AlpacaLiveBroker()
        self.assertTrue(broker.paper, "Default paper must be True — live trading must be explicit")

    def test_live_mode_blocked_without_env_confirm(self):
        """paper=False without ALPACA_LIVE_CONFIRM=true must raise RuntimeError.
        Guards against prompt-injection chain: poisoned research → generated script
        calls AlpacaLiveBroker(paper=False) → real money orders.
        """
        from execution.broker_automation.alpaca_live import AlpacaLiveBroker
        os.environ.pop("ALPACA_LIVE_CONFIRM", None)
        with self.assertRaises(RuntimeError) as ctx:
            AlpacaLiveBroker(paper=False)
        self.assertIn("ALPACA_LIVE_CONFIRM", str(ctx.exception))

    def test_live_mode_allowed_with_env_confirm(self):
        """paper=False with ALPACA_LIVE_CONFIRM=true must succeed."""
        from execution.broker_automation.alpaca_live import AlpacaLiveBroker
        os.environ["ALPACA_LIVE_CONFIRM"] = "true"
        try:
            broker = AlpacaLiveBroker(paper=False)
            self.assertFalse(broker.paper)
        finally:
            os.environ.pop("ALPACA_LIVE_CONFIRM", None)

    def test_missing_api_key_raises(self):
        """Missing ALPACA_API_KEY must raise RuntimeError before any network call."""
        os.environ.pop("ALPACA_API_KEY")
        from execution.broker_automation.alpaca_live import AlpacaLiveBroker
        with self.assertRaises(RuntimeError) as ctx:
            AlpacaLiveBroker()
        self.assertIn("ALPACA_API_KEY", str(ctx.exception))

    def test_missing_secret_key_raises(self):
        """Missing ALPACA_SECRET_KEY must raise RuntimeError before any network call."""
        os.environ.pop("ALPACA_SECRET_KEY")
        from execution.broker_automation.alpaca_live import AlpacaLiveBroker
        with self.assertRaises(RuntimeError) as ctx:
            AlpacaLiveBroker()
        self.assertIn("ALPACA_SECRET_KEY", str(ctx.exception))

    def test_empty_string_keys_raise(self):
        """Empty string keys (os.environ.get default) must be rejected."""
        os.environ["ALPACA_API_KEY"] = ""
        os.environ["ALPACA_SECRET_KEY"] = ""
        from execution.broker_automation.alpaca_live import AlpacaLiveBroker
        with self.assertRaises(RuntimeError):
            AlpacaLiveBroker()

    def test_keys_not_logged(self):
        """API keys must not appear in log output."""
        import logging
        from execution.broker_automation.alpaca_live import AlpacaLiveBroker

        log_records = []

        class Collector(logging.Handler):
            def emit(self, record):
                log_records.append(self.format(record))

        collector = Collector()
        from execution.broker_automation import alpaca_live as mod
        mod.logger.addHandler(collector)
        try:
            AlpacaLiveBroker()
        finally:
            mod.logger.removeHandler(collector)

        for record in log_records:
            self.assertNotIn("test-key", record, "API key must not appear in logs")
            self.assertNotIn("test-secret", record, "Secret key must not appear in logs")

    # ── F2: side validation ──────────────────────────────────────────────────

    def test_valid_buy_side_accepted(self):
        """'buy' is a valid side — must not error."""
        from execution.broker_automation.alpaca_live import AlpacaLiveBroker
        broker = AlpacaLiveBroker()
        result = broker.submit_market_order("SPY", 1, "buy")
        self.assertNotEqual(result.status, "error", f"Valid 'buy' order failed: {result.error}")

    def test_valid_sell_side_accepted(self):
        """'sell' is a valid side — must not error."""
        from execution.broker_automation.alpaca_live import AlpacaLiveBroker
        broker = AlpacaLiveBroker()
        result = broker.submit_market_order("SPY", 1, "sell")
        self.assertNotEqual(result.status, "error", f"Valid 'sell' order failed: {result.error}")

    def test_invalid_side_rejected(self):
        """Invalid side must raise ValueError — silent SELL coercion is exploitable."""
        from execution.broker_automation.alpaca_live import AlpacaLiveBroker
        broker = AlpacaLiveBroker()
        with self.assertRaises((ValueError, TypeError), msg="Invalid side 'long' must raise — not silently become SELL"):
            broker.submit_market_order("SPY", 1, "long")  # type: ignore[arg-type]

    def test_bracket_order_invalid_side_rejected(self):
        """Bracket order must also reject invalid side."""
        from execution.broker_automation.alpaca_live import AlpacaLiveBroker
        broker = AlpacaLiveBroker()
        with self.assertRaises((ValueError, TypeError)):
            broker.submit_bracket_order("SPY", 1, "long", stop_price=390.0, target_price=410.0)  # type: ignore[arg-type]

    # ── F3: qty range validation ─────────────────────────────────────────────

    def test_zero_qty_rejected(self):
        """qty=0 must raise ValueError — zero-share orders are malformed."""
        from execution.broker_automation.alpaca_live import AlpacaLiveBroker
        broker = AlpacaLiveBroker()
        with self.assertRaises(ValueError, msg="qty=0 must raise ValueError"):
            broker.submit_market_order("SPY", 0, "buy")

    def test_negative_qty_rejected(self):
        """qty=-1 must raise ValueError — negative shares are nonsense."""
        from execution.broker_automation.alpaca_live import AlpacaLiveBroker
        broker = AlpacaLiveBroker()
        with self.assertRaises(ValueError, msg="qty=-1 must raise ValueError"):
            broker.submit_market_order("SPY", -1, "buy")

    def test_bracket_zero_qty_rejected(self):
        """Bracket order qty=0 must raise ValueError."""
        from execution.broker_automation.alpaca_live import AlpacaLiveBroker
        broker = AlpacaLiveBroker()
        with self.assertRaises(ValueError):
            broker.submit_bracket_order("SPY", 0, "buy", stop_price=390.0, target_price=410.0)

    # ── Regression: existing happy-path behaviour preserved ──────────────────

    def test_get_account_returns_expected_keys(self):
        """get_account() must return dict with required keys."""
        from execution.broker_automation.alpaca_live import AlpacaLiveBroker
        broker = AlpacaLiveBroker()
        acct = broker.get_account()
        for key in ("id", "equity", "cash", "buying_power", "pattern_day_trader", "trading_blocked"):
            self.assertIn(key, acct, f"Missing key in get_account(): {key}")

    def test_bracket_order_happy_path(self):
        """Bracket order with valid inputs must succeed."""
        from execution.broker_automation.alpaca_live import AlpacaLiveBroker
        broker = AlpacaLiveBroker()
        result = broker.submit_bracket_order(
            symbol="SPY", qty=10, side="buy", stop_price=400.0, target_price=420.0
        )
        self.assertNotEqual(result.status, "error", f"Bracket order failed: {result.error}")
        self.assertEqual(result.symbol, "SPY")
        self.assertEqual(result.qty, 10)


    # ── F4: symbol input validation ──────────────────────────────────────────

    def test_symbol_validation_rejects_null_byte_injection(self):
        """Symbol with null byte must raise ValueError — defense-in-depth before SDK call."""
        from execution.broker_automation.alpaca_live import AlpacaLiveBroker
        broker = AlpacaLiveBroker.__new__(AlpacaLiveBroker)
        with self.assertRaisesRegex(ValueError, "rejected"):
            broker.submit_market_order("SPY\x00evil", 1, "buy")

    def test_symbol_validation_rejects_lowercase(self):
        """Lowercase symbols must raise ValueError."""
        from execution.broker_automation.alpaca_live import AlpacaLiveBroker
        broker = AlpacaLiveBroker.__new__(AlpacaLiveBroker)
        with self.assertRaisesRegex(ValueError, "rejected"):
            broker.submit_market_order("spy", 1, "buy")

    def test_symbol_validation_rejects_empty(self):
        """Empty symbol must raise ValueError."""
        from execution.broker_automation.alpaca_live import AlpacaLiveBroker
        broker = AlpacaLiveBroker.__new__(AlpacaLiveBroker)
        with self.assertRaisesRegex(ValueError, "rejected"):
            broker.submit_market_order("", 1, "buy")

    def test_symbol_validation_accepts_valid(self):
        """Valid uppercase symbols must pass validation."""
        from execution.broker_automation.alpaca_live import AlpacaLiveBroker
        broker = AlpacaLiveBroker()
        result = broker.submit_market_order("SPY", 1, "buy")
        self.assertNotEqual(result.status, "error", f"Valid symbol 'SPY' failed: {result.error}")

    def test_bracket_symbol_validation_rejects_injection(self):
        """Bracket order must also reject symbol injection."""
        from execution.broker_automation.alpaca_live import AlpacaLiveBroker
        broker = AlpacaLiveBroker.__new__(AlpacaLiveBroker)
        with self.assertRaisesRegex(ValueError, "rejected"):
            broker.submit_bracket_order("SPY;rm -rf /", 1, "buy", stop_price=390.0, target_price=410.0)


if __name__ == "__main__":
    unittest.main()
