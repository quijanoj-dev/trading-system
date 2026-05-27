"""
Live system health monitor — Sharpe degradation + drawdown circuit breaker.

Pattern from institutional quant stacks: define thresholds before trading starts.
The worst time to set risk limits is mid-drawdown.

Usage:
    from execution.broker_automation.monitor import check_system_health, HealthStatus

    status = check_system_health(live_returns, expected_sharpe=1.5, max_drawdown_limit=-0.05)
    if status.halt:
        stop_trading()
    elif status.review:
        notify_human(status.message)

CLI:
    python -m execution.broker_automation.monitor --returns-file returns.json
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np


@dataclass
class HealthStatus:
    status: str               # "OK" | "REVIEW" | "HALT"
    halt: bool
    review: bool
    message: str
    live_sharpe: Optional[float]
    live_drawdown: Optional[float]
    sharpe_z: Optional[float]
    n_bars: int
    details: dict = field(default_factory=dict)


def check_system_health(
    live_returns: list[float] | np.ndarray,
    expected_sharpe: float = 1.0,
    max_drawdown_limit: float = -0.05,
    sharpe_z_threshold: float = -2.0,
    min_bars: int = 20,
    annualization: int = 252 * 78,  # 5m bars in a trading year
) -> HealthStatus:
    """Evaluate live system health against pre-defined risk thresholds.

    Args:
        live_returns:        Array of per-bar returns (not cumulative).
        expected_sharpe:     In-sample / backtest Sharpe (set before go-live).
        max_drawdown_limit:  Halt threshold, e.g. -0.05 = 5% drawdown.
        sharpe_z_threshold:  How many Sharpe std-devs below expected before REVIEW.
        min_bars:            Minimum bars before any assessment fires.
        annualization:       Bars per year for Sharpe scaling.

    Returns:
        HealthStatus with halt/review flags and diagnostic values.
    """
    r = np.array(live_returns, dtype=float)
    n = len(r)

    if n < min_bars:
        return HealthStatus(
            status="INSUFFICIENT_DATA",
            halt=False,
            review=False,
            message=f"Only {n} bars — need {min_bars} before health checks fire.",
            live_sharpe=None,
            live_drawdown=None,
            sharpe_z=None,
            n_bars=n,
        )

    # Drawdown
    cum = np.cumprod(1 + r)
    running_max = np.maximum.accumulate(cum)
    drawdowns = (cum - running_max) / running_max
    live_dd = float(drawdowns.min())

    # Sharpe
    std = float(r.std())
    live_sharpe = float(r.mean() / (std + 1e-12) * np.sqrt(annualization))

    # Z-score of observed Sharpe vs expected (assume std-error ≈ 0.3, conventional)
    sharpe_z = float((live_sharpe - expected_sharpe) / 0.3)

    # HALT: drawdown breach
    if live_dd < max_drawdown_limit:
        return HealthStatus(
            status="HALT",
            halt=True,
            review=False,
            message=(
                f"HALT — drawdown {live_dd:.2%} breached limit {max_drawdown_limit:.2%}. "
                "Stop trading and review all open positions."
            ),
            live_sharpe=round(live_sharpe, 3),
            live_drawdown=round(live_dd, 4),
            sharpe_z=round(sharpe_z, 3),
            n_bars=n,
            details={"trigger": "max_drawdown", "value": live_dd, "limit": max_drawdown_limit},
        )

    # REVIEW: Sharpe degradation
    if sharpe_z < sharpe_z_threshold:
        return HealthStatus(
            status="REVIEW",
            halt=False,
            review=True,
            message=(
                f"HUMAN REVIEW — live Sharpe {live_sharpe:.2f} is "
                f"{abs(sharpe_z):.1f}σ below expected {expected_sharpe:.2f}. "
                "Regime shift or strategy decay likely."
            ),
            live_sharpe=round(live_sharpe, 3),
            live_drawdown=round(live_dd, 4),
            sharpe_z=round(sharpe_z, 3),
            n_bars=n,
            details={
                "trigger": "sharpe_degradation",
                "live_sharpe": live_sharpe,
                "expected_sharpe": expected_sharpe,
                "z_score": sharpe_z,
            },
        )

    return HealthStatus(
        status="OK",
        halt=False,
        review=False,
        message=f"Operating normally. Sharpe={live_sharpe:.2f}, DD={live_dd:.2%}",
        live_sharpe=round(live_sharpe, 3),
        live_drawdown=round(live_dd, 4),
        sharpe_z=round(sharpe_z, 3),
        n_bars=n,
    )


def load_returns_from_alpaca(
    symbol: str = "SPY",
    lookback_days: int = 30,
    paper: bool = True,
) -> list[float]:
    """Pull closed position P&L from Alpaca account as a return series.

    Returns list of per-trade returns (profit / entry_value).
    """
    try:
        import os
        from alpaca.trading.client import TradingClient
        from alpaca.trading.requests import GetPortfolioHistoryRequest

        client = TradingClient(
            api_key    = os.environ["ALPACA_API_KEY"],
            secret_key = os.environ["ALPACA_SECRET_KEY"],
            paper      = paper,
        )
        hist = client.get_portfolio_history(
            filter=GetPortfolioHistoryRequest(period=f"{lookback_days}D", timeframe="1D")
        )
        equity = np.array(hist.equity, dtype=float)
        returns = np.diff(equity) / equity[:-1]
        return returns.tolist()
    except Exception as e:
        print(f"  [Monitor] Alpaca pull failed: {e}")
        return []


def _main() -> None:
    import argparse, sys

    parser = argparse.ArgumentParser(description="Trading system health check")
    parser.add_argument("--returns-file",   help="JSON file with list of returns")
    parser.add_argument("--alpaca",         action="store_true", help="Pull returns from Alpaca paper account")
    parser.add_argument("--expected-sharpe",type=float, default=1.0)
    parser.add_argument("--max-drawdown",   type=float, default=-0.05)
    parser.add_argument("--lookback-days",  type=int,   default=30)
    args = parser.parse_args()

    if args.returns_file:
        with open(args.returns_file) as f:
            returns = json.load(f)
    elif args.alpaca:
        print("Pulling returns from Alpaca paper account...")
        returns = load_returns_from_alpaca(lookback_days=args.lookback_days)
    else:
        parser.print_help()
        return

    if not returns:
        print("No returns data. Exiting.")
        sys.exit(1)

    status = check_system_health(
        returns,
        expected_sharpe    = args.expected_sharpe,
        max_drawdown_limit = args.max_drawdown,
    )

    print(f"\nStatus:     {status.status}")
    print(f"Message:    {status.message}")
    if status.live_sharpe is not None:
        print(f"Sharpe:     {status.live_sharpe}")
        print(f"Drawdown:   {status.live_drawdown:.2%}")
        print(f"Sharpe Z:   {status.sharpe_z}")
        print(f"Bars:       {status.n_bars}")

    if status.halt:
        sys.exit(2)
    elif status.review:
        sys.exit(3)


if __name__ == "__main__":
    _main()
