#!/usr/bin/env bash
# PreMarket.sh — Run before each trading session.
# Fetches HMM regime, refreshes candle store, writes context/session.md.
# Usage: bash execution/hooks/PreMarket.sh
set -euo pipefail

TRADING_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PYTHON="/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9"
cd "$TRADING_ROOT"

echo "=== Pre-Market Brief — $(date +%Y-%m-%d) ==="

# 1. HMM regime
echo "Fetching regime..."
REGIME_JSON=$("$PYTHON" -m execution.hmm_regime.regime_broadcaster 2>/dev/null || echo '{"regime":"unknown","probability":0}')
REGIME=$(echo "$REGIME_JSON" | "$PYTHON" -c "import sys,json; d=json.load(sys.stdin); print(d['regime'])")
PROB=$(echo "$REGIME_JSON"   | "$PYTHON" -c "import sys,json; d=json.load(sys.stdin); print(f\"{d['probability']:.1%}\")")

# 2. Refresh candle store (suppress per-bar lines)
echo "Refreshing candle store..."
"$PYTHON" -m execution.market_data.candle_store --refresh --quiet 2>/dev/null && echo "  Done" || echo "  WARNING: candle store refresh failed"

# 3. Write session brief
mkdir -p "$TRADING_ROOT/context"
SESSION_FILE="$TRADING_ROOT/context/session.md"
cat > "$SESSION_FILE" << EOF
# Session Brief — $(date +%Y-%m-%d)

## Regime
REGIME: ${REGIME} (${PROB})
LONG_ONLY_MODE: $([ "$REGIME" = "bull" ] && echo "ENABLED — suppress CVD bear signals" || echo "off")

## APEX Rules (funded account)
MAX_TRAILING_LOSS: \$2,500 on UNREALIZED P&L
CLOSE_BY: 17:00 EST (hard rule — no exceptions)
NO_OVERNIGHT: true
NO_NEWS_TRADING: verify CPI / FOMC / NFP calendar before session
CONSISTENCY_RULE: no single day > 30% of total account gain

## Checklist
- [ ] Check economic calendar (https://www.forexfactory.com)
- [ ] Review overnight high/low on ES1! and NQ1!
- [ ] Confirm \$ADD and \$TICK opening direction on Market_Internals indicator
- [ ] Set CVD long-only mode if regime = bull
EOF

echo ""
cat "$SESSION_FILE"
