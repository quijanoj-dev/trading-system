"""Tests for execution/backtester.py"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

import pandas as pd

from execution.backtester import (
    BacktestConfig,
    Backtester,
    Signal,
)
from execution.risk_manager import RiskConfig

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ohlcv(bars: list[tuple]) -> pd.DataFrame:
    """Build a minimal OHLCV DataFrame from (timestamp, open, high, low, close) tuples."""
    timestamps = [pd.Timestamp(b[0]) for b in bars]
    df = pd.DataFrame(
        {
            "open":  [b[1] for b in bars],
            "high":  [b[2] for b in bars],
            "low":   [b[3] for b in bars],
            "close": [b[4] for b in bars],
        },
        index=pd.DatetimeIndex(timestamps),
    )
    return df


def _default_config() -> BacktestConfig:
    return BacktestConfig(
        initial_equity=50_000.0,
        risk_config=RiskConfig(
            risk_per_trade_pct=1.0,
            max_position_size=10,
            point_value=50.0,
            tick_size=0.25,
        ),
        slippage_ticks=0.0,
        commission_per_contract=0.0,
    )


# ---------------------------------------------------------------------------
# OHLCV validation
# ---------------------------------------------------------------------------

class TestOHLCVValidation(unittest.TestCase):
    def test_missing_column_raises(self) -> None:
        df = pd.DataFrame({"open": [1.0], "high": [1.0], "low": [1.0]},
                          index=pd.DatetimeIndex([pd.Timestamp("2024-01-01")]))
        bt = Backtester(_default_config())
        with self.assertRaises(ValueError):
            bt.run([], df)

    def test_non_datetime_index_raises(self) -> None:
        df = pd.DataFrame({"open": [1.0], "high": [1.0], "low": [1.0], "close": [1.0]},
                          index=[0])
        bt = Backtester(_default_config())
        with self.assertRaises(TypeError):
            bt.run([], df)

    def test_unsorted_index_raises(self) -> None:
        df = _make_ohlcv([
            ("2024-01-02", 5000, 5010, 4990, 5005),
            ("2024-01-01", 5000, 5010, 4990, 5005),
        ])
        bt = Backtester(_default_config())
        with self.assertRaises(ValueError):
            bt.run([], df)


# ---------------------------------------------------------------------------
# Empty and edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases(unittest.TestCase):
    def _ohlcv(self) -> pd.DataFrame:
        return _make_ohlcv([
            ("2024-01-01 09:30", 5000, 5020, 4980, 5010),
            ("2024-01-01 09:31", 5010, 5030, 5000, 5015),
        ])

    def test_no_signals_returns_zero_metrics(self) -> None:
        bt = Backtester(_default_config())
        result = bt.run([], self._ohlcv())
        self.assertEqual(result.metrics.total_trades, 0)
        self.assertEqual(result.metrics.net_pnl, 0.0)

    def test_result_has_equity_series(self) -> None:
        bt = Backtester(_default_config())
        result = bt.run([], self._ohlcv())
        series = result.equity_series()
        self.assertIsInstance(series, pd.Series)
        self.assertEqual(len(series), 0)


# ---------------------------------------------------------------------------
# Winning trade — long
# ---------------------------------------------------------------------------

class TestLongWin(unittest.TestCase):
    def setUp(self) -> None:
        # Entry bar + 3 subsequent bars.
        # Target at 5010; Stop at 4990; entry at 5000.
        # Bar 1 after entry: high=5005, low=4995 → no fill
        # Bar 2 after entry: high=5012, low=4998 → target hit at 5010
        self.ohlcv = _make_ohlcv([
            ("2024-01-01 09:30", 5000, 5005, 4995, 5002),  # entry bar
            ("2024-01-01 09:31", 5002, 5005, 4995, 5004),  # no fill
            ("2024-01-01 09:32", 5004, 5012, 4998, 5010),  # target hit
            ("2024-01-01 09:33", 5010, 5015, 5008, 5012),
        ])
        self.signal = Signal(
            timestamp=pd.Timestamp("2024-01-01 09:30"),
            direction="long",
            entry_price=5000.0,
            stop_price=4990.0,
            target_price=5010.0,
        )
        self.cfg = _default_config()

    def test_outcome_win(self) -> None:
        bt = Backtester(self.cfg)
        result = bt.run([self.signal], self.ohlcv)
        self.assertEqual(len(result.trades), 1)
        self.assertEqual(result.trades[0].outcome, "win")

    def test_exit_price_is_target(self) -> None:
        bt = Backtester(self.cfg)
        result = bt.run([self.signal], self.ohlcv)
        self.assertAlmostEqual(result.trades[0].exit_price, 5010.0)

    def test_pnl_points_correct(self) -> None:
        bt = Backtester(self.cfg)
        result = bt.run([self.signal], self.ohlcv)
        # 10pts long
        self.assertAlmostEqual(result.trades[0].pnl_points, 10.0)

    def test_pnl_dollars_correct(self) -> None:
        # 1% of $50k = $500; stop 10pts → $500/contract → 1 contract
        # P&L = 10pts * $50 * 1 contract = $500 (no commission)
        bt = Backtester(self.cfg)
        result = bt.run([self.signal], self.ohlcv)
        self.assertAlmostEqual(result.trades[0].pnl_dollars, 500.0)

    def test_equity_increases(self) -> None:
        bt = Backtester(self.cfg)
        result = bt.run([self.signal], self.ohlcv)
        self.assertGreater(result.equity_curve[-1], self.cfg.initial_equity)


# ---------------------------------------------------------------------------
# Losing trade — long
# ---------------------------------------------------------------------------

class TestLongLoss(unittest.TestCase):
    def setUp(self) -> None:
        # Target at 5010; Stop at 4990; entry at 5000.
        # Bar 1: high=5005, low=4989 → stop hit at 4990
        self.ohlcv = _make_ohlcv([
            ("2024-01-01 09:30", 5000, 5005, 4995, 5002),
            ("2024-01-01 09:31", 5002, 5005, 4989, 4992),
            ("2024-01-01 09:32", 4992, 4995, 4988, 4990),
        ])
        self.signal = Signal(
            timestamp=pd.Timestamp("2024-01-01 09:30"),
            direction="long",
            entry_price=5000.0,
            stop_price=4990.0,
            target_price=5010.0,
        )
        self.cfg = _default_config()

    def test_outcome_loss(self) -> None:
        bt = Backtester(self.cfg)
        result = bt.run([self.signal], self.ohlcv)
        self.assertEqual(result.trades[0].outcome, "loss")

    def test_exit_price_is_stop(self) -> None:
        bt = Backtester(self.cfg)
        result = bt.run([self.signal], self.ohlcv)
        self.assertAlmostEqual(result.trades[0].exit_price, 4990.0)

    def test_pnl_negative(self) -> None:
        bt = Backtester(self.cfg)
        result = bt.run([self.signal], self.ohlcv)
        self.assertLess(result.trades[0].pnl_dollars, 0)


# ---------------------------------------------------------------------------
# Short trade
# ---------------------------------------------------------------------------

class TestShortWin(unittest.TestCase):
    def setUp(self) -> None:
        # Short: entry at 5000, stop at 5010, target at 4990.
        # Bar 1: high=5005, low=4988 → target hit at 4990
        self.ohlcv = _make_ohlcv([
            ("2024-01-01 09:30", 5000, 5005, 4995, 5002),
            ("2024-01-01 09:31", 5002, 5005, 4988, 4992),
        ])
        self.signal = Signal(
            timestamp=pd.Timestamp("2024-01-01 09:30"),
            direction="short",
            entry_price=5000.0,
            stop_price=5010.0,
            target_price=4990.0,
        )
        self.cfg = _default_config()

    def test_outcome_win(self) -> None:
        bt = Backtester(self.cfg)
        result = bt.run([self.signal], self.ohlcv)
        self.assertEqual(result.trades[0].outcome, "win")

    def test_pnl_points(self) -> None:
        bt = Backtester(self.cfg)
        result = bt.run([self.signal], self.ohlcv)
        # Short 10pts = entry - exit = 5000 - 4990
        self.assertAlmostEqual(result.trades[0].pnl_points, 10.0)


# ---------------------------------------------------------------------------
# Conservative stop on same-bar both-levels hit
# ---------------------------------------------------------------------------

class TestConservativeStop(unittest.TestCase):
    def test_both_levels_hit_same_bar_uses_stop(self) -> None:
        # Both stop (4990) and target (5010) inside single bar's range
        ohlcv = _make_ohlcv([
            ("2024-01-01 09:30", 5000, 5005, 4995, 5002),
            ("2024-01-01 09:31", 5000, 5015, 4985, 4998),  # range covers both levels
        ])
        signal = Signal(
            timestamp=pd.Timestamp("2024-01-01 09:30"),
            direction="long",
            entry_price=5000.0,
            stop_price=4990.0,
            target_price=5010.0,
        )
        bt = Backtester(_default_config())
        result = bt.run([signal], ohlcv)
        self.assertEqual(result.trades[0].outcome, "loss")


# ---------------------------------------------------------------------------
# Force-close when max_holding_bars reached
# ---------------------------------------------------------------------------

class TestForceClose(unittest.TestCase):
    def test_open_outcome_when_neither_level_hit(self) -> None:
        # Only 2 bars after entry, neither hits stop nor target
        ohlcv = _make_ohlcv([
            ("2024-01-01 09:30", 5000, 5005, 4995, 5002),
            ("2024-01-01 09:31", 5002, 5003, 4998, 5001),
            ("2024-01-01 09:32", 5001, 5003, 4999, 5002),
        ])
        signal = Signal(
            timestamp=pd.Timestamp("2024-01-01 09:30"),
            direction="long",
            entry_price=5000.0,
            stop_price=4960.0,   # very far stop
            target_price=5040.0, # very far target
        )
        cfg = BacktestConfig(
            initial_equity=50_000.0,
            risk_config=RiskConfig(point_value=50.0, tick_size=0.25),
            max_holding_bars=2,
            slippage_ticks=0.0,
            commission_per_contract=0.0,
        )
        bt = Backtester(cfg)
        result = bt.run([signal], ohlcv)
        self.assertEqual(result.trades[0].outcome, "open")


# ---------------------------------------------------------------------------
# Slippage
# ---------------------------------------------------------------------------

class TestSlippage(unittest.TestCase):
    def test_slippage_reduces_long_pnl(self) -> None:
        # With slippage, entry is worse (higher for long)
        ohlcv = _make_ohlcv([
            ("2024-01-01 09:30", 5000, 5005, 4995, 5002),
            ("2024-01-01 09:31", 5002, 5020, 4998, 5015),  # target hit at 5010
        ])
        signal = Signal(
            timestamp=pd.Timestamp("2024-01-01 09:30"),
            direction="long",
            entry_price=5000.0,
            stop_price=4990.0,
            target_price=5010.0,
        )
        cfg_no_slip = BacktestConfig(
            initial_equity=50_000.0,
            risk_config=RiskConfig(point_value=50.0, tick_size=0.25),
            slippage_ticks=0.0,
            commission_per_contract=0.0,
        )
        cfg_slip = BacktestConfig(
            initial_equity=50_000.0,
            risk_config=RiskConfig(point_value=50.0, tick_size=0.25),
            slippage_ticks=2.0,   # 2 ticks = 0.5 pts
            commission_per_contract=0.0,
        )
        bt_no = Backtester(cfg_no_slip)
        bt_sl = Backtester(cfg_slip)
        r_no = bt_no.run([signal], ohlcv)
        r_sl = bt_sl.run([signal], ohlcv)
        self.assertGreater(r_no.trades[0].pnl_dollars, r_sl.trades[0].pnl_dollars)


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

class TestMetrics(unittest.TestCase):
    def _run_three_trade_backtest(self) -> "BacktestResult":  # noqa: F821
        """2 wins + 1 loss across a simple data set."""
        ohlcv = _make_ohlcv([
            ("2024-01-01 09:30", 5000, 5005, 4995, 5002),
            ("2024-01-01 09:31", 5002, 5015, 4998, 5012),  # target 5010 hit (W1)
            ("2024-01-01 09:32", 5012, 5005, 4985, 4990),  # entry bar W2 / L1
            ("2024-01-01 09:33", 4990, 5025, 4980, 5000),  # target 5020 hit (W2)
            ("2024-01-01 09:34", 5000, 5005, 4960, 4980),  # stop 4980 hit (L1)
            ("2024-01-01 09:35", 4980, 4985, 4970, 4975),
        ])
        signals = [
            Signal(
                timestamp=pd.Timestamp("2024-01-01 09:30"),
                direction="long",
                entry_price=5000.0,
                stop_price=4990.0,
                target_price=5010.0,
            ),
            Signal(
                timestamp=pd.Timestamp("2024-01-01 09:32"),
                direction="long",
                entry_price=5012.0,
                stop_price=4992.0,
                target_price=5032.0,
            ),
            Signal(
                timestamp=pd.Timestamp("2024-01-01 09:33"),
                direction="long",
                entry_price=4990.0,
                stop_price=4970.0,
                target_price=5010.0,
            ),
        ]
        cfg = BacktestConfig(
            initial_equity=50_000.0,
            risk_config=RiskConfig(
                risk_per_trade_pct=1.0,
                max_position_size=10,
                point_value=50.0,
                tick_size=0.25,
            ),
            slippage_ticks=0.0,
            commission_per_contract=0.0,
        )
        return Backtester(cfg).run(signals, ohlcv)

    def test_total_trades(self) -> None:
        r = self._run_three_trade_backtest()
        self.assertEqual(r.metrics.total_trades, 3)

    def test_win_rate_range(self) -> None:
        r = self._run_three_trade_backtest()
        self.assertGreaterEqual(r.metrics.win_rate, 0.0)
        self.assertLessEqual(r.metrics.win_rate, 1.0)

    def test_profit_factor_positive(self) -> None:
        r = self._run_three_trade_backtest()
        self.assertGreater(r.metrics.profit_factor, 0.0)

    def test_max_drawdown_non_negative(self) -> None:
        r = self._run_three_trade_backtest()
        self.assertGreaterEqual(r.metrics.max_drawdown_pct, 0.0)
        self.assertGreaterEqual(r.metrics.max_drawdown_dollars, 0.0)

    def test_equity_curve_length_matches_trades(self) -> None:
        r = self._run_three_trade_backtest()
        self.assertEqual(len(r.equity_curve), r.metrics.total_trades)

    def test_summary_returns_string(self) -> None:
        r = self._run_three_trade_backtest()
        summary = r.summary()
        self.assertIn("Win Rate", summary)
        self.assertIn("Sharpe", summary)
        self.assertIn("Max Drawdown", summary)


# ---------------------------------------------------------------------------
# Commission impact
# ---------------------------------------------------------------------------

class TestCommission(unittest.TestCase):
    def test_commission_reduces_net_pnl(self) -> None:
        ohlcv = _make_ohlcv([
            ("2024-01-01 09:30", 5000, 5005, 4995, 5002),
            ("2024-01-01 09:31", 5002, 5015, 4998, 5012),
        ])
        signal = Signal(
            timestamp=pd.Timestamp("2024-01-01 09:30"),
            direction="long",
            entry_price=5000.0,
            stop_price=4990.0,
            target_price=5010.0,
        )
        cfg_free = BacktestConfig(
            initial_equity=50_000.0,
            risk_config=RiskConfig(point_value=50.0, tick_size=0.25),
            slippage_ticks=0.0,
            commission_per_contract=0.0,
        )
        cfg_comm = BacktestConfig(
            initial_equity=50_000.0,
            risk_config=RiskConfig(point_value=50.0, tick_size=0.25),
            slippage_ticks=0.0,
            commission_per_contract=3.50,
        )
        r_free = Backtester(cfg_free).run([signal], ohlcv)
        r_comm = Backtester(cfg_comm).run([signal], ohlcv)
        self.assertGreater(r_free.metrics.net_pnl, r_comm.metrics.net_pnl)


if __name__ == "__main__":
    unittest.main()
