"""
TradingAgents — Top-10 Nasdaq batch run.

Runs TradingAgents for each of the top-10 Nasdaq market-cap stocks and
aggregates individual HOLD/BUY/SELL decisions into a directional bias
for QQQ/NQ.

Usage (requires .venv314 with TradingAgents installed):
    source .venv314/bin/activate
    python3 execution/silver_bullet/ta_multi.py --date 2026-05-28

Output:
    Console table + results/ta_multi_YYYY-MM-DD.json

Known issues:
    - Use claude-sonnet-4-6, NOT opus-4-7 (old thinking.type.enabled API)
    - Do NOT add SPY/QQQ — ETF has no fundamentals data
    - Runs sequentially to avoid API rate limits
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

# Top-10 Nasdaq by market cap (as of 2026) — equities only, no ETFs
TOP10_NASDAQ = [
    "AAPL",  # Apple
    "MSFT",  # Microsoft
    "NVDA",  # Nvidia
    "AMZN",  # Amazon
    "META",  # Meta Platforms
    "TSLA",  # Tesla
    "GOOGL", # Alphabet Class A
    "AVGO",  # Broadcom
    "COST",  # Costco
    "NFLX",  # Netflix
]


def _run_single(ticker: str, analysis_date: str) -> dict:
    """Run TradingAgents for one ticker. Returns {decision, raw_state}."""
    from tradingagents.default_config import TradingAgentsConfig
    from tradingagents.graph.trading_graph import TradingAgentsGraph

    config = TradingAgentsConfig(
        llm_provider="anthropic",
        deep_think_llm="claude-sonnet-4-6",
        quick_think_llm="claude-sonnet-4-6",
        max_debate_rounds=1,
        max_risk_discuss_rounds=1,
        max_recur_limit=25,
    )
    ta = TradingAgentsGraph(debug=False, config=config)

    try:
        state, decision = ta.propagate(ticker, analysis_date)
        return {"ticker": ticker, "decision": str(decision).strip().upper(), "error": None}
    except Exception as exc:
        return {"ticker": ticker, "decision": "ERROR", "error": str(exc)}


def _aggregate(results: list[dict]) -> str:
    """Majority vote across valid decisions → QQQ bias string."""
    counts: dict[str, int] = {"BUY": 0, "SELL": 0, "HOLD": 0}
    for r in results:
        d = r["decision"]
        if d in counts:
            counts[d] += 1
    buy, sell, hold = counts["BUY"], counts["SELL"], counts["HOLD"]
    if buy > sell and buy > hold:
        return "BULLISH"
    if sell > buy and sell > hold:
        return "BEARISH"
    return "NEUTRAL"


def main() -> None:
    p = argparse.ArgumentParser(description="TradingAgents top-10 Nasdaq batch")
    p.add_argument("--date", default=str(date.today()),
                   help="Analysis date YYYY-MM-DD (default: today)")
    p.add_argument("--tickers", nargs="+", default=TOP10_NASDAQ,
                   help="Override ticker list (default: top-10 Nasdaq)")
    args = p.parse_args()

    print(f"\nTradingAgents batch — {args.date}  ({len(args.tickers)} tickers)")
    print("=" * 60)

    results: list[dict] = []
    for i, ticker in enumerate(args.tickers, 1):
        print(f"[{i:02d}/{len(args.tickers)}] {ticker}...", flush=True)
        r = _run_single(ticker, args.date)
        results.append(r)
        status = r["decision"] if not r["error"] else f"ERROR: {r['error'][:60]}"
        print(f"         → {status}")

    qqq_bias = _aggregate(results)

    print("\n" + "=" * 60)
    print(f"{'Ticker':<8} {'Decision':<10}")
    print("-" * 20)
    for r in results:
        marker = " ★" if r["decision"] in ("BUY", "SELL") else ""
        print(f"{r['ticker']:<8} {r['decision']:<10}{marker}")
    print("=" * 60)

    buy_n  = sum(1 for r in results if r["decision"] == "BUY")
    sell_n = sum(1 for r in results if r["decision"] == "SELL")
    hold_n = sum(1 for r in results if r["decision"] == "HOLD")
    err_n  = sum(1 for r in results if r["decision"] == "ERROR")
    print(f"BUY={buy_n}  SELL={sell_n}  HOLD={hold_n}  ERROR={err_n}")
    print(f"\nQQQ Bias → {qqq_bias}")
    print("=" * 60)

    out_dir = _ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"ta_multi_{args.date}.json"
    payload = {
        "date": args.date,
        "ran_at": datetime.utcnow().isoformat(),
        "tickers": args.tickers,
        "results": results,
        "summary": {"buy": buy_n, "sell": sell_n, "hold": hold_n, "error": err_n},
        "qqq_bias": qqq_bias,
    }
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"Saved → {out_path}")


if __name__ == "__main__":
    main()
