#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATE="$(date +%F)"
OUTDIR="$ROOT/outputs/$DATE"
mkdir -p "$OUTDIR"

LINKS_FILE="$ROOT/signals/today_links.txt"

cat << 'TEMPLATE'
Paste LinkedIn posts using this format (Ctrl-D when done):

--- POST 1 ---
Author:
Role (if obvious):
Why I saved it:
Post text:
[paste]

--- POST 2 ---
...
TEMPLATE
cat > "$LINKS_FILE"

# One run: master prompt + the link dump
claude --print "$(
  cat "$ROOT/prompts/daily_distribution_master.md"
  echo
  echo "----- LINK DUMP START -----"
  cat "$LINKS_FILE"
  echo "----- LINK DUMP END -----"
)" > "$OUTDIR/daily.md"

ln -sf "$OUTDIR/daily.md" "$ROOT/outputs/latest.md"
echo "Wrote: $OUTDIR/daily.md"
echo "Latest: $ROOT/outputs/latest.md"
