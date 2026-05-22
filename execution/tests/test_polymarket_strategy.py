"""Tests for execution/polymarket/strategy.py — pure logic, no HTTP."""
from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from execution.polymarket.connector import PolymarketMarket
from execution.polymarket.strategy import (
    LiquidityMispricingStrategy,
    PolymarketSignal,
    ResolutionAmbiguityStrategy,
    _kelly,
)


def _future_date(days: int) -> str:
    dt = datetime.now(timezone.utc) + timedelta(days=days)
    return dt.isoformat()


def _market(
    *,
    active: bool = True,
    volume: float = 10_000,
    yes_price: float = 0.5,
    no_price: float = 0.5,
    spread: float = 0.0,
    question: str = "Will X happen?",
    end_days: int = 14,
) -> PolymarketMarket:
    return PolymarketMarket(
        market_id="test-id",
        question=question,
        description="",
        yes_price=yes_price,
        no_price=no_price,
        volume=volume,
        end_date=_future_date(end_days),
        spread=spread,
        active=active,
    )


def _signal(kelly_fraction: float = 0.4) -> PolymarketSignal:
    return PolymarketSignal(
        market=_market(),
        direction="YES",
        estimated_prob=0.7,
        market_price=0.5,
        edge=0.2,
        confidence=0.8,
        rationale="test",
        kelly_fraction=kelly_fraction,
    )


class TestKelly(unittest.TestCase):
    def test_zero_edge_returns_zero(self):
        self.assertEqual(_kelly(0.5, 0.5), 0.0)

    def test_price_zero_returns_zero(self):
        self.assertEqual(_kelly(0.7, 0.0), 0.0)

    def test_price_one_returns_zero(self):
        self.assertEqual(_kelly(0.7, 1.0), 0.0)

    def test_positive_edge(self):
        self.assertGreater(_kelly(0.7, 0.5), 0.0)

    def test_negative_edge_clamped_to_zero(self):
        self.assertEqual(_kelly(0.3, 0.8), 0.0)

    def test_known_value(self):
        # p=0.6, price=0.4 → b=(1-0.4)/0.4=1.5, q=0.4, k=(0.6*1.5-0.4)/1.5=0.333
        k = _kelly(0.6, 0.4)
        self.assertAlmostEqual(k, (0.6 * 1.5 - 0.4) / 1.5, places=6)


class TestFractionalKelly(unittest.TestCase):
    def test_default_fraction_is_quarter(self):
        self.assertAlmostEqual(_signal(0.4).fractional_kelly(), 0.1)

    def test_custom_fraction(self):
        self.assertAlmostEqual(_signal(0.4).fractional_kelly(0.5), 0.2)

    def test_zero_kelly(self):
        self.assertEqual(_signal(0.0).fractional_kelly(), 0.0)

    def test_fraction_parameter_actually_used(self):
        sig = _signal(1.0)
        self.assertNotEqual(sig.fractional_kelly(0.1), sig.fractional_kelly(0.5))


class TestResolutionAmbiguityStrategy(unittest.TestCase):
    def setUp(self):
        self.s = ResolutionAmbiguityStrategy()

    # --- is_eligible ---

    def test_eligible_normal(self):
        self.assertTrue(self.s.is_eligible(_market(volume=5_001, end_days=14)))

    def test_ineligible_inactive(self):
        self.assertFalse(self.s.is_eligible(_market(active=False, volume=5_001, end_days=14)))

    def test_ineligible_low_volume(self):
        self.assertFalse(self.s.is_eligible(_market(volume=4_999, end_days=14)))

    def test_ineligible_expires_too_soon(self):
        self.assertFalse(self.s.is_eligible(_market(volume=5_001, end_days=1)))

    def test_ineligible_expires_too_far(self):
        self.assertFalse(self.s.is_eligible(_market(volume=5_001, end_days=90)))

    # --- analyze ---

    def test_no_signal_non_ambiguous_question(self):
        m = _market(question="Will the Fed cut rates?", yes_price=0.92, no_price=0.08)
        self.assertIsNone(self.s.analyze(m))

    def test_no_signal_yes_price_below_threshold(self):
        m = _market(question="Will it probably happen?", yes_price=0.70, no_price=0.30)
        self.assertIsNone(self.s.analyze(m))

    def test_signal_for_ambiguous_near_certain_market(self):
        m = _market(
            question="Will it probably reach a major milestone?",
            yes_price=0.90,
            no_price=0.10,
        )
        sig = self.s.analyze(m)
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, "NO")
        self.assertGreater(sig.edge, 0.0)
        self.assertGreater(sig.kelly_fraction, 0.0)

    def test_no_signal_when_edge_below_minimum(self):
        # estimated_no_prob=0.20, no_price=0.16 → edge=0.04 < 0.05
        m = _market(
            question="Will it probably reach a significant milestone?",
            yes_price=0.86,
            no_price=0.16,
        )
        self.assertIsNone(self.s.analyze(m))

    def test_signal_has_correct_market_reference(self):
        m = _market(
            question="Will it likely happen before or by the deadline?",
            yes_price=0.92,
            no_price=0.08,
        )
        sig = self.s.analyze(m)
        self.assertIsNotNone(sig)
        self.assertIs(sig.market, m)


class TestLiquidityMispricingStrategy(unittest.TestCase):
    def setUp(self):
        self.s = LiquidityMispricingStrategy()

    # --- is_eligible ---

    def test_eligible_high_volume(self):
        self.assertTrue(self.s.is_eligible(_market(volume=50_001)))

    def test_ineligible_low_volume(self):
        self.assertFalse(self.s.is_eligible(_market(volume=49_999)))

    def test_ineligible_inactive(self):
        self.assertFalse(self.s.is_eligible(_market(volume=60_000, active=False)))

    # --- analyze ---

    def test_no_signal_small_spread(self):
        m = _market(volume=60_000, spread=0.02)
        self.assertIsNone(self.s.analyze(m))

    def test_buys_yes_when_cheaper(self):
        m = _market(volume=60_000, yes_price=0.40, no_price=0.56, spread=0.16)
        sig = self.s.analyze(m)
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, "YES")
        self.assertAlmostEqual(sig.market_price, 0.40)

    def test_buys_no_when_cheaper(self):
        m = _market(volume=60_000, yes_price=0.62, no_price=0.33, spread=0.29)
        sig = self.s.analyze(m)
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, "NO")
        self.assertAlmostEqual(sig.market_price, 0.33)

    def test_no_signal_when_edge_too_small(self):
        # yes_price=0.48, no_price=0.55, spread=0.07
        # YES is cheaper → estimated_prob=1-0.55=0.45, edge=0.45-0.48=-0.03 → None
        m = _market(volume=60_000, yes_price=0.48, no_price=0.55, spread=0.07)
        self.assertIsNone(self.s.analyze(m))

    def test_signal_edge_is_positive(self):
        m = _market(volume=60_000, yes_price=0.38, no_price=0.58, spread=0.20)
        sig = self.s.analyze(m)
        self.assertIsNotNone(sig)
        self.assertGreater(sig.edge, 0.0)


if __name__ == "__main__":
    unittest.main()
