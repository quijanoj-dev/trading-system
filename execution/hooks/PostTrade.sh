#!/usr/bin/env bash
# PostTrade.sh — Log every trade fill immediately after execution.
# Usage: bash execution/hooks/PostTrade.sh INSTRUMENT DIRECTION ENTRY STOP SIZE SETUP [EXIT] [PNL] [NOTES]
# Example: bash execution/hooks/PostTrade.sh "ES=F" long 5340.25 5334.75 1 "SBV1" 5355.0 +750.0 "clean break"
set -euo pipefail

if [ "$#" -lt 6 ]; then
    echo "Usage: PostTrade.sh INSTRUMENT DIRECTION ENTRY STOP SIZE SETUP [EXIT] [PNL] [NOTES]" >&2
    echo "Example: PostTrade.sh ES=F long 5340.25 5334.75 1 SBV1 5355.0 +750.0 'clean break'" >&2
    exit 1
fi

INSTRUMENT="$1"
DIRECTION="$2"
ENTRY="$3"
STOP="$4"
SIZE="$5"
SETUP="$6"
EXIT_PRICE="${7:-}"
PNL="${8:-}"
NOTES="${9:-}"

TRADING_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
mkdir -p "$TRADING_ROOT/context"
LOG="$TRADING_ROOT/context/trades.log"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
DATE_ONLY=$(date -u +"%Y-%m-%d")
TIME_ONLY=$(date -u +"%H:%M")

# ── 1. Append to flat trades.log (unchanged format) ─────────────────────────
LOG_LINE="$TIMESTAMP | instrument=$INSTRUMENT | direction=$DIRECTION | entry=$ENTRY | stop=$STOP | size=$SIZE | setup=$SETUP"
[ -n "$EXIT_PRICE" ] && LOG_LINE="$LOG_LINE | exit=$EXIT_PRICE"
[ -n "$PNL" ]        && LOG_LINE="$LOG_LINE | pnl=$PNL"
[ -n "$NOTES" ]      && LOG_LINE="$LOG_LINE | notes=$NOTES"
echo "$LOG_LINE" >> "$LOG"

# ── 2. Write Obsidian-compatible trade note ──────────────────────────────────
# One markdown file per trade — loadable into any Obsidian vault or Claude MCP
VAULT_DIR="$TRADING_ROOT/context/trade_vault"
mkdir -p "$VAULT_DIR"

SLUG="${DATE_ONLY}_${TIME_ONLY//:/-}_${INSTRUMENT/=/}_${DIRECTION}"
NOTE_FILE="$VAULT_DIR/${SLUG}.md"

cat > "$NOTE_FILE" <<OBSIDIAN
---
date: $DATE_ONLY
time: $TIME_ONLY UTC
instrument: $INSTRUMENT
direction: $DIRECTION
entry: $ENTRY
stop: $STOP
size: $SIZE
setup: $SETUP
exit: ${EXIT_PRICE:-pending}
pnl: ${PNL:-pending}
tags: [trade, $INSTRUMENT, $SETUP, $DIRECTION]
---

## Trade: $INSTRUMENT $DIRECTION @ $ENTRY

| Field | Value |
|-------|-------|
| Setup | $SETUP |
| Direction | $DIRECTION |
| Entry | $ENTRY |
| Stop | $STOP (risk: $(echo "scale=2; ($ENTRY - $STOP) * $SIZE" | bc 2>/dev/null || echo "n/a") pts) |
| Size | $SIZE |
| Exit | ${EXIT_PRICE:-pending} |
| P&L | ${PNL:-pending} |

## Notes

${NOTES:-No notes recorded.}

## Review Checklist

- [ ] Setup criteria fully met?
- [ ] Entry timing optimal?
- [ ] Stop placement logical?
- [ ] Exit at plan target?
- [ ] Emotion/discipline issue?
OBSIDIAN

echo "Logged: $INSTRUMENT $DIRECTION @ $ENTRY (stop $STOP, size $SIZE, setup: $SETUP)"
echo "trades.log:  $LOG"
echo "trade_vault: $NOTE_FILE"
