# Shared helpers for demo scripts. Source this file; do not execute it.

if [ -t 1 ]; then
  RB_C_RED="$(printf '\033[31m')"
  RB_C_GREEN="$(printf '\033[32m')"
  RB_C_YELLOW="$(printf '\033[33m')"
  RB_C_BLUE="$(printf '\033[34m')"
  RB_C_RESET="$(printf '\033[0m')"
else
  RB_C_RED=""; RB_C_GREEN=""; RB_C_YELLOW=""; RB_C_BLUE=""; RB_C_RESET=""
fi

rb_info() { printf '%s[runback]%s %s\n' "$RB_C_BLUE" "$RB_C_RESET" "$*"; }
rb_warn() { printf '%s[warn]%s %s\n' "$RB_C_YELLOW" "$RB_C_RESET" "$*"; }
rb_err() { printf '%s[err]%s %s\n' "$RB_C_RED" "$RB_C_RESET" "$*" >&2; }
rb_ok() { printf '%s[ok]%s %s\n' "$RB_C_GREEN" "$RB_C_RESET" "$*"; }

rb_repo_root() {
  (cd "$(dirname "$0")/.." && pwd)
}

rb_require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { rb_err "missing required command: $1"; return 1; }
}

rb_runback() {
  if command -v runback >/dev/null 2>&1; then
    runback "$@"
  else
    uv run runback "$@"
  fi
}

rb_wait_for_http() {
  url="$1"; max="${2:-30}"; waited=0
  while [ "$waited" -lt "$max" ]; do
    if curl -fsS -o /dev/null "$url" 2>/dev/null; then
      return 0
    fi
    sleep 1
    waited=$((waited + 1))
  done
  rb_err "timed out waiting for $url after ${max}s"
  return 1
}

rb_preflight_stack() {
  rb_require_cmd curl || return 1
  rb_require_cmd claude || return 1
  if ! command -v runback >/dev/null 2>&1; then
    rb_require_cmd uv || return 1
  fi
  rb_wait_for_http "http://localhost:8000/api/runs" 5 || {
    rb_err "Backend not reachable. Is 'uv run runback dev' running?"
    return 1
  }
  rb_wait_for_http "http://localhost:3000" 5 || {
    rb_warn "Frontend not reachable on :3000; continuing"
  }
}

rb_assert_file() {
  if [ ! -f "$1" ]; then
    rb_err "expected file does not exist: $1"
    return 1
  fi
}

rb_assert_count() {
  dir="$1"; expected="$2"
  actual="$(find "$dir" -type f ! -name '.gitkeep' | wc -l | tr -d ' ')"
  if [ "$actual" != "$expected" ]; then
    rb_err "expected $expected files in $dir, found $actual"
    find "$dir" -type f ! -name '.gitkeep' >&2
    return 1
  fi
}
