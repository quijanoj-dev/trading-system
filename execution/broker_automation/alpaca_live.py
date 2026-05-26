"""
Alpaca Live Broker — stable order execution module for paper/live trading.

Uses alpaca-py SDK (not legacy alpaca-trade-api).
Reads credentials from ALPACA_API_KEY / ALPACA_SECRET_KEY environment vars.

Paper account: PA33WGN2JSU4 @ https://paper-api.alpaca.markets

Usage:
    from execution.broker_automation.alpaca_live import AlpacaLiveBroker

    broker = AlpacaLiveBroker(paper=True)
    order = broker.submit_bracket_order("SPY", qty=10, side="buy", stop=420.0, target=430.0)
    print(broker.get_positions())
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Literal, Optional

logger = logging.getLogger(__name__)

OrderSide = Literal["buy", "sell"]


@dataclass
class OrderResult:
    order_id: str
    symbol: str
    qty: int
    side: OrderSide
    status: str
    filled_avg_price: Optional[float] = None
    error: Optional[str] = None


class AlpacaLiveBroker:
    """Thin wrapper around alpaca-py TradingClient.

    Args:
        paper: If True (default), uses paper trading endpoint.
               Set False only when --live flag explicitly passed.
    """

    def __init__(self, paper: bool = True) -> None:
        self.paper = paper
        self._client = self._build_client()
        mode = "PAPER" if paper else "LIVE"
        logger.info("AlpacaLiveBroker initialized [%s]", mode)

    def _build_client(self):
        from alpaca.trading.client import TradingClient
        api_key = os.environ.get("ALPACA_API_KEY", "")
        secret_key = os.environ.get("ALPACA_SECRET_KEY", "")
        if not api_key or not secret_key:
            raise RuntimeError("ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in environment")
        return TradingClient(api_key, secret_key, paper=self.paper)

    def get_account(self) -> dict:
        """Return account info as dict."""
        acct = self._client.get_account()
        return {
            "id": acct.id,
            "equity": float(acct.equity),
            "cash": float(acct.cash),
            "buying_power": float(acct.buying_power),
            "pattern_day_trader": acct.pattern_day_trader,
            "trading_blocked": acct.trading_blocked,
        }

    def get_positions(self) -> list[dict]:
        """Return list of current open positions."""
        positions = self._client.get_all_positions()
        return [
            {
                "symbol": p.symbol,
                "qty": float(p.qty),
                "side": p.side,
                "avg_entry_price": float(p.avg_entry_price),
                "current_price": float(p.current_price) if p.current_price else None,
                "unrealized_pl": float(p.unrealized_pl) if p.unrealized_pl else None,
            }
            for p in positions
        ]

    def submit_market_order(
        self,
        symbol: str,
        qty: int,
        side: OrderSide,
    ) -> OrderResult:
        """Submit a market order.

        Args:
            symbol: e.g. "SPY"
            qty:    Number of shares
            side:   "buy" or "sell"
        """
        from alpaca.trading.requests import MarketOrderRequest
        from alpaca.trading.enums import OrderSide as AlpacaSide, TimeInForce

        try:
            req = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=AlpacaSide.BUY if side == "buy" else AlpacaSide.SELL,
                time_in_force=TimeInForce.DAY,
            )
            order = self._client.submit_order(req)
            logger.info("Market order submitted: %s %s %d @ market", side.upper(), symbol, qty)
            return OrderResult(
                order_id=str(order.id),
                symbol=symbol,
                qty=qty,
                side=side,
                status=str(order.status),
            )
        except Exception as e:
            logger.error("Market order failed: %s", e)
            return OrderResult(order_id="", symbol=symbol, qty=qty, side=side, status="error", error=str(e))

    def submit_bracket_order(
        self,
        symbol: str,
        qty: int,
        side: OrderSide,
        stop_price: float,
        target_price: float,
        limit_entry: Optional[float] = None,
    ) -> OrderResult:
        """Submit a bracket order (entry + stop-loss + take-profit).

        Args:
            symbol:       Ticker symbol
            qty:          Number of shares
            side:         "buy" (long) or "sell" (short)
            stop_price:   Stop-loss price
            target_price: Take-profit price
            limit_entry:  Entry limit price (None = market entry)
        """
        from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, TakeProfitRequest, StopLossRequest
        from alpaca.trading.enums import OrderSide as AlpacaSide, TimeInForce, OrderClass

        try:
            alpaca_side = AlpacaSide.BUY if side == "buy" else AlpacaSide.SELL

            take_profit = TakeProfitRequest(limit_price=round(target_price, 2))
            stop_loss = StopLossRequest(stop_price=round(stop_price, 2))

            if limit_entry:
                req = LimitOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=alpaca_side,
                    time_in_force=TimeInForce.DAY,
                    limit_price=round(limit_entry, 2),
                    order_class=OrderClass.BRACKET,
                    take_profit=take_profit,
                    stop_loss=stop_loss,
                )
            else:
                req = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=alpaca_side,
                    time_in_force=TimeInForce.DAY,
                    order_class=OrderClass.BRACKET,
                    take_profit=take_profit,
                    stop_loss=stop_loss,
                )

            order = self._client.submit_order(req)
            logger.info(
                "Bracket order: %s %s %d | stop=%.2f target=%.2f",
                side.upper(), symbol, qty, stop_price, target_price,
            )
            return OrderResult(
                order_id=str(order.id),
                symbol=symbol,
                qty=qty,
                side=side,
                status=str(order.status),
            )
        except Exception as e:
            logger.error("Bracket order failed: %s", e)
            return OrderResult(order_id="", symbol=symbol, qty=qty, side=side, status="error", error=str(e))

    def cancel_all_orders(self) -> int:
        """Cancel all open orders. Returns number of orders cancelled."""
        try:
            cancelled = self._client.cancel_orders()
            n = len(cancelled) if cancelled else 0
            logger.info("Cancelled %d orders", n)
            return n
        except Exception as e:
            logger.error("cancel_all_orders failed: %s", e)
            return 0

    def close_all_positions(self) -> list[OrderResult]:
        """Close all open positions at market price."""
        results = []
        for pos in self.get_positions():
            qty = abs(int(float(pos["qty"])))
            close_side: OrderSide = "sell" if pos["side"] == "long" else "buy"
            result = self.submit_market_order(pos["symbol"], qty, close_side)
            results.append(result)
        return results

    def close_position(self, symbol: str) -> OrderResult:
        """Close a specific position at market."""
        try:
            order = self._client.close_position(symbol)
            logger.info("Closed position: %s", symbol)
            return OrderResult(
                order_id=str(order.id),
                symbol=symbol,
                qty=0,
                side="sell",
                status=str(order.status),
            )
        except Exception as e:
            logger.error("close_position(%s) failed: %s", symbol, e)
            return OrderResult(order_id="", symbol=symbol, qty=0, side="sell", status="error", error=str(e))

    def flatten_all(self) -> None:
        """Cancel all orders then close all positions (end-of-day cleanup)."""
        self.cancel_all_orders()
        self.close_all_positions()
        logger.info("All positions flattened")
