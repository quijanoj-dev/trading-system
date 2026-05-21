"""Tests for execution/risk_manager.py"""

import unittest
from datetime import date

from execution.risk_manager import (
    RiskConfig,
    RiskManager,
    PositionSizer,
    RiskController,
)

EQUITY = 50_000.0  # $50k account (typical Apex 50k eval)


class TestRiskConfig(unittest.TestCase):
    def test_defaults_valid(self) -> None:
        cfg = RiskConfig()
        self.assertEqual(cfg.risk_per_trade_pct, 1.0)
        self.assertEqual(cfg.daily_loss_limit_pct, 2.0)
        self.assertEqual(cfg.max_drawdown_pct, 5.0)

    def test_invalid_risk_pct_raises(self) -> None:
        with self.assertRaises(AssertionError):
            RiskConfig(risk_per_trade_pct=0)
        with self.assertRaises(AssertionError):
            RiskConfig(risk_per_trade_pct=6)


class TestPositionSizer(unittest.TestCase):
    def setUp(self) -> None:
        self.cfg = RiskConfig(risk_per_trade_pct=1.0, point_value=50.0, tick_size=0.25)
        self.sizer = PositionSizer(self.cfg)

    def test_basic_sizing(self) -> None:
        # 1% of $50k = $500 risk
        # ES: stop 2pts away = $100/contract → 5 contracts
        result = self.sizer.size(EQUITY, entry_price=5000.0, stop_price=4998.0)
        self.assertTrue(result.approved)
        self.assertEqual(result.contracts, 5)
        self.assertAlmostEqual(result.dollar_risk, 500.0)
        self.assertAlmostEqual(result.stop_distance_pts, 2.0)

    def test_tight_stop_rounds_to_one(self) -> None:
        # Stop distance > 10 pts → risk_per_contract > dollar_risk_target → raw < 1 → floor to 1
        # 1% of $50k = $500; 10.25pts × $50/pt = $512.50/contract → raw = 0.97 → floor=0 → max(1,0)=1
        result = self.sizer.size(EQUITY, entry_price=5000.0, stop_price=4989.75)
        self.assertTrue(result.approved)
        self.assertEqual(result.contracts, 1)

    def test_max_position_cap(self) -> None:
        cfg = RiskConfig(risk_per_trade_pct=5.0, max_position_size=3, point_value=50.0)
        sizer = PositionSizer(cfg)
        # 5% of $50k = $2500, stop 1pt = $50/contract → raw=50, capped at 3
        result = sizer.size(EQUITY, entry_price=5000.0, stop_price=4999.0)
        self.assertEqual(result.contracts, 3)

    def test_stop_below_tick_size_rejected(self) -> None:
        result = self.sizer.size(EQUITY, entry_price=5000.0, stop_price=4999.999)
        self.assertFalse(result.approved)
        self.assertIn("tick_size", result.rejection_reason)

    def test_zero_equity_rejected(self) -> None:
        result = self.sizer.size(0.0, entry_price=5000.0, stop_price=4998.0)
        self.assertFalse(result.approved)
        self.assertIn("account_equity", result.rejection_reason)

    def test_short_trade_sizing(self) -> None:
        # Short: entry < stop (stop is above entry)
        result = self.sizer.size(EQUITY, entry_price=4998.0, stop_price=5000.0)
        self.assertTrue(result.approved)
        self.assertAlmostEqual(result.stop_distance_pts, 2.0)
        self.assertEqual(result.contracts, 5)


class TestRiskController(unittest.TestCase):
    def setUp(self) -> None:
        self.cfg = RiskConfig(daily_loss_limit_pct=2.0, max_drawdown_pct=5.0)
        self.rc = RiskController(self.cfg)

    def _start(self, equity: float = EQUITY) -> None:
        self.rc.start_session(equity, trading_date=date(2026, 3, 29))

    def test_trade_allowed_after_session_start(self) -> None:
        self._start()
        allowed, reason = self.rc.check_trade_allowed()
        self.assertTrue(allowed)
        self.assertEqual(reason, "")

    def test_no_session_blocks_trade(self) -> None:
        allowed, reason = self.rc.check_trade_allowed()
        self.assertFalse(allowed)
        self.assertIn("No active session", reason)

    def test_daily_loss_limit_triggers_halt(self) -> None:
        self._start()
        # 2% of $50k = $1000 daily limit
        self.rc.record_pnl(-1000.0)  # exactly at limit
        self.assertTrue(self.rc.is_halted)
        allowed, reason = self.rc.check_trade_allowed()
        self.assertFalse(allowed)
        self.assertIn("Daily loss limit", reason)

    def test_daily_loss_partial_does_not_halt(self) -> None:
        self._start()
        self.rc.record_pnl(-999.99)
        self.assertFalse(self.rc.is_halted)

    def test_max_drawdown_triggers_halt(self) -> None:
        self._start()
        # 5% of $50k peak = $2500
        self.rc.update_unrealized_equity(EQUITY - 2500.0)
        self.assertTrue(self.rc.is_halted)

    def test_max_drawdown_updates_peak(self) -> None:
        self._start()
        # Profit raises peak, then drawdown from new peak
        self.rc.record_pnl(1000.0)   # peak → $51k
        self.rc.record_pnl(-2550.0)  # drawdown 5% of $51k = $2550
        self.assertTrue(self.rc.is_halted)

    def test_profitable_day_no_halt(self) -> None:
        self._start()
        self.rc.record_pnl(500.0)
        self.rc.record_pnl(300.0)
        self.assertFalse(self.rc.is_halted)

    def test_end_session_returns_state(self) -> None:
        self._start()
        self.rc.record_pnl(-200.0)
        state = self.rc.end_session()
        self.assertIsNotNone(state)
        self.assertAlmostEqual(state.realized_pnl, -200.0)
        self.assertEqual(state.trade_count, 1)
        self.assertIsNone(self.rc.session)

    def test_status_dict_fields(self) -> None:
        self._start()
        self.rc.record_pnl(-300.0)
        s = self.rc.status_dict()
        self.assertTrue(s["active_session"])
        self.assertAlmostEqual(s["realized_pnl"], -300.0)
        self.assertIn("daily_loss_remaining_usd", s)
        self.assertIn("drawdown_remaining_usd", s)

    def test_halted_session_remains_halted(self) -> None:
        self._start()
        self.rc.record_pnl(-1001.0)
        self.assertTrue(self.rc.is_halted)
        # Profit does not unblock
        self.rc.record_pnl(5000.0)
        self.assertTrue(self.rc.is_halted)


class TestRiskManagerFacade(unittest.TestCase):
    def test_full_trade_flow(self) -> None:
        rm = RiskManager(RiskConfig(risk_per_trade_pct=1.0, daily_loss_limit_pct=2.0))
        rm.start_session(EQUITY, trading_date=date(2026, 3, 29))

        trade = rm.size_position(EQUITY, entry_price=5000.0, stop_price=4998.0)
        self.assertTrue(trade.approved)
        self.assertEqual(trade.contracts, 5)

        allowed, _ = rm.check_trade_allowed()
        self.assertTrue(allowed)

        rm.record_pnl(250.0)  # winning trade
        self.assertFalse(rm.is_halted)

        rm.record_pnl(-1251.0)  # net: -1001 → exceeds $1000 daily limit
        self.assertTrue(rm.is_halted)

        state = rm.end_session()
        self.assertIsNotNone(state)
        self.assertAlmostEqual(state.realized_pnl, -1001.0)


if __name__ == "__main__":
    unittest.main()
