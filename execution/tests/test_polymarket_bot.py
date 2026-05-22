"""Tests for execution/polymarket/bot.py — mocks connector and strategies."""
from __future__ import annotations

import sys
import unittest
from unittest.mock import MagicMock, patch

# Inject fake py_clob_client before any connector import
_fake_clob = MagicMock()
for _mod in ("py_clob_client", "py_clob_client.client", "py_clob_client.clob_types"):
    sys.modules.setdefault(_mod, _fake_clob)

from execution.polymarket.connector import PolymarketMarket
from execution.polymarket.strategy import PolymarketSignal
from execution.polymarket.bot import ACCOUNT_VALUE, format_signal, scan_markets


def _market(market_id: str = "m1", question: str = "Will X happen?") -> PolymarketMarket:
    return PolymarketMarket(
        market_id=market_id,
        question=question,
        description="",
        yes_price=0.60,
        no_price=0.40,
        volume=50_000,
        end_date="2026-08-01T00:00:00Z",
        spread=0.0,
        active=True,
    )


def _signal(market: PolymarketMarket, edge: float = 0.10, kelly: float = 0.20) -> PolymarketSignal:
    return PolymarketSignal(
        market=market,
        direction="YES",
        estimated_prob=0.70,
        market_price=0.60,
        edge=edge,
        confidence=0.8,
        rationale="Test signal",
        kelly_fraction=kelly,
    )


class TestScanMarkets(unittest.TestCase):
    def _strategy(self, eligible: bool = True, signal=None):
        s = MagicMock()
        s.is_eligible.return_value = eligible
        s.analyze.return_value = signal
        return s

    def test_returns_signal_above_threshold(self):
        m = _market()
        connector = MagicMock()
        connector.get_markets.return_value = [m]
        strategy = self._strategy(signal=_signal(m, edge=0.10))
        signals = scan_markets(connector, [strategy])
        self.assertEqual(len(signals), 1)

    def test_filters_signal_below_threshold(self):
        m = _market()
        connector = MagicMock()
        connector.get_markets.return_value = [m]
        strategy = self._strategy(signal=_signal(m, edge=0.02))
        signals = scan_markets(connector, [strategy])
        self.assertEqual(len(signals), 0)

    def test_skips_ineligible_markets(self):
        m = _market()
        connector = MagicMock()
        connector.get_markets.return_value = [m]
        strategy = self._strategy(eligible=False)
        scan_markets(connector, [strategy])
        strategy.analyze.assert_not_called()

    def test_none_from_analyze_handled(self):
        m = _market()
        connector = MagicMock()
        connector.get_markets.return_value = [m]
        strategy = self._strategy(signal=None)
        signals = scan_markets(connector, [strategy])
        self.assertEqual(len(signals), 0)

    def test_sorts_by_edge_descending(self):
        markets = [_market(f"m{i}") for i in range(3)]
        connector = MagicMock()
        connector.get_markets.return_value = markets
        strategy = MagicMock()
        strategy.is_eligible.return_value = True
        strategy.analyze.side_effect = [
            _signal(markets[0], edge=0.08),
            _signal(markets[1], edge=0.15),
            _signal(markets[2], edge=0.06),
        ]
        signals = scan_markets(connector, [strategy])
        edges = [s.edge for s in signals]
        self.assertEqual(edges, sorted(edges, reverse=True))

    def test_multiple_strategies_on_same_market(self):
        m = _market()
        connector = MagicMock()
        connector.get_markets.return_value = [m]
        s1 = self._strategy(signal=_signal(m, edge=0.10))
        s2 = self._strategy(signal=_signal(m, edge=0.12))
        signals = scan_markets(connector, [s1, s2])
        self.assertEqual(len(signals), 2)

    def test_empty_markets_returns_empty(self):
        connector = MagicMock()
        connector.get_markets.return_value = []
        signals = scan_markets(connector, [self._strategy()])
        self.assertEqual(signals, [])


class TestFormatSignal(unittest.TestCase):
    def test_contains_market_question(self):
        m = _market(question="Will the election happen?")
        output = format_signal(_signal(m), ACCOUNT_VALUE)
        self.assertIn("Will the election happen?", output)

    def test_contains_direction(self):
        m = _market()
        output = format_signal(_signal(m), ACCOUNT_VALUE)
        self.assertIn("YES", output)

    def test_contains_edge(self):
        m = _market()
        sig = _signal(m, edge=0.10)
        output = format_signal(sig, ACCOUNT_VALUE)
        self.assertIn("0.100", output)

    def test_position_size_not_capped(self):
        m = _market()
        # kelly=0.04, fractional=0.01, size=0.01*10000=100 < 200 cap
        sig = _signal(m, kelly=0.04)
        output = format_signal(sig, ACCOUNT_VALUE)
        self.assertIn("$100.00", output)

    def test_position_size_capped_at_two_percent(self):
        m = _market()
        # kelly=10.0, fractional=2.5, 2.5*10000=25000 → capped at 0.02*10000=200
        sig = PolymarketSignal(
            market=m,
            direction="YES",
            estimated_prob=0.99,
            market_price=0.01,
            edge=0.98,
            confidence=1.0,
            rationale="extreme",
            kelly_fraction=10.0,
        )
        output = format_signal(sig, ACCOUNT_VALUE)
        self.assertIn("$200.00", output)

    def test_contains_size_label(self):
        output = format_signal(_signal(_market()), ACCOUNT_VALUE)
        self.assertIn("Size:", output)

    def test_contains_kelly_label(self):
        output = format_signal(_signal(_market()), ACCOUNT_VALUE)
        self.assertIn("Kelly:", output)


if __name__ == "__main__":
    unittest.main()
