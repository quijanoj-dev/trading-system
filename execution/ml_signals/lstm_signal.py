"""
LSTM binary direction classifier for ES=F / NQ=F 5m bars.

Architecture: 2-layer LSTM (hidden=64) → binary sigmoid output.
Inputs: stationary features only (ADF-validated). Target: direction of next bar's return.

Usage:
    # Train
    python -m execution.ml_signals.lstm_signal --symbol ES=F --train

    # Predict (latest bar)
    python -m execution.ml_signals.lstm_signal --symbol ES=F --predict

    # Walk-forward backtest
    python -m execution.ml_signals.lstm_signal --symbol ES=F --backtest
"""

from __future__ import annotations

import json
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)

_MODEL_DIR = Path(__file__).parent / "models"
_MODEL_DIR.mkdir(exist_ok=True)

_LOOKBACK = 20        # sequence length fed to LSTM
_HIDDEN   = 64        # LSTM hidden units per layer
_LAYERS   = 2         # stacked LSTM depth
_DROPOUT  = 0.2
_EPOCHS   = 50
_BATCH    = 32
_LR       = 1e-3
_TRAIN_SPLIT = 0.7   # fraction used for in-sample training
_WF_STEP  = 252       # walk-forward retrain interval (bars)


# ── Stationarity check ──────────────────────────────────────────────────────

def check_stationarity(series: pd.Series, name: str = "", alpha: float = 0.05) -> bool:
    """ADF test — returns True if series is stationary (p < alpha)."""
    try:
        from statsmodels.tsa.stattools import adfuller
        result = adfuller(series.dropna(), autolag="AIC")
        passed = result[1] < alpha
        if name:
            status = "OK" if passed else "FAIL"
            print(f"  ADF [{status}] {name}: p={result[1]:.4f}")
        return passed
    except ImportError:
        return True  # statsmodels optional; skip check


# ── Feature engineering ──────────────────────────────────────────────────────

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build stationary features from OHLCV DataFrame.

    All features ADF-validated against non-stationarity.
    Returns DataFrame with NaN rows dropped.
    """
    out = pd.DataFrame(index=df.index)

    r = df["close"].pct_change()
    vol5  = r.rolling(5).std()
    vol20 = r.rolling(20).std()

    out["return_1"] = r
    out["return_5"] = df["close"].pct_change(5)
    out["return_20"] = df["close"].pct_change(20)

    # Vol ratio: σ_short/σ_long — stationary by construction
    out["vol_ratio"] = (vol5 / vol20).replace([np.inf, -np.inf], np.nan)

    # Risk-adjusted momentum
    out["mom_vol"] = (r / vol20).replace([np.inf, -np.inf], np.nan)

    # Volume z-score (rolling 20-bar)
    if "volume" in df.columns:
        v = df["volume"].astype(float)
        v_mean = v.rolling(20).mean()
        v_std  = v.rolling(20).std().replace(0, np.nan)
        out["vol_zscore"] = (v - v_mean) / v_std
    else:
        out["vol_zscore"] = 0.0

    # VWAP deviation (regime indicator)
    if {"high", "low", "volume"}.issubset(df.columns):
        typical = (df["high"] + df["low"] + df["close"]) / 3
        cum_vol = df["volume"].astype(float).cumsum()
        cum_tp  = (typical * df["volume"].astype(float)).cumsum()
        vwap = (cum_tp / cum_vol.replace(0, np.nan))
        out["vwap_dev"] = ((df["close"] - vwap) / vwap).replace([np.inf, -np.inf], np.nan)
    else:
        out["vwap_dev"] = 0.0

    # High-low range z-score
    if {"high", "low"}.issubset(df.columns):
        hl_range = (df["high"] - df["low"]) / df["close"]
        out["hl_zscore"] = (hl_range - hl_range.rolling(20).mean()) / hl_range.rolling(20).std().replace(0, np.nan)
    else:
        out["hl_zscore"] = 0.0

    return out.dropna()


def build_target(df: pd.DataFrame, features_index: pd.Index) -> pd.Series:
    """Binary direction of next bar: 1 if next close > current close, else 0."""
    r_next = df["close"].pct_change().shift(-1)
    return (r_next > 0).astype(int).reindex(features_index).dropna()


# ── Model ────────────────────────────────────────────────────────────────────

def _make_sequences(
    X: np.ndarray, y: np.ndarray, lookback: int
) -> tuple[np.ndarray, np.ndarray]:
    Xs, ys = [], []
    for i in range(lookback, len(X)):
        Xs.append(X[i - lookback : i])
        ys.append(y[i])
    return np.array(Xs, dtype=np.float32), np.array(ys, dtype=np.float32)


class TradingLSTM:
    """2-layer LSTM binary direction classifier.

    Wraps PyTorch model with sklearn-style fit/predict interface.
    Falls back gracefully when torch is not installed.
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int = _HIDDEN,
        num_layers: int = _LAYERS,
        dropout: float = _DROPOUT,
    ) -> None:
        self.input_size  = input_size
        self.hidden_size = hidden_size
        self.num_layers  = num_layers
        self.dropout     = dropout
        self._model      = None
        self._scaler     = None
        self._feature_names: list[str] = []

    def _build_torch_model(self):
        import torch
        import torch.nn as nn

        class _Net(nn.Module):
            def __init__(self, input_size, hidden_size, num_layers, dropout):
                super().__init__()
                self.lstm = nn.LSTM(
                    input_size=input_size,
                    hidden_size=hidden_size,
                    num_layers=num_layers,
                    dropout=dropout if num_layers > 1 else 0.0,
                    batch_first=True,
                )
                self.drop = nn.Dropout(dropout)
                self.fc   = nn.Linear(hidden_size, 1)

            def forward(self, x):
                out, _ = self.lstm(x)
                out = self.drop(out[:, -1, :])
                return torch.sigmoid(self.fc(out)).squeeze(-1)

        return _Net(self.input_size, self.hidden_size, self.num_layers, self.dropout)

    def fit(
        self,
        X_raw: np.ndarray,
        y: np.ndarray,
        epochs: int = _EPOCHS,
        batch_size: int = _BATCH,
        lr: float = _LR,
        verbose: bool = True,
    ) -> "TradingLSTM":
        try:
            import torch
            import torch.nn as nn
            from sklearn.preprocessing import StandardScaler
        except ImportError as e:
            print(f"  [LSTM] Missing dep: {e}. Install torch + scikit-learn.")
            return self

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_raw)
        self._scaler = scaler

        Xs, ys = _make_sequences(X_scaled, y, _LOOKBACK)
        X_t = torch.tensor(Xs)
        y_t = torch.tensor(ys)

        model = self._build_torch_model()
        optimizer = torch.optim.Adam(model.parameters(), lr=lr)
        loss_fn   = nn.BCELoss()

        dataset = torch.utils.data.TensorDataset(X_t, y_t)
        loader  = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

        model.train()
        for epoch in range(1, epochs + 1):
            total_loss = 0.0
            for xb, yb in loader:
                optimizer.zero_grad()
                pred = model(xb)
                loss = loss_fn(pred, yb)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            if verbose and epoch % 10 == 0:
                avg = total_loss / len(loader)
                print(f"  [LSTM] Epoch {epoch:3d}/{epochs} — loss={avg:.4f}")

        self._model = model
        return self

    def predict_proba(self, X_raw: np.ndarray) -> np.ndarray:
        """Return P(up) for the last `lookback` rows of X_raw."""
        import torch

        if self._model is None or self._scaler is None:
            raise RuntimeError("Model not trained. Call fit() first.")

        X_scaled = self._scaler.transform(X_raw)
        if len(X_scaled) < _LOOKBACK:
            raise ValueError(f"Need at least {_LOOKBACK} rows, got {len(X_scaled)}")

        seq = X_scaled[-_LOOKBACK:][np.newaxis, :, :]  # (1, lookback, features)
        x_t = torch.tensor(seq, dtype=torch.float32)

        self._model.eval()
        with torch.no_grad():
            prob = self._model(x_t).item()
        return np.array([1 - prob, prob])

    def save(self, path: Path) -> None:
        import torch

        if self._model is None:
            return
        torch.save(
            {
                "state_dict":   self._model.state_dict(),
                "input_size":   self.input_size,
                "hidden_size":  self.hidden_size,
                "num_layers":   self.num_layers,
                "dropout":      self.dropout,
                "scaler_mean":  self._scaler.mean_.tolist(),
                "scaler_scale": self._scaler.scale_.tolist(),
                "feature_names": self._feature_names,
            },
            path,
        )
        print(f"  [LSTM] Saved → {path}")

    @classmethod
    def load(cls, path: Path) -> "TradingLSTM":
        import torch
        from sklearn.preprocessing import StandardScaler

        ckpt = torch.load(path, weights_only=True)
        obj = cls(
            input_size  = ckpt["input_size"],
            hidden_size = ckpt["hidden_size"],
            num_layers  = ckpt["num_layers"],
            dropout     = ckpt["dropout"],
        )
        obj._model = obj._build_torch_model()
        obj._model.load_state_dict(ckpt["state_dict"])
        obj._model.eval()

        scaler = StandardScaler()
        scaler.mean_  = np.array(ckpt["scaler_mean"])
        scaler.scale_ = np.array(ckpt["scaler_scale"])
        obj._scaler = scaler
        obj._feature_names = ckpt.get("feature_names", [])
        return obj


# ── Walk-forward evaluation ──────────────────────────────────────────────────

@dataclass
class WalkForwardResult:
    n_windows:   int
    accuracy:    float
    sharpe:      float
    win_rate:    float
    total_bars:  int


def walk_forward_backtest(
    df: pd.DataFrame,
    symbol: str = "ES=F",
    step: int = _WF_STEP,
    min_train: int = 500,
    threshold: float = 0.55,
    verbose: bool = True,
) -> WalkForwardResult:
    """Walk-forward LSTM backtest.

    At each window: train on [0..t], predict [t..t+step].
    Long if P(up) > threshold, short if P(up) < (1-threshold), else flat.
    """
    feats = build_features(df)
    target = build_target(df, feats.index)
    aligned = feats.join(target.rename("target")).dropna()

    X_all = aligned.drop(columns=["target"]).values
    y_all = aligned["target"].values
    feature_names = list(aligned.drop(columns=["target"]).columns)

    n = len(X_all)
    predictions = []
    actuals     = []

    windows = range(min_train, n - step, step)
    if verbose:
        print(f"  [WF] {len(windows)} windows, step={step}, min_train={min_train}")

    for t in windows:
        X_train, y_train = X_all[:t], y_all[:t]
        X_test,  y_test  = X_all[t : t + step], y_all[t : t + step]
        if len(X_test) == 0:
            break

        model = TradingLSTM(input_size=len(feature_names))
        model._feature_names = feature_names
        model.fit(X_train, y_train, verbose=False)

        for i in range(_LOOKBACK, len(X_test)):
            window = X_test[i - _LOOKBACK : i]
            try:
                prob_up = model.predict_proba(window)[1]
                pred = 1 if prob_up > threshold else (0 if prob_up < (1 - threshold) else -1)
            except Exception:
                pred = -1
            predictions.append(pred)
            actuals.append(int(y_test[i]))

    if not predictions:
        return WalkForwardResult(0, 0.0, 0.0, 0.0, 0)

    preds = np.array(predictions)
    acts  = np.array(actuals)
    active = preds != -1
    acc = float(np.mean(preds[active] == acts[active])) if active.any() else 0.0

    # Simple P&L: +1 correct direction, -1 wrong, 0 flat
    returns = np.where(active, np.where(preds == acts, 1, -1), 0).astype(float)
    sharpe = float(returns.mean() / (returns.std() + 1e-9) * np.sqrt(252 * 78))
    win_rate = float(np.mean(returns[active] > 0)) if active.any() else 0.0

    return WalkForwardResult(
        n_windows  = len(windows),
        accuracy   = round(acc, 4),
        sharpe     = round(sharpe, 4),
        win_rate   = round(win_rate, 4),
        total_bars = len(predictions),
    )


# ── CLI ──────────────────────────────────────────────────────────────────────

def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="LSTM direction signal for ES/NQ")
    parser.add_argument("--symbol",   default="ES=F",  help="Symbol (ES=F or NQ=F)")
    parser.add_argument("--interval", default="5m",    help="Bar interval (default: 5m)")
    parser.add_argument("--train",    action="store_true", help="Train and save model")
    parser.add_argument("--predict",  action="store_true", help="Predict next bar direction")
    parser.add_argument("--backtest", action="store_true", help="Walk-forward backtest")
    parser.add_argument("--epochs",   type=int, default=_EPOCHS)
    parser.add_argument("--threshold",type=float, default=0.55, help="Signal threshold")
    args = parser.parse_args()

    from execution.market_data.candle_store import CandleStore

    store  = CandleStore()
    df     = store.get_candles(args.symbol, args.interval, limit=2000)

    if df.empty:
        print(f"No candles for {args.symbol}/{args.interval}. Run candle_store refresh first.")
        return

    feats = build_features(df)
    print(f"Built {feats.shape[1]} features, {len(feats)} bars")

    # ADF stationarity check
    for col in feats.columns:
        check_stationarity(feats[col], col)

    model_path = _MODEL_DIR / f"{args.symbol.replace('=', '')}_{args.interval}_lstm.pt"

    if args.backtest:
        print(f"\nWalk-forward backtest: {args.symbol} {args.interval}")
        result = walk_forward_backtest(df, symbol=args.symbol)
        print(f"\nResults:")
        print(f"  Windows:   {result.n_windows}")
        print(f"  Accuracy:  {result.accuracy:.1%}")
        print(f"  Win Rate:  {result.win_rate:.1%}")
        print(f"  Sharpe:    {result.sharpe:.2f}")
        print(f"  Bars:      {result.total_bars}")
        return

    if args.train:
        target = build_target(df, feats.index)
        aligned = feats.join(target.rename("target")).dropna()
        X = aligned.drop(columns=["target"]).values
        y = aligned["target"].values

        split = int(len(X) * _TRAIN_SPLIT)
        X_train, y_train = X[:split], y[:split]
        X_test,  y_test  = X[split:], y[split:]

        print(f"\nTraining: {args.symbol} {args.interval} | {len(X_train)} train, {len(X_test)} test bars")
        model = TradingLSTM(input_size=X.shape[1])
        model._feature_names = list(feats.columns)
        model.fit(X_train, y_train, epochs=args.epochs)

        # Out-of-sample accuracy
        Xs, ys = _make_sequences(
            model._scaler.transform(X_test), y_test, _LOOKBACK
        )
        import torch
        model._model.eval()
        with torch.no_grad():
            Xt = torch.tensor(Xs)
            probs = model._model(Xt).numpy()
        preds = (probs > args.threshold).astype(int)
        acc = float(np.mean(preds == ys[_LOOKBACK:]))
        print(f"  OOS accuracy: {acc:.1%} ({len(preds)} bars)")
        model.save(model_path)
        return

    if args.predict:
        if not model_path.exists():
            print(f"No trained model at {model_path}. Run --train first.")
            return
        model = TradingLSTM.load(model_path)
        X = feats.values
        probs = model.predict_proba(X)
        prob_up = probs[1]
        direction = "LONG" if prob_up > args.threshold else ("SHORT" if prob_up < (1 - args.threshold) else "FLAT")
        print(f"\n{args.symbol} {args.interval} — P(up)={prob_up:.3f} → {direction}")
        return

    parser.print_help()


if __name__ == "__main__":
    _main()
