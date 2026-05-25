"""
Regime Broadcaster — fetches OHLCV, runs HMM regime detection, outputs JSON signal.

Usage:
    python -m execution.hmm_regime.regime_broadcaster          # stdout (default)
    python -m execution.hmm_regime.regime_broadcaster --file   # write to output_file
    python -m execution.hmm_regime.regime_broadcaster --webhook  # POST to webhook_url
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import yaml

_CONFIG_PATH = Path(__file__).parent / "broadcaster_config.yaml"
_SITE_PACKAGES = "/Users/apple/Library/Python/3.9/lib/python/site-packages"


def _ensure_site_packages() -> None:
    if _SITE_PACKAGES not in sys.path:
        sys.path.insert(0, _SITE_PACKAGES)


def _load_config() -> dict:
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)


def _fetch_ohlcv(ticker: str, period: str, interval: str) -> pd.DataFrame:
    _ensure_site_packages()
    import yfinance as yf  # noqa: PLC0415

    df = yf.download(ticker, period=period, interval=interval,
                     progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0).str.lower()
    else:
        df.columns = [c.lower() for c in df.columns]
    return df.dropna()


class RegimeBroadcaster:
    def __init__(self) -> None:
        self.config = _load_config()

    def get_ohlcv(self) -> pd.DataFrame:
        return _fetch_ohlcv(
            self.config["ticker"],
            self.config["period"],
            self.config["interval"],
        )

    def broadcast(self) -> dict:
        from .regime_detector import RegimeDetector  # noqa: PLC0415

        ohlcv = self.get_ohlcv()
        det = RegimeDetector()
        det.fit(ohlcv)
        result = det.predict(ohlcv)

        payload = {
            "regime": result.regime.value,
            "probability": round(result.probabilities[result.regime.value], 4),
            "probabilities": {k: round(v, 4) for k, v in result.probabilities.items()},
            "ticker": self.config["ticker"],
            "bars": len(ohlcv),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        mode = self.config.get("output_mode", "stdout")

        if mode == "file":
            out_path = Path(self.config["output_file"])
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(payload, indent=2))
        elif mode == "webhook":
            url = self.config.get("webhook_url", "")
            if url:
                requests.post(url, json=payload, timeout=10)
            else:
                print("WARNING: webhook_url not configured", file=sys.stderr)
        else:
            print(json.dumps(payload))

        return payload


if __name__ == "__main__":
    mode_override = None
    if "--file" in sys.argv:
        mode_override = "file"
    elif "--webhook" in sys.argv:
        mode_override = "webhook"

    b = RegimeBroadcaster()
    if mode_override:
        b.config["output_mode"] = mode_override

    try:
        result = b.broadcast()
        if b.config.get("output_mode") != "stdout":
            print(f"Regime: {result['regime']} ({result['probability']:.1%})")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
