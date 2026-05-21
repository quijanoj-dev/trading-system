"""
Risk management module for the trading execution system.

Implements:
- Per-trade position sizing based on % account risk
- Max drawdown circuit breaker
- Daily loss limit enforcement
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RiskConfig:
    """Risk parameters for the trading system.

    Designed for prop-firm environments (e.g. Apex Trader Funding).
    All monetary values are in account currency (USD).
    """

    # Per-trade risk
    risk_per_trade_pct: float = 1.0        # % of account equity risked per trade
    max_position_size: int = 10            # Hard cap on contracts/shares per trade

    # Daily loss limit — triggers a trading halt for the session
    daily_loss_limit_pct: float = 2.0      # % of starting daily equity

    # Max drawdown circuit breaker — halts trading for the day (or until reset)
    max_drawdown_pct: float = 5.0          # % drawdown from peak equity

    # Point value per contract (ES = $50/pt, NQ = $20/pt)
    point_value: float = 50.0

    # Minimum tick size (ES = 0.25, NQ = 0.25)
    tick_size: float = 0.25

    # Prediction market limits (Polymarket)
    polymarket_max_position_pct: float = 0.02   # 2% of account per market
    polymarket_max_open_markets: int = 5

    def __post_init__(self) -> None:
        assert 0 < self.risk_per_trade_pct <= 5, "risk_per_trade_pct must be in (0, 5]"
        assert 0 < self.daily_loss_limit_pct <= 10, "daily_loss_limit_pct must be in (0, 10]"
        assert 0 < self.max_drawdown_pct <= 20, "max_drawdown_pct must be in (0, 20]"
        assert self.max_position_size >= 1, "max_position_size must be >= 1"
        assert self.point_value > 0, "point_value must be > 0"
        assert self.tick_size > 0, "tick_size must be > 0"


@dataclass
class TradeRisk:
    """Position-sizing result returned by PositionSizer."""

    contracts: int                  # Approved position size
    dollar_risk: float              # Max dollar loss at stop
    risk_pct: float                 # Actual % of equity being risked
    stop_distance_pts: float        # Distance from entry to stop in points
    approved: bool = True           # False when position cannot be sized safely
    rejection_reason: str = ""      # Human-readable reason when approved=False


class PositionSizer:
    """Calculates position size to risk a fixed % of account equity.

    Formula:
        dollar_risk    = equity * (risk_pct / 100)
        contracts      = floor(dollar_risk / (stop_pts * point_value))
        contracts      = min(contracts, max_position_size)

    Always returns at least 1 contract when the math allows it, or
    TradeRisk(approved=False) when the stop is too tight or equity is zero.
    """

    def __init__(self, config: RiskConfig) -> None:
        self.config = config

    def size(
        self,
        account_equity: float,
        entry_price: float,
        stop_price: float,
    ) -> TradeRisk:
        """Compute the appropriate position size for a trade.

        Args:
            account_equity: Current net liquidation value of the account.
            entry_price:    Intended entry price.
            stop_price:     Hard stop-loss price.

        Returns:
            TradeRisk with contracts and risk details.
        """
        if account_equity <= 0:
            return TradeRisk(
                contracts=0,
                dollar_risk=0.0,
                risk_pct=0.0,
                stop_distance_pts=0.0,
                approved=False,
                rejection_reason="account_equity must be > 0",
            )

        stop_distance_pts = abs(entry_price - stop_price)
        if stop_distance_pts < self.config.tick_size:
            return TradeRisk(
                contracts=0,
                dollar_risk=0.0,
                risk_pct=0.0,
                stop_distance_pts=stop_distance_pts,
                approved=False,
                rejection_reason=(
                    f"stop_distance {stop_distance_pts} < tick_size {self.config.tick_size}"
                ),
            )

        dollar_risk_target = account_equity * (self.config.risk_per_trade_pct / 100.0)
        risk_per_contract = stop_distance_pts * self.config.point_value

        raw_contracts = int(dollar_risk_target / risk_per_contract)
        contracts = max(1, min(raw_contracts, self.config.max_position_size))

        actual_dollar_risk = contracts * risk_per_contract
        actual_risk_pct = (actual_dollar_risk / account_equity) * 100.0

        logger.debug(
            "PositionSizer: equity=%.2f stop_pts=%.4f target_$=%.2f "
            "raw_contracts=%d final_contracts=%d",
            account_equity,
            stop_distance_pts,
            dollar_risk_target,
            raw_contracts,
            contracts,
        )

        return TradeRisk(
            contracts=contracts,
            dollar_risk=actual_dollar_risk,
            risk_pct=actual_risk_pct,
            stop_distance_pts=stop_distance_pts,
            approved=True,
        )


@dataclass
class SessionState:
    """Mutable daily session state tracked by RiskController."""

    trading_date: date
    starting_equity: float
    peak_equity: float
    current_equity: float
    realized_pnl: float = 0.0       # Cumulative closed P&L for the day
    trade_count: int = 0
    halted: bool = False
    halt_reason: str = ""


class RiskController:
    """Enforces daily loss limits and max-drawdown circuit breakers.

    Designed to be called:
        1. Before every trade (check_trade_allowed)
        2. After every fill / P&L update (record_pnl)
        3. At session start (start_session)
        4. At session end (end_session / reset)

    Thread safety: not guaranteed — wrap with a lock in a multi-threaded OMS.
    """

    def __init__(self, config: RiskConfig) -> None:
        self.config = config
        self._session: Optional[SessionState] = None

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def start_session(self, account_equity: float, trading_date: Optional[date] = None) -> None:
        """Initialize a new trading session.

        Args:
            account_equity: Account equity at session open.
            trading_date:   Defaults to today (UTC).
        """
        today = trading_date or datetime.now(timezone.utc).date()
        self._session = SessionState(
            trading_date=today,
            starting_equity=account_equity,
            peak_equity=account_equity,
            current_equity=account_equity,
        )
        logger.info(
            "RiskController: session started date=%s equity=%.2f", today, account_equity
        )

    def end_session(self) -> Optional[SessionState]:
        """Close the current session and return its final state."""
        if self._session:
            logger.info(
                "RiskController: session ended pnl=%.2f trades=%d halted=%s",
                self._session.realized_pnl,
                self._session.trade_count,
                self._session.halted,
            )
        snapshot = self._session
        self._session = None
        return snapshot

    # ------------------------------------------------------------------
    # Trade gate
    # ------------------------------------------------------------------

    def check_trade_allowed(self) -> tuple[bool, str]:
        """Return (allowed, reason) before entering a new position.

        Returns:
            (True, "")              — trading is allowed
            (False, reason_str)    — trading is halted, reason explains why
        """
        if self._session is None:
            return False, "No active session — call start_session() first"

        if self._session.halted:
            return False, self._session.halt_reason

        # Re-evaluate limits in case equity updated since last check
        reason = self._evaluate_limits()
        if reason:
            self._halt(reason)
            return False, reason

        return True, ""

    # ------------------------------------------------------------------
    # P&L tracking
    # ------------------------------------------------------------------

    def record_pnl(self, pnl: float) -> None:
        """Record closed P&L for a completed trade and re-evaluate limits.

        Args:
            pnl: Signed P&L in account currency (positive = profit, negative = loss).
        """
        if self._session is None:
            logger.warning("record_pnl called with no active session — ignored")
            return

        self._session.realized_pnl += pnl
        self._session.current_equity += pnl
        self._session.trade_count += 1

        if self._session.current_equity > self._session.peak_equity:
            self._session.peak_equity = self._session.current_equity

        logger.debug(
            "record_pnl: pnl=%.2f cumulative=%.2f equity=%.2f peak=%.2f",
            pnl,
            self._session.realized_pnl,
            self._session.current_equity,
            self._session.peak_equity,
        )

        reason = self._evaluate_limits()
        if reason:
            self._halt(reason)

    def update_unrealized_equity(self, current_equity: float) -> None:
        """Update current equity with unrealized mark-to-market (intrabar).

        Useful for real-time drawdown checks while a position is open.
        """
        if self._session is None:
            return

        self._session.current_equity = current_equity
        if current_equity > self._session.peak_equity:
            self._session.peak_equity = current_equity

        reason = self._evaluate_limits()
        if reason:
            self._halt(reason)

    # ------------------------------------------------------------------
    # Status / reporting
    # ------------------------------------------------------------------

    @property
    def is_halted(self) -> bool:
        return self._session is not None and self._session.halted

    @property
    def session(self) -> Optional[SessionState]:
        return self._session

    def status_dict(self) -> dict:
        """Return a JSON-serializable status snapshot."""
        if self._session is None:
            return {"active_session": False}

        s = self._session
        daily_loss_limit = s.starting_equity * (self.config.daily_loss_limit_pct / 100.0)
        max_dd = s.peak_equity * (self.config.max_drawdown_pct / 100.0)

        return {
            "active_session": True,
            "trading_date": s.trading_date.isoformat(),
            "starting_equity": s.starting_equity,
            "current_equity": s.current_equity,
            "peak_equity": s.peak_equity,
            "realized_pnl": s.realized_pnl,
            "trade_count": s.trade_count,
            "halted": s.halted,
            "halt_reason": s.halt_reason,
            "daily_loss_limit_usd": daily_loss_limit,
            "daily_loss_used_usd": max(0.0, -s.realized_pnl),
            "daily_loss_remaining_usd": daily_loss_limit + s.realized_pnl,
            "max_drawdown_limit_usd": max_dd,
            "current_drawdown_usd": max(0.0, s.peak_equity - s.current_equity),
            "drawdown_remaining_usd": max_dd - max(0.0, s.peak_equity - s.current_equity),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _evaluate_limits(self) -> str:
        """Return a non-empty reason string if any risk limit is breached."""
        s = self._session
        assert s is not None

        # Daily loss limit
        daily_loss_limit = s.starting_equity * (self.config.daily_loss_limit_pct / 100.0)
        if s.realized_pnl <= -daily_loss_limit:
            return (
                f"Daily loss limit hit: realized P&L ${s.realized_pnl:.2f} "
                f">= limit -${daily_loss_limit:.2f} "
                f"({self.config.daily_loss_limit_pct}% of ${s.starting_equity:.2f})"
            )

        # Max drawdown circuit breaker
        drawdown = s.peak_equity - s.current_equity
        max_drawdown_allowed = s.peak_equity * (self.config.max_drawdown_pct / 100.0)
        if drawdown >= max_drawdown_allowed:
            return (
                f"Max drawdown circuit breaker: drawdown ${drawdown:.2f} "
                f">= limit ${max_drawdown_allowed:.2f} "
                f"({self.config.max_drawdown_pct}% from peak ${s.peak_equity:.2f})"
            )

        return ""

    def _halt(self, reason: str) -> None:
        """Mark the session as halted."""
        if self._session and not self._session.halted:
            self._session.halted = True
            self._session.halt_reason = reason
            logger.warning("RiskController: TRADING HALTED — %s", reason)


class RiskManager:
    """Facade that combines PositionSizer and RiskController.

    Typical OMS integration:
        1. On session open:
               rm.start_session(account_equity)
        2. Before each order:
               trade_risk = rm.size_position(equity, entry, stop)
               if not trade_risk.approved: reject
               allowed, reason = rm.check_trade_allowed()
               if not allowed: reject
        3. After each fill/close:
               rm.record_pnl(realized_pnl)
        4. On intrabar mark-to-market:
               rm.update_unrealized_equity(current_equity)
        5. On session close:
               rm.end_session()
    """

    def __init__(self, config: Optional[RiskConfig] = None) -> None:
        self.config = config or RiskConfig()
        self._sizer = PositionSizer(self.config)
        self._controller = RiskController(self.config)

    # Delegate sizing
    def size_position(
        self, account_equity: float, entry_price: float, stop_price: float
    ) -> TradeRisk:
        return self._sizer.size(account_equity, entry_price, stop_price)

    # Delegate session + gate + P&L tracking
    def start_session(self, account_equity: float, trading_date: Optional[date] = None) -> None:
        self._controller.start_session(account_equity, trading_date)

    def end_session(self) -> Optional[SessionState]:
        return self._controller.end_session()

    def check_trade_allowed(self) -> tuple[bool, str]:
        return self._controller.check_trade_allowed()

    def record_pnl(self, pnl: float) -> None:
        self._controller.record_pnl(pnl)

    def update_unrealized_equity(self, current_equity: float) -> None:
        self._controller.update_unrealized_equity(current_equity)

    @property
    def is_halted(self) -> bool:
        return self._controller.is_halted

    def status_dict(self) -> dict:
        return self._controller.status_dict()
