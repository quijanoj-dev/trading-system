#!/usr/bin/env bash
# PostTrade.sh — Log every trade fill immediately after execution.
# Usage: bash execution/hooks/PostTrade.sh INSTRUMENT DIRECTION ENTRY STOP SIZE SETUP
# Example: bash execution/hooks/PostTrade.sh "ES=F" long 5340.25 5334.75 1 "add_bull_div"
set -euo pipefail

if [ "$#" -lt 6 ]; then
    echo "Usage: PostTrade.sh INSTRUMENT DIRECTION ENTRY STOP SIZE SETUP" >&2
    echo "Example: PostTrade.sh ES=F long 5340.25 5334.75 1 add_bull_div" >&2
    exit 1
fi

INSTRUMENT="$1"
DIRECTION="$2"
ENTRY="$3"
STOP="$4"
SIZE="$5"
SETUP="$6"

TRADING_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
mkdir -p "$TRADING_ROOT/context"
LOG="$TRADING_ROOT/context/trades.log"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

LOG_LINE="$TIMESTAMP | instrument=$INSTRUMENT | direction=$DIRECTION | entry=$ENTRY | stop=$STOP | size=$SIZE | setup=$SETUP"
echo "$LOG_LINE" >> "$LOG"

echo "Logged: $INSTRUMENT $DIRECTION @ $ENTRY (stop $STOP, size $SIZE, setup: $SETUP)"
echo "trades.log: $LOG"
