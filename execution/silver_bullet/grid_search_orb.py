"""
ORB Grid Search — 48 parameter combinations.
Tests R × ATR-stop × range-end × trade-until on SPY 1m Alpaca data.

ORB note: OR-boundary stop (atr_stop=0) is confirmed dead on SPY 1m proxy.
This grid only tests ATR-based stops. ATR(14) on SPY 1m ≈ $0.20-0.40.
"""
from __future__ import annotations

import sys
from datetime import time
from itertools import product
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from execution.backtester import Backtester, BacktestConfig
from execution.risk_manager import RiskConfig
from execution.silver_bullet.run_backtest import _fetch_alpaca
from execution.silver_bullet.run_backtest_orb import generate_orb_signals

import numpy as np

print("Loading data (cache)...")
es = _fetch_alpaca("ES=F", "2024-01-01", None)
print(f"  {len(es):,} bars")

rc = RiskConfig(
    risk_per_trade_pct=0.5,
    max_position_size=100,
    daily_loss_limit_pct=10.0,
    max_drawdown_pct=20.0,
    point_value=1.0,
    tick_size=0.01,
)
_bt_config_base = dict(risk_config=rc, max_holding_bars=390)

# Grid — ATR-based stops only (OR-boundary confirmed dead)
R_VALS       = [1.5, 2.0, 3.0]
ATR_STOPS    = [1.0, 1.5, 2.0, 2.5]
RANGE_ENDS   = [time(10,  0), time(10, 30)]
TRADE_UNTILS = [time(14,  0), time(16,  0)]

results = []
total = len(R_VALS) * len(ATR_STOPS) * len(RANGE_ENDS) * len(TRADE_UNTILS)
i = 0

for r, atr_s, re, tu in product(R_VALS, ATR_STOPS, RANGE_ENDS, TRADE_UNTILS):
    i += 1
    label = f"OR:{re.strftime('%H:%M')} until:{tu.strftime('%H:%M')} R={r} atr={atr_s}"
    print(f"[{i:02d}/{total}] {label}...", flush=True)

    sigs = generate_orb_signals(
        es,
        range_end=re,
        trade_until=tu,
        r_multiple=r,
        atr_stop_mult=atr_s,
        htf_ema_period=20,
    )

    if len(sigs) < 3:
        results.append({"label": label, "n": len(sigs), "wr": 0, "pnl": 0, "pf": 0, "sharpe": -99})
        continue

    cfg = BacktestConfig(initial_equity=25_000.0, **_bt_config_base)
    bt = Backtester(cfg)
    result = bt.run(sigs, es)
    m = result.trades

    wins   = [t for t in m if t.outcome == "win"]
    losses = [t for t in m if t.outcome == "loss"]
    wr = len(wins) / len(m) if m else 0
    pnl = sum(t.pnl_dollars for t in m)
    gross_win  = sum(t.pnl_dollars for t in wins)
    gross_loss = abs(sum(t.pnl_dollars for t in losses))
    pf = gross_win / gross_loss if gross_loss > 0 else 0

    rets = [t.pnl_dollars / 25_000.0 for t in m]
    sharpe = (np.mean(rets) / np.std(rets) * (252 ** 0.5)) if np.std(rets) > 0 else 0

    results.append({"label": label, "n": len(m), "wr": round(wr * 100, 1),
                    "pnl": round(pnl, 2), "pf": round(pf, 2), "sharpe": round(sharpe, 2)})

results.sort(key=lambda x: x["sharpe"], reverse=True)

print("\n" + "=" * 90)
print(f"{'Window + Params':<50} {'n':>4} {'WR%':>6} {'P&L':>10} {'PF':>5} {'Sharpe':>7}")
print("=" * 90)
for r in results:
    marker = " ★" if r["sharpe"] > 1.0 else ""
    print(f"{r['label']:<50} {r['n']:>4} {r['wr']:>6} {r['pnl']:>10.2f} {r['pf']:>5.2f} {r['sharpe']:>7.2f}{marker}")
print("=" * 90)
