# HMM Regime Detector

3-state Gaussian Hidden Markov Model: **bull / bear / chop** regime classification.

## Install

```bash
pip install hmmlearn
```

Then add `hmmlearn>=0.3` to `requirements.txt`.

## Quick Start

```python
import pandas as pd
from execution.hmm_regime import RegimeDetector, Regime

# ohlcv must have columns: open, high, low, close, volume
ohlcv = pd.read_csv("data/btc_daily.csv", parse_dates=["timestamp"])

detector = RegimeDetector()
detector.fit(ohlcv)

result = detector.predict(ohlcv)
print(result.regime)          # Regime.BULL
print(result.probabilities)   # {"bull": 0.71, "bear": 0.19, "chop": 0.10}
```

## Integration with Existing Strategies

```python
from execution.hmm_regime import RegimeDetector, Regime
from execution.risk_manager import RiskManager

detector = RegimeDetector()
detector.fit(ohlcv_df)
result = detector.predict(ohlcv_df)

# Gate trades by regime
if result.regime == Regime.BULL:
    risk_manager.set_position_size(full_size)
elif result.regime == Regime.CHOP:
    risk_manager.set_position_size(half_size)
elif result.regime == Regime.BEAR:
    risk_manager.set_position_size(0)   # flat
```

## Retraining

Refit the model periodically (e.g., every 50 bars or on market structure breaks):

```python
if bar_count % config["retrain_every_n_bars"] == 0:
    detector.fit(latest_ohlcv)
```

## Configuration

Edit `regime_config.yaml`:
- `lookback_period` — bars of history used for fitting (default: 252)
- `n_iter` — EM algorithm iterations (default: 100)
- `covariance_type` — `full` (richest) or `diag` (faster, less memory)
- `retrain_every_n_bars` — caller-managed refit interval

## Features Used

| Feature | Description |
|---------|-------------|
| Returns | Close-to-close percentage change |
| Log volume | Natural log of bar volume |
| HL spread | (High - Low) / prior close — proxy for volatility |

## State Labeling

States auto-labeled by mean return: highest mean → bull, lowest → bear, middle → chop.
Labels stable across refits as long as market structure is consistent.
