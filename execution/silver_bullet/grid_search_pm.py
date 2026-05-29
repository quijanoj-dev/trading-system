"""
PM Session Grid Search — SBV pattern, 27 parameter combinations.
Finds best config for 1:00–3:00 PM ET window.
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
from execution.silver_bullet.signals import generate_signals

print("Loading data (cache)...")
es = _fetch_alpaca("ES=F", "2024-01-01", None)
nq = _fetch_alpaca("NQ=F", "2024-01-01", None)
common = es.index.intersection(nq.index)
es, nq = es.loc[common], nq.loc[common]

rc = RiskConfig(
    risk_per_trade_pct=0.5,
    max_position_size=100,
    daily_loss_limit_pct=10.0,
    max_drawdown_pct=20.0,
    point_value=1.0,
    tick_size=0.01,
)
_bt_config_base = dict(risk_config=rc, max_holding_bars=90)

# Grid
WINDOWS = [
    (time(13,  0), time(14,  0)),
    (time(13,  0), time(14, 30)),
    (time(13, 30), time(14, 30)),
]
R_VALS      = [1.5, 2.0, 3.0]
ATR_STOPS   = [1.5, 2.0, 2.5]

results = []

total = len(WINDOWS) * len(R_VALS) * len(ATR_STOPS)
i = 0
for (ss, se), r, atr_s in product(WINDOWS, R_VALS, ATR_STOPS):
    i += 1
    label = f"{ss.strftime('%H:%M')}–{se.strftime('%H:%M')} R={r} atr={atr_s}"
    print(f"[{i:02d}/{total}] {label}...", flush=True)

    sigs = generate_signals(
        es, nq,
        swing_length=10, sh_lookback=60,
        fvg_min=0.05, expiry_bars=20,
        r_multiple=r, require_smt=False,
        atr_mult=0.5, atr_stop_mult=atr_s,
        htf_ema_period=20,
        po3_gate=True, ifvg=True,
        session_start=ss, session_end=se,
        dead_start=None, dead_end=None,
    )

    if len(sigs) < 3:
        results.append({"label": label, "n": len(sigs), "wr": 0, "pnl": 0, "pf": 0, "sharpe": -99})
        continue

    cfg = BacktestConfig(initial_equity=25_000.0, **_bt_config_base)
    bt = Backtester(cfg)
    result = bt.run(sigs, es)
    m = result.trades

    wins = [t for t in m if t.outcome == "win"]
    losses = [t for t in m if t.outcome == "loss"]
    wr = len(wins) / len(m) if m else 0
    pnl = sum(t.pnl_dollars for t in m)
    gross_win = sum(t.pnl_dollars for t in wins)
    gross_loss = abs(sum(t.pnl_dollars for t in losses))
    pf = gross_win / gross_loss if gross_loss > 0 else 0

    import numpy as np
    rets = [t.pnl_dollars / 25_000.0 for t in m]
    sharpe = (np.mean(rets) / np.std(rets) * (252 ** 0.5)) if np.std(rets) > 0 else 0

    results.append({"label": label, "n": len(m), "wr": round(wr * 100, 1),
                    "pnl": round(pnl, 2), "pf": round(pf, 2), "sharpe": round(sharpe, 2)})

# Sort by Sharpe descending
results.sort(key=lambda x: x["sharpe"], reverse=True)

print("\n" + "="*80)
print(f"{'Window + Params':<40} {'n':>4} {'WR%':>6} {'P&L':>8} {'PF':>5} {'Sharpe':>7}")
print("="*80)
for r in results:
    marker = " ★" if r["sharpe"] > 1.0 else ""
    print(f"{r['label']:<40} {r['n']:>4} {r['wr']:>6} {r['pnl']:>8.2f} {r['pf']:>5.2f} {r['sharpe']:>7.2f}{marker}")
print("="*80)
