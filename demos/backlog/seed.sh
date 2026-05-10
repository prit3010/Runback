#!/bin/sh
# Reset the backlog demo to its canonical seeded state.

set -eu

DEMO_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$DEMO_DIR/../.." && pwd)"
FRESH=0

for arg in "$@"; do
  case "$arg" in
    --fresh) FRESH=1 ;;
    --help|-h)
      echo "Usage: $0 [--fresh]"
      exit 0
      ;;
    *)
      echo "seed.sh: unknown arg: $arg" >&2
      exit 2
      ;;
  esac
done

echo "[seed.sh] resetting backlog demo state in $DEMO_DIR"

cd "$REPO_ROOT"
git checkout -- \
  demos/backlog/src/pagination.js \
  demos/backlog/src/inventory.js \
  demos/backlog/src/fetcher.js \
  demos/backlog/src/email.js \
  demos/backlog/src/config.js \
  demos/backlog/src/greet.js \
  demos/backlog/src/index.js \
  demos/backlog/BACKLOG.md \
  demos/backlog/package.json \
  demos/backlog/jest.config.js \
  2>/dev/null || true

cd "$DEMO_DIR"
git clean -fd src/ tests/ 2>/dev/null || true

if [ -d "$DEMO_DIR/.fake-prs" ]; then
  find "$DEMO_DIR/.fake-prs" -type f ! -name '.gitkeep' -delete
fi

if git -C "$DEMO_DIR" rev-parse --git-dir >/dev/null 2>&1; then
  git -C "$DEMO_DIR" branch --list 'fix/issue-*' 2>/dev/null \
    | sed 's/^[* ] *//' \
    | while read -r b; do
        [ -n "$b" ] && git -C "$DEMO_DIR" branch -D "$b" >/dev/null 2>&1 || true
      done
fi

if [ "$FRESH" = "1" ]; then
  rm -rf "$DEMO_DIR/node_modules" "$DEMO_DIR/coverage"
fi

if [ ! -d "$DEMO_DIR/node_modules" ]; then
  echo "[seed.sh] installing npm deps"
  (cd "$DEMO_DIR" && npm install --no-audit --no-fund --loglevel=error)
fi

echo "[seed.sh] verifying seeded state..."
(cd "$DEMO_DIR" && npm run test:baseline --silent >/dev/null 2>&1) \
  || { echo "[seed.sh] FATAL: baseline tests do not pass on seeded state" >&2; exit 1; }

EXPECTED_FAILS=0
for t in pagination inventory fetcher email config; do
  if (cd "$DEMO_DIR" && npx jest "tests/${t}.test.js" --runInBand --silent >/dev/null 2>&1); then
    echo "[seed.sh] FATAL: tests/${t}.test.js passes on seeded state; bug not seeded?" >&2
    exit 1
  fi
  EXPECTED_FAILS=$((EXPECTED_FAILS + 1))
done

echo "[seed.sh] OK - baseline green, ${EXPECTED_FAILS} ticket suites red as expected"
