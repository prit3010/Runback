# Runner IPC Protocol

The Runback backend and CLI talk to the runner daemon over a Unix domain socket.

Default socket path: `/tmp/runback-runner.sock`.

Environment overrides:
- Runner/CLI: `RUNBACK_RUNNER_SOCKET`
- Backend compatibility: `RUNBACK_RUNNER_SOCKET_PATH`

Encoding: UTF-8 JSON, one object per message, terminated by `\n`. Each
connection carries exactly one request and one response.

## Requests

### `start_run`

Called by `runback claude`.

```json
{
  "action": "start_run",
  "request_id": "req_01HXYZ",
  "prompt": "user prompt text",
  "repo_path": "/absolute/path/to/repo"
}
```

Success:

```json
{ "ok": true, "request_id": "req_01HXYZ", "run_id": "run_01HXYZ", "pid": 12345 }
```

### `replay`

Called by the backend replay endpoint. The current backend payload is replay
metadata only; if `git_ref` and `workspace_path` are present the runner uses
them directly, otherwise it falls back to the active run workspace and
`refs/runback/<run_id>/0`.

```json
{
  "action": "replay",
  "run_id": "run_01HXYZ",
  "checkpoint_id": "cp_01HXYZ",
  "new_branch_id": "branch_01HXYZ",
  "resume_prompt": "You are resuming a Runback workflow...",
  "replay_id": "replay_01HXYZ"
}
```

Extended runner-native form:

```json
{
  "action": "replay",
  "request_id": "req_01HXYZ",
  "run_id": "run_01HXYZ",
  "checkpoint_id": "cp_01HXYZ",
  "git_ref": "refs/runback/run_01HXYZ/0",
  "workspace_path": "/absolute/path/to/ws",
  "new_branch_id": "branch_01HXYZ",
  "resume_prompt": "You are resuming a Runback workflow..."
}
```

Success:

```json
{ "ok": true, "request_id": "replay_01HXYZ", "pid": 12345 }
```

### `stop`

```json
{ "action": "stop", "request_id": "req_01HXYZ" }
```

Success:

```json
{ "ok": true, "request_id": "req_01HXYZ" }
```

## Errors

Any failure produces:

```json
{ "ok": false, "request_id": "req_01HXYZ", "error": "one-line message", "code": "bad_request" }
```

Reserved error codes:
- `bad_request`
- `not_found`
- `runtime`
- `internal`
- `worktree_missing`
- `checkpoint_missing`
- `claude_not_found`
- `internal_error`
