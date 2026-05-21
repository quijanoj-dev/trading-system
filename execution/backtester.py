"""
Backtesting harness for Pine Script / discretionary strategies.

Usage:
    signals = [
        Signal(timestamp=..., direction="long", entry_price=5000.0,
               stop_price=4996.0, target_price=5012.0),
        ...
    ]
    ohlcv = pd.DataFrame(...)  # columns: open, high, low, close, volume; DatetimeIndex

    bt = Backtester(BacktestConfig(initial_equity=50_000))
    result = bt.run(signals, ohlcv)
    print(result.summary())

Signal resolution:
    For each signal the backtester scans forward candle-by-candle from the
    entry bar.  The trade is closed at whichever level is hit first — stop or
    target — using the candle's high/low range as the intra-bar proxy.

    If neither level is hit before the data ends the trade is closed at the
    last available close price (open position at end of data).
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional

import pandas as pd

from execution.risk_manager import RiskConfig, PositionSizer
from execution.market_data.interfaces import MarketDataFeed

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

Direction = Literal["long", "short"]


@dataclass
class Signal:
    """A single trade signal to be evaluated by the backtester."""

    timestamp: pd.Timestamp          # Bar at which the trade is taken
    direction: Direction             # "long" or "short"
    entry_price: float               # Fill price
    stop_price: float                # Invalidation / stop-loss level
    target_price: float              # Take-profit level
    label: str = ""                  # Optional tag (e.g. strategy name, setup type)


@dataclass
class Trade:
    """Completed (or force-closed) trade record."""

    signal: Signal
    contracts: int
    exit_price: float
    exit_timestamp: pd.Timestamp
    outcome: Literal["win", "loss", "breakeven", "open"]
    pnl_points: float                # Net points (after slippage, before commission)
    pnl_dollars: float               # Dollar P&L after commission
    equity_after: float              # Account equity after this trade closes


@dataclass
class BacktestConfig:
    """Configuration for a single backtest run."""

    initial_equity: float = 50_000.0
    risk_config: RiskConfig = field(default_factory=RiskConfig)

    # Slippage: added to entry in direction of trade (long → higher fill)
    slippage_ticks: float = 1.0

    # Commission per round-turn per contract (USD)
    commission_per_contract: float = 3.50

    # Maximum bars to hold a position before force-closing at close price
    max_holding_bars: int = 200

    def __post_init__(self) -> None:
        assert self.initial_equity > 0, "initial_equity must be positive"
        assert self.slippage_ticks >= 0, "slippage_ticks must be >= 0"
        assert self.commission_per_contract >= 0, "commission must be >= 0"
        assert self.max_holding_bars >= 1, "max_holding_bars must be >= 1"


@dataclass
class BacktestMetrics:
    """Performance statistics computed from a list of trades."""

    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float                   # 0–1
    net_pnl: float                    # Dollar
    gross_profit: float
    gross_loss: float                 # Positive number
    profit_factor: float              # gross_profit / gross_loss (inf if no losses)
    average_win: float
    average_loss: float               # Positive number (magnitude)
    expectancy: float                 # Expected dollar return per trade
    max_drawdown_pct: float           # Peak-to-trough as % of peak equity
    max_drawdown_dollars: float
    sharpe_ratio: float               # Annualised (trade-by-trade returns, 252 days)
    sortino_ratio: float              # Uses downside deviation only
    largest_win: float
    largest_loss: float               # Positive number (magnitude)
    max_consecutive_losses: int

    def __str__(self) -> str:
        lines = [
            "=" * 52,
            "  BACKTEST METRICS",
            "=" * 52,
            f"  Trades             : {self.total_trades}",
            f"  Win Rate           : {self.win_rate * 100:.1f}%",
            f"  Net P&L            : ${self.net_pnl:,.2f}",
            f"  Profit Factor      : {self.profit_factor:.2f}",
            f"  Avg Win            : ${self.average_win:,.2f}",
            f"  Avg Loss           : ${self.average_loss:,.2f}",
            f"  Expectancy         : ${self.expectancy:,.2f}",
            f"  Max Drawdown       : {self.max_drawdown_pct:.2f}%  (${self.max_drawdown_dollars:,.2f})",
            f"  Sharpe Ratio       : {self.sharpe_ratio:.2f}",
            f"  Sortino Ratio      : {self.sortino_ratio:.2f}",
            f"  Largest Win        : ${self.largest_win:,.2f}",
            f"  Largest Loss       : ${self.largest_loss:,.2f}",
            f"  Max Consec. Losses : {self.max_consecutive_losses}",
            "=" * 52,
        ]
        return "\n".join(lines)


@dataclass
class BacktestResult:
    """Full result set returned by Backtester.run()."""

    config: BacktestConfig
    trades: list[Trade]
    equity_curve: list[float]        # Equity after each trade (length == len(trades))
    metrics: BacktestMetrics

    def summary(self) -> str:
        return str(self.metrics)

    def equity_series(self) -> pd.Series:
        """Return equity curve as a pandas Series indexed by trade number."""
        return pd.Series(self.equity_curve, name="equity")


# ---------------------------------------------------------------------------
# Core engine
# ---------------------------------------------------------------------------

class Backtester:
    """Simulates a list of Signals against OHLCV data.

    Args:
        config: BacktestConfig instance.
    """

    def __init__(
        self,
        config: Optional[BacktestConfig] = None,
        market_data_feed: Optional[MarketDataFeed] = None,
    ) -> None:
        self.config = config or BacktestConfig()
        self._sizer = PositionSizer(self.config.risk_config)
        self.market_data_feed = market_data_feed

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, signals: list[Signal], ohlcv: pd.DataFrame) -> BacktestResult:
        """Run backtest.

        Args:
            signals: Ordered list of Signal objects. Overlapping signals are
                     allowed; each is evaluated independently.
            ohlcv:   DataFrame with DatetimeIndex and columns
                     [open, high, low, close].  A 'volume' column is accepted
                     but not required.  Must be sorted ascending.

        Returns:
            BacktestResult with trades, equity curve, and metrics.
        """
        self._validate_ohlcv(ohlcv)

        equity = self.config.initial_equity
        trades: list[Trade] = []
        equity_curve: list[float] = []

        for signal in signals:
            trade = self._evaluate_signal(signal, ohlcv, equity)
            if trade is None:
                continue
            equity = trade.equity_after
            trades.append(trade)
            equity_curve.append(equity)

        metrics = self._compute_metrics(trades, self.config.initial_equity)
        return BacktestResult(
            config=self.config,
            trades=trades,
            equity_curve=equity_curve,
            metrics=metrics,
        )

    # ------------------------------------------------------------------
    # Signal evaluation
    # ------------------------------------------------------------------

    def _evaluate_signal(
        self,
        signal: Signal,
        ohlcv: pd.DataFrame,
        equity: float,
    ) -> Optional[Trade]:
        """Resolve a single signal to a completed Trade."""
        cfg = self.config
        tick = cfg.risk_config.tick_size
        point_value = cfg.risk_config.point_value

        # Apply slippage to entry price
        slippage = cfg.slippage_ticks * tick
        if signal.direction == "long":
            entry_price = signal.entry_price + slippage
            stop_price = signal.stop_price
            target_price = signal.target_price
        else:
            entry_price = signal.entry_price - slippage
            stop_price = signal.stop_price
            target_price = signal.target_price

        # Size the position
        trade_risk = self._sizer.size(equity, entry_price, stop_price)
        if not trade_risk.approved:
            return None

        contracts = trade_risk.contracts

        # Find entry bar index
        try:
            entry_idx = ohlcv.index.get_loc(signal.timestamp)
        except KeyError:
            # Timestamp not in index — find first bar at or after signal time
            candidates = ohlcv.index[ohlcv.index >= signal.timestamp]
            if candidates.empty:
                return None
            entry_idx = ohlcv.index.get_loc(candidates[0])

        # Scan forward bars for exit
        exit_price, exit_ts, outcome = self._scan_exit(
            signal.direction,
            entry_price,
            stop_price,
            target_price,
            ohlcv,
            entry_idx,
        )

        # P&L calculation
        if signal.direction == "long":
            pnl_points = exit_price - entry_price
        else:
            pnl_points = entry_price - exit_price

        commission = cfg.commission_per_contract * contracts * 2  # round-turn
        pnl_dollars = (pnl_points * point_value * contracts) - commission
        equity_after = equity + pnl_dollars

        # Classify outcome
        if outcome == "open":
            final_outcome = "open"
        elif pnl_dollars > 0:
            final_outcome = "win"
        elif pnl_dollars < 0:
            final_outcome = "loss"
        else:
            final_outcome = "breakeven"

        return Trade(
            signal=signal,
            contracts=contracts,
            exit_price=exit_price,
            exit_timestamp=exit_ts,
            outcome=final_outcome,
            pnl_points=pnl_points,
            pnl_dollars=pnl_dollars,
            equity_after=equity_after,
        )

    def _scan_exit(
        self,
        direction: Direction,
        entry_price: float,
        stop_price: float,
        target_price: float,
        ohlcv: pd.DataFrame,
        entry_idx: int,
    ) -> tuple[float, pd.Timestamp, str]:
        """Scan candles from entry_idx+1 to find first stop or target hit.

        Uses candle high and low as the intra-bar proxy for order fills.
        The first level hit within the candle's range is assumed to fill.
        If both levels fall inside the same candle, the less favourable fill
        (stop) is used as a conservative estimate.

        Returns:
            (exit_price, exit_timestamp, outcome_label)
        """
        max_bars = self.config.max_holding_bars
        bars = ohlcv.iloc[entry_idx + 1: entry_idx + 1 + max_bars]

        for ts, row in bars.iterrows():
            high = row["high"]
            low = row["low"]

            if direction == "long":
                stop_hit = low <= stop_price
                target_hit = high >= target_price
            else:
                stop_hit = high >= stop_price
                target_hit = low <= target_price

            if stop_hit and target_hit:
                # Both levels breached in same bar — conservative: stop wins
                return stop_price, ts, "loss"
            if target_hit:
                return target_price, ts, "win"
            if stop_hit:
                return stop_price, ts, "loss"

        # Force-close at last available bar's close
        last_bar = ohlcv.iloc[min(entry_idx + max_bars, len(ohlcv) - 1)]
        return last_bar["close"], ohlcv.index[min(entry_idx + max_bars, len(ohlcv) - 1)], "open"

    # ------------------------------------------------------------------
    # Metrics computation
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_metrics(trades: list[Trade], initial_equity: float) -> BacktestMetrics:
        if not trades:
            return BacktestMetrics(
                total_trades=0, winning_trades=0, losing_trades=0,
                win_rate=0.0, net_pnl=0.0, gross_profit=0.0, gross_loss=0.0,
                profit_factor=0.0, average_win=0.0, average_loss=0.0,
                expectancy=0.0, max_drawdown_pct=0.0, max_drawdown_dollars=0.0,
                sharpe_ratio=0.0, sortino_ratio=0.0,
                largest_win=0.0, largest_loss=0.0, max_consecutive_losses=0,
            )

        wins = [t for t in trades if t.outcome == "win"]
        losses = [t for t in trades if t.outcome == "loss"]

        total = len(trades)
        n_wins = len(wins)
        n_losses = len(losses)
        win_rate = n_wins / total if total else 0.0

        gross_profit = sum(t.pnl_dollars for t in wins)
        gross_loss = abs(sum(t.pnl_dollars for t in losses))
        net_pnl = sum(t.pnl_dollars for t in trades)
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf")

        avg_win = gross_profit / n_wins if n_wins else 0.0
        avg_loss = gross_loss / n_losses if n_losses else 0.0
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

        # Equity curve metrics
        equity_curve = [initial_equity] + [t.equity_after for t in trades]
        peak = initial_equity
        max_dd_dollars = 0.0
        for eq in equity_curve:
            if eq > peak:
                peak = eq
            dd = peak - eq
            if dd > max_dd_dollars:
                max_dd_dollars = dd
        max_dd_pct = (max_dd_dollars / peak * 100.0) if peak > 0 else 0.0

        # Sharpe & Sortino — trade-by-trade percentage returns
        pnl_pct_returns = []
        running_eq = initial_equity
        for t in trades:
            if running_eq > 0:
                pnl_pct_returns.append(t.pnl_dollars / running_eq)
            running_eq = t.equity_after

        sharpe = _annualised_sharpe(pnl_pct_returns)
        sortino = _annualised_sortino(pnl_pct_returns)

        # Largest win/loss
        largest_win = max((t.pnl_dollars for t in wins), default=0.0)
        largest_loss = abs(min((t.pnl_dollars for t in losses), default=0.0))

        # Max consecutive losses
        max_consec = 0
        current_consec = 0
        for t in trades:
            if t.outcome == "loss":
                current_consec += 1
                max_consec = max(max_consec, current_consec)
            else:
                current_consec = 0

        return BacktestMetrics(
            total_trades=total,
            winning_trades=n_wins,
            losing_trades=n_losses,
            win_rate=win_rate,
            net_pnl=net_pnl,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            profit_factor=profit_factor,
            average_win=avg_win,
            average_loss=avg_loss,
            expectancy=expectancy,
            max_drawdown_pct=max_dd_pct,
            max_drawdown_dollars=max_dd_dollars,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            largest_win=largest_win,
            largest_loss=largest_loss,
            max_consecutive_losses=max_consec,
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_ohlcv(ohlcv: pd.DataFrame) -> None:
        required = {"open", "high", "low", "close"}
        missing = required - set(ohlcv.columns)
        if missing:
            raise ValueError(f"ohlcv DataFrame missing columns: {missing}")
        if not isinstance(ohlcv.index, pd.DatetimeIndex):
            raise TypeError("ohlcv index must be a DatetimeIndex")
        if not ohlcv.index.is_monotonic_increasing:
            raise ValueError("ohlcv must be sorted ascending by timestamp")


# ---------------------------------------------------------------------------
# Statistical helpers
# ---------------------------------------------------------------------------

_TRADING_DAYS_PER_YEAR = 252


def _annualised_sharpe(returns: list[float], risk_free: float = 0.0) -> float:
    """Annualised Sharpe ratio from a list of per-trade % returns."""
    if len(returns) < 2:
        return 0.0
    mean = statistics.mean(returns) - risk_free
    std = statistics.stdev(returns)
    if std == 0:
        return 0.0
    return (mean / std) * math.sqrt(_TRADING_DAYS_PER_YEAR)


def _annualised_sortino(returns: list[float], risk_free: float = 0.0) -> float:
    """Annualised Sortino ratio — uses downside deviation only."""
    if len(returns) < 2:
        return 0.0
    mean = statistics.mean(returns) - risk_free
    downside = [r for r in returns if r < 0]
    if not downside:
        return float("inf")
    downside_std = statistics.stdev(downside) if len(downside) > 1 else abs(downside[0])
    if downside_std == 0:
        return 0.0
    return (mean / downside_std) * math.sqrt(_TRADING_DAYS_PER_YEAR)
