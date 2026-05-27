"""
Markov Chain Signal — transition matrix + Monte Carlo regime/probability estimator.

Ported from @de1lymoon's framework (https://x.com/de1lymoon/status/2059275498660757727).
Adapted for two use cases:
  1. ES/NQ regime probability — price states → forward regime distribution
  2. Polymarket contract pricing — 0-100¢ states → P(YES) calibrated for longshot bias

Usage:
    # ES/NQ regime probability
    from execution.ml_signals.markov_signal import MarkovSignal
    sig = MarkovSignal(n_states=10)
    sig.fit(price_history)          # list of floats normalized 0.0–1.0
    result = sig.predict(current_price, days_forward=5)
    print(result.p_up, result.regime_label)

    # Polymarket
    sig = MarkovSignal(n_states=10)
    sig.fit([p / 100 for p in polymarket_prices_cents])
    result = sig.predict(current_price_cents / 100, days_forward=30)
    print(f"Model: {result.p_up:.1%}  Market: {current_price_cents/100:.0%}")

CLI:
    python -m execution.ml_signals.markov_signal --symbol ES=F --days 5
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np


@dataclass
class MarkovResult:
    p_up: float           # probability price ends above current state
    p_down: float         # probability price ends below current state
    p_stay: float         # probability price stays in current bucket
    current_state: int    # discretized state index
    n_states: int
    n_sims: int
    regime_label: str     # "bullish" | "bearish" | "ranging"
    edge_cents: Optional[float] = None   # set when market_price_cents provided


class MarkovTransitionMatrix:
    """Build and query a Markov transition matrix from price history."""

    def __init__(self, n_states: int = 10) -> None:
        self.n_states = n_states
        self.T: Optional[np.ndarray] = None
        self._min_transitions = 20  # minimum observations per state for reliability

    def fit(self, prices: list[float]) -> "MarkovTransitionMatrix":
        """Build transition matrix from normalized price history (0.0–1.0).

        Args:
            prices: List of prices normalized to [0.0, 1.0].
                    For ES/NQ: (price - min) / (max - min) over lookback window.
                    For Polymarket: price_cents / 100.
        """
        n = self.n_states
        states = np.clip((np.array(prices) * n).astype(int), 0, n - 1)

        T = np.zeros((n, n))
        for i in range(len(states) - 1):
            T[states[i], states[i + 1]] += 1

        # Warn on sparse states (< min_transitions observed)
        sparse = [i for i in range(n) if T[i].sum() < self._min_transitions and T[i].sum() > 0]
        if sparse:
            import warnings
            warnings.warn(
                f"States {sparse} have fewer than {self._min_transitions} transitions — "
                "matrix may be noisy. Gather more history or reduce n_states.",
                UserWarning,
                stacklevel=2,
            )

        row_sums = T.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        self.T = T / row_sums
        return self

    def state_for(self, price_normalized: float) -> int:
        """Return state index for a normalized price."""
        return int(np.clip(price_normalized * self.n_states, 0, self.n_states - 1))


class MarkovMonteCarlo:
    """Monte Carlo simulator over a Markov transition matrix."""

    def __init__(self, matrix: MarkovTransitionMatrix, n_sims: int = 10_000) -> None:
        self.matrix = matrix
        self.n_sims = n_sims

    def simulate(self, start_state: int, steps: int) -> np.ndarray:
        """Simulate N price paths. Returns array of final states (shape: n_sims,)."""
        T = self.matrix.T
        n = self.matrix.n_states
        finals = np.empty(self.n_sims, dtype=int)

        for i in range(self.n_sims):
            state = start_state
            for _ in range(steps):
                state = np.random.choice(n, p=T[state])
            finals[i] = state

        return finals

    def estimate(
        self,
        start_price: float,
        steps: int,
        market_price_cents: Optional[float] = None,
        apply_longshot_calibration: bool = True,
    ) -> MarkovResult:
        """Full prediction pipeline.

        Args:
            start_price:       Normalized current price (0.0–1.0).
            steps:             Steps forward (bars for ES/NQ, days for Polymarket).
            market_price_cents: Polymarket market price in cents for edge calculation.
            apply_longshot_calibration: Deflate longshot probability (Polymarket only).
        """
        n = self.matrix.n_states
        start_state = self.matrix.state_for(start_price)
        finals = self.simulate(start_state, steps)

        p_up = float((finals > start_state).mean())
        p_down = float((finals < start_state).mean())
        p_stay = float((finals == start_state).mean())

        # Longshot bias calibration (Becker 2026: 72.1M trades analysis)
        # Contracts <20¢ are systematically overpriced → deflate raw MC estimate
        if apply_longshot_calibration and start_price < 0.20:
            raw_p_yes = float((finals >= n // 2).mean())
            # Empirical calibration: raw model overestimates by ~15% at 10¢
            calibration_factor = 0.85 + (start_price / 0.20) * 0.10
            p_up = raw_p_yes * calibration_factor
            p_down = 1.0 - p_up - p_stay

        if p_up > 0.55:
            regime_label = "bullish"
        elif p_down > 0.55:
            regime_label = "bearish"
        else:
            regime_label = "ranging"

        edge_cents = None
        if market_price_cents is not None:
            model_p = float((finals >= n // 2).mean())
            edge_cents = round((model_p - market_price_cents / 100) * 100, 2)

        return MarkovResult(
            p_up=round(p_up, 4),
            p_down=round(p_down, 4),
            p_stay=round(p_stay, 4),
            current_state=start_state,
            n_states=n,
            n_sims=self.n_sims,
            regime_label=regime_label,
            edge_cents=edge_cents,
        )


class MarkovSignal:
    """High-level wrapper: fit on price history, predict forward distribution."""

    def __init__(self, n_states: int = 10, n_sims: int = 10_000) -> None:
        self._mtm = MarkovTransitionMatrix(n_states)
        self._mc: Optional[MarkovMonteCarlo] = None
        self.n_sims = n_sims

    def fit(self, prices: list[float]) -> "MarkovSignal":
        self._mtm.fit(prices)
        self._mc = MarkovMonteCarlo(self._mtm, n_sims=self.n_sims)
        return self

    def predict(
        self,
        current_price: float,
        days_forward: int = 5,
        market_price_cents: Optional[float] = None,
        apply_longshot_calibration: bool = False,
    ) -> MarkovResult:
        if self._mc is None:
            raise RuntimeError("Call fit() before predict()")
        return self._mc.estimate(
            start_price=current_price,
            steps=days_forward,
            market_price_cents=market_price_cents,
            apply_longshot_calibration=apply_longshot_calibration,
        )

    def save(self, path: str | Path) -> None:
        """Persist fitted transition matrix to JSON."""
        if self._mtm.T is None:
            raise RuntimeError("Call fit() first")
        Path(path).write_text(json.dumps({
            "n_states": self._mtm.n_states,
            "T": self._mtm.T.tolist(),
        }))

    @classmethod
    def load(cls, path: str | Path, n_sims: int = 10_000) -> "MarkovSignal":
        """Load fitted signal from JSON."""
        data = json.loads(Path(path).read_text())
        sig = cls(n_states=data["n_states"], n_sims=n_sims)
        sig._mtm.T = np.array(data["T"])
        sig._mc = MarkovMonteCarlo(sig._mtm, n_sims=n_sims)
        return sig


def _fetch_prices_yfinance(symbol: str, lookback_days: int = 90) -> list[float]:
    import yfinance as yf
    from datetime import datetime, timedelta
    end = datetime.today()
    start = end - timedelta(days=lookback_days)
    df = yf.download(symbol, start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"),
                     interval="1d", progress=False, auto_adjust=True)
    closes = df["Close"].dropna().values.flatten().tolist()
    # Normalize to 0–1 over the window
    mn, mx = min(closes), max(closes)
    if mx == mn:
        return [0.5] * len(closes)
    return [(p - mn) / (mx - mn) for p in closes]


def _main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="Markov Chain signal — ES/NQ regime probability")
    p.add_argument("--symbol", default="ES=F", help="yfinance symbol")
    p.add_argument("--days", type=int, default=5, help="Steps forward")
    p.add_argument("--lookback", type=int, default=90, help="History days")
    p.add_argument("--states", type=int, default=10, help="Number of price states")
    p.add_argument("--sims", type=int, default=10_000, help="Monte Carlo simulations")
    args = p.parse_args()

    print(f"Fetching {args.lookback}d history for {args.symbol}...")
    prices = _fetch_prices_yfinance(args.symbol, args.lookback)
    print(f"  {len(prices)} bars loaded")

    sig = MarkovSignal(n_states=args.states, n_sims=args.sims)
    sig.fit(prices)

    current = prices[-1]
    result = sig.predict(current, days_forward=args.days)

    print(f"\nMarkov Signal — {args.symbol} ({args.days}d forward)")
    print(f"  Current state: {result.current_state}/{result.n_states - 1}")
    print(f"  P(up):    {result.p_up:.1%}")
    print(f"  P(down):  {result.p_down:.1%}")
    print(f"  P(stay):  {result.p_stay:.1%}")
    print(f"  Regime:   {result.regime_label.upper()}")


if __name__ == "__main__":
    _main()
