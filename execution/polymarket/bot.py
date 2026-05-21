"""Claude Code-driven Polymarket bot runner.

Autonomous market scanning loop. Finds edges, presents them for approval,
optionally executes. Default: dry-run (never live without --live flag).

Usage:
    # Dry run — show opportunities
    python -m execution.polymarket.bot

    # Live trading (requires POLYMARKET_API_KEY + POLYMARKET_SECRET)
    python -m execution.polymarket.bot --live

    # One-shot scan, no loop
    python -m execution.polymarket.bot --once
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from typing import List, Optional

from execution.polymarket.connector import PolymarketConnector, PolymarketMarket
from execution.polymarket.strategy import (
    LiquidityMispricingStrategy,
    PolymarketSignal,
    PolymarketStrategy,
    ResolutionAmbiguityStrategy,
)


SCAN_INTERVAL_SECONDS = 3600   # 1 hour
MIN_VOLUME = 10_000             # USD minimum market volume
MAX_SPREAD = 0.10               # 10% max spread
MAX_OPEN_MARKETS = 5            # from RiskConfig.polymarket_max_open_markets
ACCOUNT_VALUE = 10_000          # placeholder; replace with live account value


def scan_markets(connector: PolymarketConnector, strategies: List[PolymarketStrategy]) -> List[PolymarketSignal]:
    """Scan all active markets and return signals from all strategies."""
    markets = connector.get_markets(
        active=True,
        min_volume=MIN_VOLUME,
        max_spread=MAX_SPREAD,
    )

    signals: List[PolymarketSignal] = []
    for market in markets:
        for strategy in strategies:
            if strategy.is_eligible(market):
                signal = strategy.analyze(market)
                if signal and signal.edge >= 0.05:
                    signals.append(signal)

    signals.sort(key=lambda s: s.edge, reverse=True)
    return signals


def format_signal(signal: PolymarketSignal, account_value: float) -> str:
    size = signal.market.__class__  # get strategy class for sizing
    # Use strategy's base size method
    position_size = min(signal.fractional_kelly * account_value, 0.02 * account_value)

    return (
        f"\n{'='*60}\n"
        f"MARKET:  {signal.market.question[:80]}\n"
        f"ID:      {signal.market.market_id[:32]}...\n"
        f"Volume:  ${signal.market.volume:,.0f}  |  End: {signal.market.end_date[:10]}\n"
        f"Prices:  YES={signal.market.yes_price:.3f}  NO={signal.market.no_price:.3f}\n"
        f"Signal:  BUY {signal.direction} @ {signal.market_price:.3f}\n"
        f"Edge:    +{signal.edge:.3f}  |  Est prob: {signal.estimated_prob:.3f}\n"
        f"Size:    ${position_size:.2f}  |  Kelly: {signal.kelly_fraction:.3f}\n"
        f"Reason:  {signal.rationale}\n"
        f"Conf:    {signal.confidence:.0%}\n"
    )


def run_loop(live: bool = False, once: bool = False) -> None:
    connector = PolymarketConnector(live=live)
    strategies: List[PolymarketStrategy] = [
        ResolutionAmbiguityStrategy(),
        LiquidityMispricingStrategy(),
    ]

    mode = "LIVE" if live else "DRY RUN"
    print(f"\nPolymarket Bot — {mode} mode")
    print(f"Scanning every {SCAN_INTERVAL_SECONDS//60} minutes")
    print(f"Strategies: {[s.__class__.__name__ for s in strategies]}\n")

    while True:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] Scanning markets...")

        try:
            signals = scan_markets(connector, strategies)
        except Exception as e:
            print(f"  Scan error: {e}")
            if once:
                break
            time.sleep(SCAN_INTERVAL_SECONDS)
            continue

        if not signals:
            print("  No signals above threshold.")
        else:
            print(f"  Found {len(signals)} signal(s):")
            for sig in signals[:MAX_OPEN_MARKETS]:
                print(format_signal(sig, ACCOUNT_VALUE))

                if live:
                    # Human-in-the-loop: require explicit confirmation
                    confirm = input(f"  Execute BUY {sig.direction}? [y/N]: ").strip().lower()
                    if confirm == "y":
                        size = min(sig.fractional_kelly * ACCOUNT_VALUE, 0.02 * ACCOUNT_VALUE)
                        order = connector.place_order(
                            market_id=sig.market.market_id,
                            side=sig.direction,
                            size=size,
                            price=sig.market_price,
                        )
                        print(f"  Order: {json.dumps(order.__dict__, default=str)}")

        if once:
            break

        print(f"\nNext scan in {SCAN_INTERVAL_SECONDS//60} minutes...")
        time.sleep(SCAN_INTERVAL_SECONDS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Polymarket bot runner")
    parser.add_argument("--live", action="store_true", help="Enable live order execution")
    parser.add_argument("--once", action="store_true", help="Run one scan and exit")
    args = parser.parse_args()

    if args.live:
        print("WARNING: Live mode enabled. Orders will be submitted to Polymarket.")
        print("Verify jurisdiction legality before proceeding.")
        confirm = input("Continue? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

    run_loop(live=args.live, once=args.once)


if __name__ == "__main__":
    main()
