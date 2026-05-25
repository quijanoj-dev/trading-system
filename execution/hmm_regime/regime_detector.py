from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd
import yaml

try:
    from hmmlearn.hmm import GaussianHMM
except ImportError as e:
    raise ImportError("hmmlearn required: pip install hmmlearn") from e


class Regime(str, Enum):
    BULL = "bull"
    BEAR = "bear"
    CHOP = "chop"


@dataclass
class RegimeResult:
    regime: Regime
    probabilities: dict[str, float]
    state_index: int


_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "regime_config.yaml")


def _load_config() -> dict:
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)


def _build_features(ohlcv: pd.DataFrame) -> np.ndarray:
    """Returns (returns, log_volume, hl_spread) feature matrix."""
    close = ohlcv["close"].astype(float)
    high = ohlcv["high"].astype(float)
    low = ohlcv["low"].astype(float)
    volume = ohlcv["volume"].astype(float)

    returns = close.pct_change().fillna(0).values
    log_vol = np.log1p(volume.values)
    hl_spread = ((high - low) / close.shift(1).fillna(close)).fillna(0).values

    return np.column_stack([returns, log_vol, hl_spread])


class RegimeDetector:
    """
    3-state Gaussian HMM regime detector (bull / bear / chop).

    Usage:
        detector = RegimeDetector()
        detector.fit(ohlcv_df)          # ohlcv_df: DataFrame with columns open/high/low/close/volume
        result = detector.predict(ohlcv_df)
        print(result.regime)            # Regime.BULL | BEAR | CHOP
        print(result.probabilities)     # {"bull": 0.72, "bear": 0.18, "chop": 0.10}
    """

    N_STATES = 3

    def __init__(self, config_path: Optional[str] = None) -> None:
        cfg = _load_config() if config_path is None else yaml.safe_load(open(config_path))
        self._lookback = cfg.get("lookback_period", 252)
        self._n_iter = cfg.get("n_iter", 100)
        self._covariance_type = cfg.get("covariance_type", "full")
        self._model: Optional[GaussianHMM] = None
        self._regime_map: dict[int, Regime] = {}

    def fit(self, ohlcv: pd.DataFrame) -> "RegimeDetector":
        """Fit HMM on the last `lookback_period` rows."""
        subset = ohlcv.tail(self._lookback)
        X = _build_features(subset)

        model = GaussianHMM(
            n_components=self.N_STATES,
            covariance_type=self._covariance_type,
            n_iter=self._n_iter,
            random_state=42,
        )
        model.fit(X)
        self._model = model
        self._regime_map = self._label_states(model, subset)
        return self

    def predict(self, ohlcv: pd.DataFrame) -> RegimeResult:
        if self._model is None:
            raise RuntimeError("Call fit() before predict()")
        X = _build_features(ohlcv.tail(self._lookback))
        state_seq = self._model.predict(X)
        posteriors = self._model.predict_proba(X)

        current_state = int(state_seq[-1])
        current_probs = posteriors[-1]

        probs_by_regime = {
            self._regime_map[i].value: float(current_probs[i])
            for i in range(self.N_STATES)
        }

        return RegimeResult(
            regime=self._regime_map[current_state],
            probabilities=probs_by_regime,
            state_index=current_state,
        )

    def _label_states(self, model: GaussianHMM, ohlcv: pd.DataFrame) -> dict[int, Regime]:
        """Assign bull/bear/chop labels by mean return of each state."""
        X = _build_features(ohlcv)
        states = model.predict(X)
        returns = X[:, 0]

        mean_returns = {
            s: float(returns[states == s].mean()) if (states == s).any() else 0.0
            for s in range(self.N_STATES)
        }
        sorted_states = sorted(mean_returns, key=mean_returns.get)

        return {
            sorted_states[0]: Regime.BEAR,
            sorted_states[1]: Regime.CHOP,
            sorted_states[2]: Regime.BULL,
        }
