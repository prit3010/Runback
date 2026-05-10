#!/bin/sh
# Sequential unattended demo smoke runner.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/_lib.sh"

REPO_ROOT="$(rb_repo_root)"
RUNBACK_API="${RUNBACK_API:-http://localhost:8000}"
TIMEOUT_SECS="${RUNBACK_DEMO_TIMEOUT:-600}"

rb_info "dry-run-all: verifying dev stack"
rb_preflight_stack || exit 1

poll_latest_run_until_terminal() {
  start_ts="$(date +%s)"
  while :; do
    body="$(curl -fsS "$RUNBACK_API/api/runs" || true)"
    run_id="$(printf '%s' "$body" | python3 -c 'import sys,json; d=json.load(sys.stdin); print((d or [{}])[0].get("id",""))' 2>/dev/null || true)"
    status="$(printf '%s' "$body" | python3 -c 'import sys,json; d=json.load(sys.stdin); print((d or [{}])[0].get("status",""))' 2>/dev/null || true)"
    if [ -n "$run_id" ] && { [ "$status" = "success" ] || [ "$status" = "failed" ] || [ "$status" = "paused" ]; }; then
      echo "$run_id"
      return 0
    fi
    elapsed="$(( $(date +%s) - start_ts ))"
    if [ "$elapsed" -gt "$TIMEOUT_SECS" ]; then
      rb_err "timeout waiting for run to terminate; last status: $status"
      return 1
    fi
    sleep 2
  done
}

count_side_effects() {
  run_id="$1"; kind="$2"
  curl -fsS "$RUNBACK_API/api/runs/$run_id/dag" \
    | python3 -c 'import sys,json; kind=sys.argv[1]; rows=json.load(sys.stdin).get("side_effects", []); print(sum(1 for r in rows if r.get("kind")==kind))' "$kind"
}

count_duplicate_side_effect_keys() {
  run_id="$1"; kind="${2:-}"
  curl -fsS "$RUNBACK_API/api/runs/$run_id/dag" \
    | python3 -c 'import sys,json; kind=sys.argv[1]; rows=json.load(sys.stdin).get("side_effects", []); rows=[r for r in rows if not kind or r.get("kind")==kind]; keys=[r.get("idempotency_key") for r in rows]; print(len(keys)-len(set(keys)))' "$kind"
}

rb_info "===== demo 1: backlog ====="
bash "$SCRIPT_DIR/demo-1.sh"
RUN1="$(poll_latest_run_until_terminal)"
rb_info "demo 1 run id: $RUN1"

PR_COUNT="$(count_side_effects "$RUN1" gh_pr_create)"
if [ "$PR_COUNT" -ge 3 ]; then
  rb_ok "demo 1: $PR_COUNT PR side effects ledgered"
else
  rb_err "demo 1: expected >=3 PR side effects, got $PR_COUNT"
  exit 1
fi

FAKE_PR_COUNT="$(find "$REPO_ROOT/demos/backlog/.fake-prs" -name '*.json' -type f | wc -l | tr -d ' ')"
if [ "$FAKE_PR_COUNT" -ge 3 ]; then
  rb_ok "demo 1: $FAKE_PR_COUNT fake PR files"
else
  rb_err "demo 1: expected >=3 fake PR files, got $FAKE_PR_COUNT"
  exit 1
fi

[ "$(count_duplicate_side_effect_keys "$RUN1" "")" = "0" ] || { rb_err "demo 1 duplicate side-effect keys"; exit 1; }

rb_info "===== demo 2: research ====="
bash "$SCRIPT_DIR/demo-2.sh"
RUN2="$(poll_latest_run_until_terminal)"
rb_info "demo 2 run id: $RUN2"

if [ -f "$REPO_ROOT/demos/research/report.md" ]; then
  rb_ok "demo 2: report.md written"
else
  rb_warn "demo 2: report.md not present; run may have paused before synthesis"
fi

SLACK_FILES="$(find "$REPO_ROOT/demos/research/.fake-slack" -type f ! -name '.gitkeep' | wc -l | tr -d ' ')"
if [ "$SLACK_FILES" -le 1 ]; then
  rb_ok "demo 2: $SLACK_FILES slack posts on disk"
else
  rb_err "demo 2: expected <=1 slack post, got $SLACK_FILES"
  exit 1
fi

[ "$(count_duplicate_side_effect_keys "$RUN2" slack_post)" = "0" ] || { rb_err "demo 2 duplicate slack keys"; exit 1; }

rb_ok "dry-run-all: both demos passed smoke assertions"
