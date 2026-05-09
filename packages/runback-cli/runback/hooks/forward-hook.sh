#!/bin/sh
# Runback hook forwarder. Reads JSON from stdin and POSTs to local backend.
exec curl -fsS -m 5 \
  -X POST "${RUNBACK_BACKEND_URL:-http://127.0.0.1:8000}/api/hooks/claude" \
  -H 'content-type: application/json' \
  -H "x-runback-run-id: ${RUNBACK_RUN_ID:-unknown}" \
  -H "x-runback-branch-id: ${RUNBACK_BRANCH_ID:-}" \
  --data-binary @-
