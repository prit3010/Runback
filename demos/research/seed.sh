#!/bin/sh
# Reset the research demo to its canonical seeded state.

set -eu

DEMO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[seed.sh] resetting research demo state in $DEMO_DIR"

rm -f "$DEMO_DIR/report.md"

if [ -d "$DEMO_DIR/.fake-slack" ]; then
  find "$DEMO_DIR/.fake-slack" -type f ! -name '.gitkeep' -delete
fi

MISSING=0
for n in 1 2 3 4 5; do
  if [ ! -s "$DEMO_DIR/fixtures/page${n}.html" ]; then
    echo "[seed.sh] FATAL: fixtures/page${n}.html missing or empty" >&2
    MISSING=$((MISSING + 1))
  fi
done
if [ "$MISSING" -gt 0 ]; then
  exit 1
fi

LINES="$(grep -c '^https://' "$DEMO_DIR/urls.txt" || true)"
if [ "$LINES" != "5" ]; then
  echo "[seed.sh] FATAL: urls.txt should have 5 https URLs, found $LINES" >&2
  exit 1
fi

echo "[seed.sh] OK - fixtures intact, generated outputs cleared"
