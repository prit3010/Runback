#!/bin/sh
# One-command driver for the research demo.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/_lib.sh"

REPO_ROOT="$(rb_repo_root)"
DEMO_DIR="$REPO_ROOT/demos/research"

rb_info "demo-2: website-to-report"
rb_preflight_stack || exit 1

rb_info "running seed.sh"
bash "$DEMO_DIR/seed.sh"

export PATH="$DEMO_DIR/.fake-bin:$PATH"
export RUNBACK_DEMO_MODE=1
export RUNBACK_DEMO_RESEARCH_DIR="$DEMO_DIR"
export RUNBACK_FIXTURE_DIR="$DEMO_DIR/fixtures"

SLACK_PATH="$(command -v slack-cli || true)"
case "$SLACK_PATH" in
  "$DEMO_DIR/.fake-bin/slack-cli") rb_ok "slack-cli stub is on PATH" ;;
  *) rb_err "expected slack-cli stub at $DEMO_DIR/.fake-bin/slack-cli, got: $SLACK_PATH"; exit 1 ;;
esac

PROMPT="$(cat "$DEMO_DIR/prompt.md")"

rb_info "launching runback claude"
(cd "$DEMO_DIR" && rb_runback claude "$PROMPT")
rb_ok "demo-2 launched. Open http://localhost:3000 to watch the DAG."
