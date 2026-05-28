"""
Silver Bullet V1 — Paper Trade Executor

Submits bracket orders to Alpaca paper account when a signal fires.
Order structure: market entry + stop loss + take profit (OCO bracket).

Position sizing: 0.5% risk per trade (A grade) / 1.0% (A+ grade).
Symbol: SPY (long) or SPY short via fractional shares.

Env vars required:
    ALPACA_API_KEY
    ALPACA_SECRET_KEY
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderClass, OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest, TakeProfitRequest, StopLossRequest

from execution.backtester import Signal

_TS_ROOT = Path(__file__).resolve().parent.parent.parent
_FORWARD_TEST = _TS_ROOT / "Forward_Test_Notes.md"

# Risk per trade by grade
_RISK_PCT = {"A+": 0.010, "A": 0.005}  # 1.0% A+, 0.5% A

# SPY short not supported via simple short on free paper tier — use inverse note
_ALLOW_SHORTS = False  # set True if margin enabled on paper account


@dataclass
class OrderResult:
    order_id: str
    symbol: str
    side: str
    qty: float
    entry: float
    stop: float
    target: float
    grade: str
    submitted_at: datetime
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


def _client() -> TradingClient:
    key    = os.environ.get("ALPACA_API_KEY", "")
    secret = os.environ.get("ALPACA_SECRET_KEY", "")
    if not key or not secret:
        raise EnvironmentError("ALPACA_API_KEY and ALPACA_SECRET_KEY must be set.")
    return TradingClient(key, secret, paper=True)


def _calc_qty(equity: float, risk_pct: float, entry: float, stop: float) -> int:
    """Shares = (equity × risk_pct) / |entry - stop|, floored to whole shares."""
    risk_dollars = equity * risk_pct
    risk_per_share = abs(entry - stop)
    if risk_per_share < 0.01:
        return 0
    qty = int(risk_dollars / risk_per_share)
    return max(qty, 1)


def submit_paper_order(signal: Signal, grade: str) -> OrderResult:
    """
    Submit a bracket order for the given signal.

    Returns OrderResult with order_id on success, error string on failure.
    Skips short signals if _ALLOW_SHORTS is False (logs a note instead).
    """
    if signal.direction == "short" and not _ALLOW_SHORTS:
        msg = f"[executor] SHORT skipped — margin not enabled on paper account"
        print(msg, flush=True)
        _append_execution_note(signal, grade, skipped=True, note=msg)
        return OrderResult(
            order_id="SKIPPED", symbol="SPY", side="short",
            qty=0, entry=signal.entry_price, stop=signal.stop_price,
            target=signal.target_price, grade=grade,
            submitted_at=datetime.now(timezone.utc), error=msg,
        )

    try:
        client = _client()
        acct   = client.get_account()
        equity = float(acct.equity)

        risk_pct = _RISK_PCT.get(grade, 0.005)
        qty      = _calc_qty(equity, risk_pct, signal.entry_price, signal.stop_price)

        if qty == 0:
            error = "qty=0 — stop too close to entry"
            print(f"[executor] {error}", flush=True)
            return OrderResult(
                order_id="SKIPPED", symbol="SPY", side=signal.direction,
                qty=0, entry=signal.entry_price, stop=signal.stop_price,
                target=signal.target_price, grade=grade,
                submitted_at=datetime.now(timezone.utc), error=error,
            )

        side = OrderSide.BUY if signal.direction == "long" else OrderSide.SELL

        request = MarketOrderRequest(
            symbol="SPY",
            qty=qty,
            side=side,
            time_in_force=TimeInForce.DAY,
            order_class=OrderClass.BRACKET,
            take_profit=TakeProfitRequest(limit_price=round(signal.target_price, 2)),
            stop_loss=StopLossRequest(stop_price=round(signal.stop_price, 2)),
        )

        order = client.submit_order(request)
        result = OrderResult(
            order_id=str(order.id),
            symbol="SPY",
            side=signal.direction,
            qty=qty,
            entry=signal.entry_price,
            stop=signal.stop_price,
            target=signal.target_price,
            grade=grade,
            submitted_at=datetime.now(timezone.utc),
        )

        print(
            f"[executor] ORDER SUBMITTED  id={result.order_id}  "
            f"{side.value.upper()} {qty} SPY  "
            f"stop={signal.stop_price:.2f}  target={signal.target_price:.2f}  "
            f"risk={risk_pct*100:.1f}% (${equity*risk_pct:,.0f})",
            flush=True,
        )
        _append_execution_note(signal, grade, result=result)
        return result

    except Exception as exc:
        error = str(exc)
        print(f"[executor] ORDER FAILED: {error}", flush=True)
        _append_execution_note(signal, grade, error=error)
        return OrderResult(
            order_id="ERROR", symbol="SPY", side=signal.direction,
            qty=0, entry=signal.entry_price, stop=signal.stop_price,
            target=signal.target_price, grade=grade,
            submitted_at=datetime.now(timezone.utc), error=error,
        )


def _append_execution_note(
    signal: Signal,
    grade: str,
    result: OrderResult | None = None,
    skipped: bool = False,
    note: str = "",
    error: str = "",
) -> None:
    ts_et = signal.timestamp.astimezone(__import__("pytz").timezone("America/New_York"))
    ts_str = ts_et.strftime("%Y-%m-%d %H:%M ET")

    if skipped:
        line = f"  **Execution**: SKIPPED — {note}\n"
    elif error:
        line = f"  **Execution**: FAILED — {error}\n"
    elif result:
        rr = abs(signal.target_price - signal.entry_price) / abs(signal.entry_price - signal.stop_price)
        line = (
            f"  **Execution**: SUBMITTED  "
            f"order_id=`{result.order_id}`  "
            f"qty={result.qty} SPY  "
            f"stop={signal.stop_price:.2f}  target={signal.target_price:.2f}  "
            f"({rr:.1f}R)\n"
        )
    else:
        line = ""

    if line:
        with _FORWARD_TEST.open("a") as fh:
            fh.write(line)
