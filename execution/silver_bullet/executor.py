"""
Silver Bullet V1 — Paper Trade Executor

Submits bracket orders to Alpaca paper account when a signal fires.
Order structure: limit entry at FVG midpoint + stop loss + take profit (OCO bracket).

Position sizing: quarter-Kelly derived from SBV1 backtest stats (58.3% win, 14 trades).
Update _KELLY_BACKTEST at n=30 paper fills for live-calibrated sizing.
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
from alpaca.trading.requests import LimitOrderRequest, TakeProfitRequest, StopLossRequest

from execution.backtester import Signal

_TS_ROOT = Path(__file__).resolve().parent.parent.parent
_FORWARD_TEST = _TS_ROOT / "Forward_Test_Notes.md"

# Backtest-derived Kelly stats (58.3% win, 14 trades — update at n=30 paper fills)
_KELLY_BACKTEST = dict(win_rate=0.583, avg_win=170.67, avg_loss=52.74, n=14)

# SPY short not supported via simple short on free paper tier — use inverse note
_ALLOW_SHORTS = True  # shorting_enabled confirmed on paper account


def _kelly_fraction(stats: dict) -> float:
    """Full Kelly = (w*avg_w - (1-w)*avg_l) / avg_w. Returns quarter-Kelly."""
    w, avg_w, avg_l = stats["win_rate"], stats["avg_win"], stats["avg_loss"]
    kelly = (w * avg_w - (1 - w) * avg_l) / avg_w
    return max(kelly * 0.25, 0.001)  # quarter-Kelly, floor 0.1%


def _risk_pct(grade: str) -> float:
    """
    Quarter-Kelly from backtest stats. A+ gets 2× (same ratio as original fixed sizing).
    Cap at 3% to guard against oversizing on small-n data.
    """
    base = min(_kelly_fraction(_KELLY_BACKTEST), 0.03)
    return base * 2 if grade == "A+" else base


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
    Submit a bracket limit order for the given signal.
    Limit price = signal.fvg_mid (FVG zone midpoint); falls back to entry_price if fvg_mid == 0.

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

        risk   = _risk_pct(grade)
        qty    = _calc_qty(equity, risk, signal.entry_price, signal.stop_price)

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
        limit_price = round(signal.fvg_mid, 2) if signal.fvg_mid > 0 else round(signal.entry_price, 2)

        request = LimitOrderRequest(
            symbol="SPY",
            qty=qty,
            side=side,
            time_in_force=TimeInForce.DAY,
            order_class=OrderClass.BRACKET,
            limit_price=limit_price,
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
            f"limit={limit_price:.2f}  stop={signal.stop_price:.2f}  target={signal.target_price:.2f}  "
            f"risk={risk*100:.1f}% (${equity*risk:,.0f})  kelly-base={_kelly_fraction(_KELLY_BACKTEST)*100:.1f}%",
            flush=True,
        )
        _append_execution_note(signal, grade, result=result, limit_price=limit_price)
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
    limit_price: float = 0.0,
) -> None:
    ts_et = signal.timestamp.astimezone(__import__("pytz").timezone("America/New_York"))
    ts_str = ts_et.strftime("%Y-%m-%d %H:%M ET")

    if skipped:
        line = f"  **Execution**: SKIPPED — {note}\n"
    elif error:
        line = f"  **Execution**: FAILED — {error}\n"
    elif result:
        rr = abs(signal.target_price - signal.entry_price) / abs(signal.entry_price - signal.stop_price)
        lp = limit_price if limit_price > 0 else signal.entry_price
        line = (
            f"  **Execution**: SUBMITTED  "
            f"order_id=`{result.order_id}`  "
            f"qty={result.qty} SPY  "
            f"limit={lp:.2f}  stop={signal.stop_price:.2f}  target={signal.target_price:.2f}  "
            f"({rr:.1f}R)\n"
        )
    else:
        line = ""

    if line:
        with _FORWARD_TEST.open("a") as fh:
            fh.write(line)
