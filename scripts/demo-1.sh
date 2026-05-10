#!/bin/sh
# One-command driver for the backlog demo.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/_lib.sh"

REPO_ROOT="$(rb_repo_root)"
DEMO_DIR="$REPO_ROOT/demos/backlog"

rb_info "demo-1: backlog ticket fixing"
rb_preflight_stack || exit 1

rb_info "running seed.sh"
bash "$DEMO_DIR/seed.sh"

export PATH="$DEMO_DIR/.fake-bin:$PATH"
export RUNBACK_DEMO_MODE=1
export RUNBACK_DEMO_BACKLOG_DIR="$DEMO_DIR"

PROMPT="$(cat <<'EOF'
Process every ticket labeled `auto-fix` in BACKLOG.md. For each ticket:

1. Read the referenced file and the corresponding test under tests/.
2. Make the test pass without breaking the baseline suite.
3. Run `npm test` and confirm green.
4. Create a branch named `fix/issue-N`, where N is the ticket number.
5. Commit with message `fix: <ticket title>`.
6. Push the branch and open a PR via `gh pr create --title "<ticket title>" --body "Closes ticket #N" --head fix/issue-N`.

Use TodoWrite to mark ticket boundaries. Stop and ask in chat before any
external action other than `gh pr create`. Process tickets in order.
EOF
)"

GH_PATH="$(command -v gh || true)"
case "$GH_PATH" in
  "$DEMO_DIR/.fake-bin/gh") rb_ok "gh stub is on PATH" ;;
  *) rb_err "expected gh stub at $DEMO_DIR/.fake-bin/gh, got: $GH_PATH"; exit 1 ;;
esac

rb_info "launching runback claude"
(cd "$DEMO_DIR" && rb_runback claude "$PROMPT")
rb_ok "demo-1 launched. Open http://localhost:3000 to watch the DAG."
