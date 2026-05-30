"""
ta_multi_lite — Zero-cost Top-10 Nasdaq bias scanner.

Replaces TradingAgents (expensive LLM API) with a deterministic scoring engine:
  - Technical  : RSI, MACD, EMA trend, ATR momentum (yfinance 1d OHLCV)
  - Fundamental: P/E, growth, margins, debt/equity (yfinance .info)
  - Momentum   : 52w position, 20d return, vs 50d/200d MA
  - Intraday   : 5m EMA 9/20/50 stack — Stock Market Wolf layout
  - Opening Prt: price vs 9:30 AM ET open — session directional bias

5m EMA stack interpretation:
  Bull: price > EMA9 > EMA20 > EMA50 → long bias
  Bear: price < EMA9 < EMA20 < EMA50 → short bias
  Mixed: EMAs tangled → neutral

Composite score 0–100:
  ≥ 65 → BUY  |  ≤ 35 → SELL  |  35–65 → HOLD
  Weights: tech=0.30 · fund=0.22 · mom=0.22 · ema5m=0.11 · op_bias=0.15

Cost: $0.  Runtime: ~30s for 10 tickers.

Usage:
    source .venv/bin/activate  (NOT .venv314)
    python3 execution/silver_bullet/ta_multi_lite.py
    python3 execution/silver_bullet/ta_multi_lite.py --date 2026-05-28 --verbose
    python3 execution/silver_bullet/ta_multi_lite.py --tickers AAPL MSFT NVDA
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from datetime import date, datetime, time as _time, timezone
from pathlib import Path
from typing import Optional

import yfinance as yf
import pandas as pd

warnings.filterwarnings("ignore")

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

TOP10_NASDAQ = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META",
    "TSLA", "GOOGL", "AVGO", "COST", "NFLX",
]



# ── Technical indicators (pure pandas, no extra deps) ───────────────────────

def _rsi(close: pd.Series, period: int = 14) -> float:
    delta = close.diff().dropna()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, float("nan"))
    rsi_series = 100 - (100 / (1 + rs))
    return float(rsi_series.iloc[-1]) if not rsi_series.empty else 50.0


def _macd_signal(close: pd.Series) -> float:
    """Return MACD histogram value (positive = bullish momentum)."""
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    return float(hist.iloc[-1]) if not hist.empty else 0.0


def _ema(close: pd.Series, span: int) -> float:
    return float(close.ewm(span=span, adjust=False).mean().iloc[-1])


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)
    return float(tr.rolling(period).mean().iloc[-1])


# ── Scoring functions (each returns 0–100) ──────────────────────────────────

def _score_technical(hist: pd.DataFrame) -> tuple[float, dict]:
    close = hist["Close"]
    high  = hist["High"]
    low   = hist["Low"]
    vol   = hist["Volume"]
    price = float(close.iloc[-1])

    details: dict[str, float] = {}

    # RSI (0–100 → remap: oversold=bullish, overbought=bearish)
    rsi = _rsi(close)
    details["rsi"] = round(rsi, 1)
    if rsi < 30:
        rsi_score = 90   # oversold — mean reversion setup
    elif rsi < 45:
        rsi_score = 70
    elif rsi < 55:
        rsi_score = 50
    elif rsi < 70:
        rsi_score = 35
    else:
        rsi_score = 20   # overbought

    # MACD histogram (positive = bullish)
    macd_hist = _macd_signal(close)
    details["macd_hist"] = round(macd_hist, 4)
    macd_score = 65 if macd_hist > 0 else 35

    # Price vs EMA 20 / 50 / 200
    ema20  = _ema(close, 20)
    ema50  = _ema(close, 50)
    ema200 = _ema(close, 200) if len(close) >= 200 else ema50
    details["ema20"] = round(ema20, 2)
    details["ema50"] = round(ema50, 2)
    details["price_vs_ema20_pct"] = round((price / ema20 - 1) * 100, 2)

    ema_score = 50
    if price > ema200 and price > ema50 and price > ema20:
        ema_score = 80   # full bull stack
    elif price > ema50 and price > ema20:
        ema_score = 70
    elif price > ema20:
        ema_score = 55
    elif price < ema200 and price < ema50 and price < ema20:
        ema_score = 20   # full bear stack
    elif price < ema50 and price < ema20:
        ema_score = 30
    else:
        ema_score = 40

    # Volume trend (20d avg vs 5d avg)
    vol_5d  = float(vol.iloc[-5:].mean())  if len(vol) >= 5  else float(vol.mean())
    vol_20d = float(vol.iloc[-20:].mean()) if len(vol) >= 20 else float(vol.mean())
    vol_ratio = vol_5d / vol_20d if vol_20d > 0 else 1.0
    details["vol_ratio_5d_20d"] = round(vol_ratio, 2)
    vol_score = 65 if vol_ratio > 1.1 else (45 if vol_ratio > 0.9 else 35)

    tech_score = (rsi_score * 0.30 + macd_score * 0.25 +
                  ema_score * 0.35 + vol_score * 0.10)
    return round(tech_score, 1), details


def _score_fundamental(info: dict) -> tuple[float, dict]:
    details: dict[str, object] = {}
    scores: list[float] = []

    # Forward P/E (lower = cheaper = bullish, but must exist)
    fpe = info.get("forwardPE")
    details["forwardPE"] = fpe
    if fpe is not None:
        if fpe < 15:   scores.append(80)
        elif fpe < 25: scores.append(65)
        elif fpe < 35: scores.append(50)
        elif fpe < 50: scores.append(40)
        else:          scores.append(25)

    # Revenue growth YoY
    rev_growth = info.get("revenueGrowth")
    details["revenueGrowth"] = rev_growth
    if rev_growth is not None:
        if rev_growth > 0.20:   scores.append(80)
        elif rev_growth > 0.10: scores.append(65)
        elif rev_growth > 0.0:  scores.append(50)
        else:                   scores.append(30)

    # Earnings growth
    eg = info.get("earningsGrowth")
    details["earningsGrowth"] = eg
    if eg is not None:
        if eg > 0.20:   scores.append(80)
        elif eg > 0.05: scores.append(65)
        elif eg > 0.0:  scores.append(50)
        else:           scores.append(25)

    # Gross margins
    gm = info.get("grossMargins")
    details["grossMargins"] = gm
    if gm is not None:
        if gm > 0.40:   scores.append(75)
        elif gm > 0.25: scores.append(60)
        elif gm > 0.10: scores.append(45)
        else:           scores.append(30)

    # Debt/equity (lower = safer)
    de = info.get("debtToEquity")
    details["debtToEquity"] = de
    if de is not None:
        if de < 50:    scores.append(75)
        elif de < 100: scores.append(60)
        elif de < 200: scores.append(45)
        else:          scores.append(30)

    fund_score = (sum(scores) / len(scores)) if scores else 50.0
    return round(fund_score, 1), details


def _score_momentum(info: dict, hist: pd.DataFrame) -> tuple[float, dict]:
    details: dict[str, object] = {}
    close = hist["Close"]
    price = float(close.iloc[-1])
    scores: list[float] = []

    # 52-week position (price / 52w high)
    wk52_high = info.get("fiftyTwoWeekHigh") or float(close.max())
    wk52_low  = info.get("fiftyTwoWeekLow")  or float(close.min())
    rng = wk52_high - wk52_low
    wk52_pos = ((price - wk52_low) / rng) if rng > 0 else 0.5
    details["52w_position_pct"] = round(wk52_pos * 100, 1)
    if wk52_pos > 0.80:   scores.append(80)
    elif wk52_pos > 0.60: scores.append(65)
    elif wk52_pos > 0.40: scores.append(50)
    elif wk52_pos > 0.20: scores.append(40)
    else:                  scores.append(25)

    # 20-day return
    ret20 = (price / float(close.iloc[-20]) - 1) if len(close) >= 20 else 0.0
    details["return_20d_pct"] = round(ret20 * 100, 2)
    if ret20 > 0.08:    scores.append(80)
    elif ret20 > 0.03:  scores.append(65)
    elif ret20 > -0.02: scores.append(50)
    elif ret20 > -0.07: scores.append(35)
    else:               scores.append(20)

    # Beta (higher beta stocks get momentum premium in bull env — neutral scoring)
    beta = info.get("beta")
    details["beta"] = beta

    # Earnings proximity (within 30 days = uncertainty → neutral dampener)
    try:
        cal = yf.Ticker(info.get("symbol", "")).calendar
        if cal and "Earnings Date" in cal:
            earn_dates = cal["Earnings Date"]
            if earn_dates:
                next_earn = earn_dates[0]
                days_to_earn = (next_earn - date.today()).days
                details["days_to_earnings"] = days_to_earn
                if 0 <= days_to_earn <= 7:
                    scores.append(50)  # event risk — neutral
    except Exception:
        pass

    mom_score = (sum(scores) / len(scores)) if scores else 50.0
    return round(mom_score, 1), details


def _score_ema5m(ticker: str) -> tuple[float, dict]:
    """5-minute EMA 9/20/50 stack — Stock Market Wolf intraday bias."""
    try:
        hist5m = yf.Ticker(ticker).history(period="5d", interval="5m")
    except Exception as e:
        return 50.0, {"error": str(e)}

    if hist5m.empty or len(hist5m) < 50:
        return 50.0, {"error": "insufficient 5m bars"}

    close = hist5m["Close"]
    price  = float(close.iloc[-1])
    ema9   = float(close.ewm(span=9,  adjust=False).mean().iloc[-1])
    ema20  = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
    ema50  = float(close.ewm(span=50, adjust=False).mean().iloc[-1])

    details = {
        "price_5m":  round(price,  2),
        "ema9_5m":   round(ema9,   2),
        "ema20_5m":  round(ema20,  2),
        "ema50_5m":  round(ema50,  2),
    }

    # Stack alignment scoring
    bull_conditions = [price > ema9, ema9 > ema20, ema20 > ema50, price > ema50]
    bear_conditions = [price < ema9, ema9 < ema20, ema20 < ema50, price < ema50]
    bull_count = sum(bull_conditions)
    bear_count = sum(bear_conditions)

    details["stack"] = (
        "FULL_BULL" if bull_count == 4 else
        "FULL_BEAR" if bear_count == 4 else
        f"MIXED_{bull_count}b/{bear_count}br"
    )

    # Score: full bull=85, 3/4 bull=70, mixed=50, 3/4 bear=30, full bear=15
    if   bull_count == 4: score = 85.0
    elif bull_count == 3: score = 70.0
    elif bear_count == 3: score = 30.0
    elif bear_count == 4: score = 15.0
    else:                 score = 50.0

    return score, details


def _opening_print_bias(ticker: str) -> tuple[float, dict]:
    """Opening Print: price vs 9:30 AM ET open. Above OP → 80 (long), below → 20 (short)."""
    try:
        hist1m = yf.Ticker(ticker).history(period="1d", interval="1m")
    except Exception as e:
        return 50.0, {"error": str(e)}

    if hist1m.empty:
        return 50.0, {"error": "no intraday data"}

    idx = hist1m.index
    if idx.tzinfo is None:
        idx = idx.tz_localize("America/New_York")
    else:
        idx = idx.tz_convert("America/New_York")
    hist1m.index = idx

    open_bars = hist1m[hist1m.index.time >= _time(9, 30)]
    if open_bars.empty:
        return 50.0, {"error": "no bars at/after 9:30 ET"}

    op_price = float(open_bars.iloc[0]["Open"])
    current  = float(hist1m["Close"].iloc[-1])
    diff_pct = (current / op_price - 1) * 100 if op_price > 0 else 0.0

    if current > op_price:
        bias, score = "LONG", 80.0
    elif current < op_price:
        bias, score = "SHORT", 20.0
    else:
        bias, score = "NEUTRAL", 50.0

    return score, {
        "opening_print": round(op_price, 2),
        "current":       round(current, 2),
        "op_bias":       bias,
        "diff_pct":      round(diff_pct, 3),
    }


# ── Main scoring entry point ─────────────────────────────────────────────────

def _score_ticker(ticker: str) -> dict:
    t = yf.Ticker(ticker)
    try:
        hist = t.history(period="1y", interval="1d")
    except Exception as e:
        return {"ticker": ticker, "decision": "ERROR", "error": str(e),
                "score": None, "breakdown": {}}

    if hist.empty or len(hist) < 30:
        return {"ticker": ticker, "decision": "ERROR",
                "error": "insufficient history", "score": None, "breakdown": {}}

    try:
        info = t.info
    except Exception:
        info = {}

    # Individual scores
    tech_score,  tech_det  = _score_technical(hist)
    fund_score,  fund_det  = _score_fundamental(info)
    mom_score,   mom_det   = _score_momentum(info, hist)
    ema5m_score, ema5m_det = _score_ema5m(ticker)
    op_score,    op_det    = _opening_print_bias(ticker)

    # Weighted composite (tech:0.30 · fund:0.22 · mom:0.22 · ema5m:0.11 · op_bias:0.15)
    composite = round(
        tech_score  * 0.30 +
        fund_score  * 0.22 +
        mom_score   * 0.22 +
        ema5m_score * 0.11 +
        op_score    * 0.15,
        1
    )

    if composite >= 65:
        decision = "BUY"
    elif composite <= 35:
        decision = "SELL"
    else:
        decision = "HOLD"

    return {
        "ticker":   ticker,
        "decision": decision,
        "score":    composite,
        "error":    None,
        "breakdown": {
            "technical":    {"score": tech_score,  **tech_det},
            "fundamental":  {"score": fund_score,  **fund_det},
            "momentum":     {"score": mom_score,   **mom_det},
            "ema5m":        {"score": ema5m_score, **ema5m_det},
            "opening_print": {"score": op_score,   **op_det},
        },
    }


# ── Aggregation ──────────────────────────────────────────────────────────────

def _aggregate(results: list[dict]) -> str:
    counts: dict[str, int] = {"BUY": 0, "SELL": 0, "HOLD": 0}
    for r in results:
        d = r.get("decision", "")
        if d in counts:
            counts[d] += 1
    buy, sell, hold = counts["BUY"], counts["SELL"], counts["HOLD"]
    if buy > sell and buy > hold:
        return "BULLISH"
    if sell > buy and sell > hold:
        return "BEARISH"
    return "NEUTRAL"


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description="Zero-cost Top-10 Nasdaq bias scanner")
    p.add_argument("--date",    default=str(date.today()),
                   help="Analysis date label YYYY-MM-DD (default: today)")
    p.add_argument("--tickers", nargs="+", default=TOP10_NASDAQ,
                   help="Override ticker list")
    p.add_argument("--verbose", action="store_true",
                   help="Print per-ticker score breakdown")
    args = p.parse_args()

    print(f"\nta_multi_lite — {args.date}  ({len(args.tickers)} tickers)  [zero-cost]")
    print("=" * 60)

    results: list[dict] = []
    for i, ticker in enumerate(args.tickers, 1):
        print(f"[{i:02d}/{len(args.tickers)}] {ticker}...", end=" ", flush=True)
        r = _score_ticker(ticker)
        results.append(r)

        if r["error"]:
            print(f"ERROR: {r['error'][:60]}")
        else:
            score_str = f"score={r['score']:.0f}"
            bd = r["breakdown"]
            stack = bd["ema5m"].get("stack", "?")
            op_bias = bd["opening_print"].get("op_bias", "?")
            detail_str = (
                f"  tech={bd['technical']['score']:.0f}"
                f"  fund={bd['fundamental']['score']:.0f}"
                f"  mom={bd['momentum']['score']:.0f}"
                f"  5m={bd['ema5m']['score']:.0f}({stack})"
                f"  op={op_bias}"
            )
            print(f"→ {r['decision']:<4}  {score_str}{detail_str if args.verbose else ''}")

        if i < len(args.tickers):
            time.sleep(0.5)  # gentle rate-limit

    qqq_bias = _aggregate(results)

    print("\n" + "=" * 60)
    print(f"{'Ticker':<8} {'Decision':<8} {'Score':>5}  {'Tech':>4} {'Fund':>4} {'Mom':>4} {'5mEMA':>5} {'OP':>5}  {'Stack':<12} OP Bias")
    print("-" * 74)
    for r in results:
        if r["error"]:
            print(f"{r['ticker']:<8} {'ERROR':<8}")
        else:
            bd = r["breakdown"]
            stack  = bd["ema5m"].get("stack", "?")
            op_bias = bd["opening_print"].get("op_bias", "?")
            marker = " ★" if r["decision"] in ("BUY", "SELL") else ""
            print(
                f"{r['ticker']:<8} {r['decision']:<8} {r['score']:>5.0f}"
                f"  {bd['technical']['score']:>4.0f}"
                f" {bd['fundamental']['score']:>4.0f}"
                f" {bd['momentum']['score']:>4.0f}"
                f" {bd['ema5m']['score']:>5.0f}"
                f" {bd['opening_print']['score']:>5.0f}"
                f"  {stack:<12} {op_bias}{marker}"
            )
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
    out_path = out_dir / f"ta_lite_{args.date}.json"
    payload = {
        "date":     args.date,
        "engine":   "ta_multi_lite",
        "ran_at":   datetime.now(timezone.utc).isoformat(),
        "tickers":  args.tickers,
        "results":  results,
        "summary":  {"buy": buy_n, "sell": sell_n, "hold": hold_n, "error": err_n},
        "qqq_bias": qqq_bias,
        "weights":  {"technical": 0.30, "fundamental": 0.22, "momentum": 0.22, "ema5m": 0.11, "opening_print": 0.15},
    }
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"Saved → {out_path}")


if __name__ == "__main__":
    main()
