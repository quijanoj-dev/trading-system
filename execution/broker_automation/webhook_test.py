"""
Test Alpha Insider webhook connectivity before going live.

Usage:
    ALPHA_INSIDER_API_TOKEN=your_token python webhook_test.py
"""
from __future__ import annotations

import json
import os
import sys

import requests
import yaml

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "alpha_insider_config.yaml")


def load_config() -> dict:
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)


def test_connection(config: dict) -> bool:
    token = os.environ.get("ALPHA_INSIDER_API_TOKEN")
    if not token:
        print("ERROR: ALPHA_INSIDER_API_TOKEN env var not set")
        return False

    webhook_url = config.get("webhook_url", "")
    if not webhook_url:
        print("ERROR: webhook_url not set in alpha_insider_config.yaml")
        return False

    payload = {
        "action": "buy",
        "contracts": "1",
        "price": "50000.00",
        "ticker": "BTCUSDT",
        "_test": True,
    }

    try:
        resp = requests.post(
            webhook_url,
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
        return resp.ok
    except requests.RequestException as e:
        print(f"Connection error: {e}")
        return False


def print_tradingview_payload_template() -> None:
    template = {
        "action": "{{strategy.order.action}}",
        "contracts": "{{strategy.order.contracts}}",
        "price": "{{close}}",
        "ticker": "{{ticker}}",
    }
    print("\nTradingView alert message template (paste into alert message field):")
    print(json.dumps(template, indent=2))


if __name__ == "__main__":
    cfg = load_config()
    print_tradingview_payload_template()
    print("\nTesting webhook connection...")
    ok = test_connection(cfg)
    sys.exit(0 if ok else 1)
