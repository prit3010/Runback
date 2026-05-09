# Runback PRD

**Product:** Runback  
**Version:** v0.1 PRD  
**Status:** Draft for hackathon MVP + product foundation  
**Primary integration:** Claude Code hooks  
**Primary use case:** Checkpointing and replay for long-horizon Claude Code workflows  

---

## 1. Executive Summary

Runback is checkpointing and replay infrastructure for long-horizon AI agent workflows, starting with Claude Code.

As developers increasingly use coding agents for multi-step tasks such as debugging, refactoring, testing, documentation generation, dependency upgrades, and scheduled maintenance, failures become expensive. A coding agent may read files, inspect a repository, generate a plan, edit code, run tests, fail, and then require the user to manually reconstruct what happened. Existing traces and terminal logs show activity, but they usually do not answer the most important question:

> Where can I safely resume this failed agent run without restarting from scratch?

Runback captures Claude Code runs as a dynamic DAG of prompts, tool calls, file mutations, logs, artifacts, checkpoints, and replay attempts. Each node receives a recovery policy such as rerun, reuse cached output, restore checkpoint, requires approval, unsafe, or unknown. When a run fails, Runback recommends the nearest safe recovery point, restores the workspace to a checkpoint, reuses trusted prior outputs, and relaunches Claude Code with a generated resume prompt. The replay creates a new branch in the DAG so users can compare the failed path and the recovery path.

The long-term vision is to become an Airflow-style control plane for agent workflows: scheduling, observability, checkpointing, replay, side-effect safety, and human-in-the-loop recovery for long-running agents.

The hackathon MVP should focus on a tight, compelling demo:

1. User registers or triggers a Claude Code flow.
2. Runback launches Claude Code with hooks installed.
3. Claude Code tool calls stream into Runback.
4. Runback visualizes the run as a DAG.
5. A test/build step fails.
6. Runback identifies the nearest safe checkpoint.
7. User clicks replay.
8. Runback restores the checkpoint, reuses cached prior outputs, relaunches Claude Code with a resume prompt, and creates a successful replay branch.

---

## 2. Product Positioning

### 2.1 One-line description

Runback enables checkpointing and replay for long-horizon Claude Code workflows, letting developers resume failed runs from safe recovery points instead of restarting from scratch.

### 2.2 Short GitHub description

Airflow-style checkpointing and replay for Claude Code runs. Capture tool calls as a DAG, restore safe checkpoints, and replay failed agent workflows.

### 2.3 Product thesis

Observability tells developers what happened. Runback tells developers where it is safe to resume.

### 2.4 Why now

Coding agents are becoming capable enough to execute longer tasks, but the developer experience around failure recovery is still immature. Long-horizon agent runs are often represented as long transcripts, scattered logs, and file diffs. When something fails late, developers either restart the agent, manually issue a follow-up prompt, or inspect the terminal history themselves.

Runback introduces an execution model that treats agent runs like recoverable workflows:

- Tool calls become DAG nodes.
- File mutations become checkpoint boundaries.
- External reads become cached artifacts.
- Side effects are labeled and protected.
- Failed nodes can be replayed from safe recovery points.

### 2.5 Differentiation

Runback is not primarily another trace viewer. It is a replay and recovery layer.

| Category | What it usually provides | Runback differentiation |
|---|---|---|
| Claude Code terminal | Agent execution and terminal logs | Adds DAG visualization, checkpoints, replay branches, and recovery policy |
| Observability tools | Traces, spans, costs, latency, errors | Adds checkpoint-aware replay and safe recovery recommendations |
| Workflow orchestrators like Airflow | Static DAGs, scheduled tasks, task retry | Captures dynamic agent DAGs generated at runtime |
| Agent frameworks | Runtime abstractions and tool orchestration | Works with existing Claude Code workflows instead of replacing the agent |
| Git only | Repo history and diffs | Maps file state to agent nodes and replay semantics |

---

## 3. Problem Statement

### 3.1 Core problem

Long-horizon coding-agent workflows are hard to debug and recover when they fail.

Developers using Claude Code often face runs like:

```text
Prompt
→ Read repository
→ Search files
→ Read docs
→ Generate plan
→ Edit code
→ Run tests
→ Fail
→ Inspect error
→ Edit again
→ Fail again
```

When the run fails, the user wants to know:

- What exactly happened?
- Which tool calls were made?
- What files changed?
- Which artifacts were produced?
- What error caused the failure?
- Which previous outputs are safe to reuse?
- Which steps must be rerun?
- Which steps should not be replayed because they have side effects?
- Where can the agent safely resume?

Today, these answers are not organized around recovery.

### 3.2 Current user pain

1. **Restarting from scratch wastes time and tokens**  
   If a run fails after 20 minutes, the user often has to restart the agent or manually prompt it to continue.

2. **Terminal logs are not structured enough**  
   Logs show raw activity but not an execution graph, checkpoint boundaries, or replay policies.

3. **Agent transcripts are noisy**  
   Users must infer which steps succeeded and what context can be reused.

4. **File changes are hard to associate with agent decisions**  
   Developers can inspect git diffs, but it is not always obvious which tool call or node created each change.

5. **External reads and side effects are treated the same**  
   Reading a website, running tests, editing a file, creating a PR, and deploying code have very different replay semantics.

6. **Replay is manual and unsafe**  
   Users may rerun commands that should not be rerun, such as deployment, publishing, external API writes, or GitHub PR creation.

---

## 4. Goals and Non-goals

### 4.1 Goals

#### P0 goals

1. Capture Claude Code runs through hooks.
2. Convert tool calls into a dynamic DAG.
3. Store tool inputs, outputs, errors, durations, and relevant metadata.
4. Capture file diffs and artifacts associated with nodes.
5. Create git-backed or workspace-backed checkpoints around important boundaries.
6. Assign each node a recovery policy.
7. Show an Airflow-like DAG UI with node status and recovery labels.
8. Allow users to inspect logs, outputs, artifacts, diffs, and checkpoint metadata per node.
9. Let users replay from a failed node by restoring the nearest safe checkpoint and relaunching Claude Code with a generated resume prompt.
10. Create replay branches instead of overwriting failed history.

#### P1 goals

1. Allow users to register reusable flows with prompts, repo paths, schedules, and replay policies.
2. Allow manual triggering of registered flows.
3. Add basic scheduling for recurring flows.
4. Add runner heartbeat and run queue.
5. Add cache validity rules by source type.
6. Add manual override for recovery policy classification.
7. Add side-effect labels and warnings.
8. Add lightweight model-based classification for ambiguous commands.
9. Add basic notifications for failed scheduled runs.

#### P2 goals

1. Support deeper integration with Claude Agent SDK.
2. Support additional coding agents.
3. Add team workspaces, shared runners, and hosted deployments.
4. Add approval gates for side-effectful nodes.
5. Add organization policies for unsafe commands.
6. Add comparison view between original failed branch and replay branch.
7. Add evals and success-rate analytics for replay attempts.
8. Add plugin marketplace or adapters for popular agent harnesses.

### 4.2 Non-goals

Runback will not initially:

1. Replace Claude Code or become a full coding agent.
2. Promise deterministic replay of LLM tokens or hidden model reasoning.
3. Guarantee that external websites, APIs, or services are unchanged.
4. Automatically replay dangerous side effects.
5. Act as a general-purpose Airflow replacement.
6. Support every agent framework in the MVP.
7. Support production-grade distributed runners in the MVP.
8. Store user secrets in the hosted backend by default.
9. Guarantee perfect classification of all Bash commands.

---

## 5. Target Users and Personas

### 5.1 Primary MVP persona: Claude Code power user

**Profile:** Individual developer or hackathon builder using Claude Code for coding tasks.

**Needs:**

- Wants to run longer Claude Code tasks with more confidence.
- Wants to inspect what the agent did without digging through raw transcripts.
- Wants to resume failed tasks from a useful point.
- Wants a visual run graph like Airflow or GitHub Actions.

**Example flows:**

- Fix failing tests.
- Add a feature and run the test suite.
- Refactor a module.
- Generate docs.
- Upgrade dependencies.
- Run weekly repository maintenance.

### 5.2 Secondary persona: AI infra engineer

**Profile:** Engineer building internal agent workflows or developer automation.

**Needs:**

- Wants replayable workflows across internal tools.
- Wants auditability of agent actions.
- Wants to prevent accidental reruns of side-effectful actions.
- Wants scheduled or recurring agents with failure recovery.

### 5.3 Future persona: team lead / engineering manager

**Profile:** Team lead adopting coding agents across a team.

**Needs:**

- Wants visibility into agent run success/failure.
- Wants policies around unsafe commands and external side effects.
- Wants metrics on replay savings and failed-run recovery.
- Wants a hosted dashboard.

---

## 6. Core Concepts

### 6.1 Flow

A Flow is a reusable agent task template.

Example:

```text
Name: Weekly dependency upgrade
Repo: /Users/prittam/projects/my-app
Prompt: Upgrade minor dependencies, run tests, fix failures, and summarize changes.
Schedule: Every Monday at 9 AM
Agent: Claude Code
Replay mode: Semi-automatic
Side-effect policy: Label only
```

A Flow contains configuration, not execution history.

### 6.2 Flow version

A Flow version captures a specific revision of the flow prompt and settings. If the user edits a prompt or schedule, future runs should reference the new version while old runs remain tied to the old version.

This prevents confusion when investigating historical runs.

### 6.3 Run

A Run is one execution of a Flow or one ad hoc Claude Code task.

A Run has:

- Run ID
- Flow ID
- Flow version ID
- Status
- Original prompt
- Repo path
- Runner ID
- Started/ended timestamps
- Root branch ID
- Current branch ID
- Failure node, if any
- Recommended recovery point, if any

### 6.4 Node

A Node is a unit of execution in the dynamic DAG.

Examples:

- User prompt
- Tool call
- File mutation
- Checkpoint
- Artifact generation
- Error
- Replay attempt
- Approval request
- Stop / completion

### 6.5 Edge

An Edge connects nodes in the execution graph.

Claude Code runs are dynamic. The DAG is not fully known upfront. Runback builds the DAG from hook events as the agent executes.

### 6.6 Artifact

An Artifact is any output worth preserving, inspecting, caching, or passing to a downstream node.

Examples:

- Tool output
- Terminal log
- Git diff
- File snapshot
- Cached website HTML
- Parsed text
- Normalized JSON
- Generated markdown
- Test report
- Transcript path
- JSON output
- Screenshot
- Patch file

Artifacts should be materialized as files whenever possible. The database should store metadata, provenance, paths, content hashes, cache policy, and node relationships, while the artifact body should live in the local filesystem or object storage.

This is especially important for non-coding workflows such as:

```text
Fetch website
→ Parse HTML
→ LLM normalize
→ Validate schema
→ Append/upsert table
```

In that flow, the website fetch node should output an HTML artifact file, the parser node should consume that file and output a cleaned text or structured extraction artifact, and the LLM normalization node should consume the parsed artifact rather than raw HTML in the prompt.

Recommended artifact storage layout:

```text
.runback/
  runs/
    run_123/
      artifacts/
        fetch_website_1/
          page.html
          metadata.json
        parse_html_1/
          extracted_text.txt
          links.json
        normalize_1/
          normalized.json
```

Artifact metadata example:

```json
{
  "artifact_id": "artifact_html_123",
  "run_id": "run_123",
  "produced_by_node_id": "fetch_website_1",
  "type": "html",
  "path": ".runback/runs/run_123/artifacts/fetch_website_1/page.html",
  "source_url": "https://example.com/menu",
  "content_hash": "sha256:abc123",
  "captured_at": "2026-05-09T10:30:00+08:00",
  "recovery_policy": "reuse_cached"
}
```

Downstream nodes should receive artifact references and a small manifest, not large raw payloads in the prompt.

Example node input manifest:

```json
{
  "inputs": [
    {
      "artifact_id": "artifact_html_123",
      "type": "html",
      "path": ".runback/runs/run_123/artifacts/fetch_website_1/page.html",
      "description": "Cached HTML fetched from restaurant website",
      "source_url": "https://example.com/menu",
      "captured_at": "2026-05-09T10:30:00+08:00"
    }
  ]
}
```

Design principle:

> Node inputs are artifact files plus small metadata. Node outputs are artifact files plus metadata. Replay reuses or regenerates artifacts based on each node's recovery policy.

### 6.7 Checkpoint

A Checkpoint is a restorable workspace state associated with a node or boundary.

For the Claude Code MVP, checkpoints should be git/workspace-backed.

Examples:

- Run start
- Before file mutation
- After file mutation
- Before test/build command
- Before replay
- After successful replay

### 6.8 Recovery policy

Each node receives a recovery policy that tells Runback what to do during replay.

Recommended policies:

```text
rerun
reuse_cached
restore_checkpoint
requires_approval
unsafe
unknown
```

These are more useful than a simple deterministic/non-deterministic label.

### 6.9 Replay branch

A Replay Branch is a new DAG branch created when a user replays from a recovery point.

Replay should never overwrite the failed path.

Example:

```text
Prompt
 → Read files
 → Edit auth.ts
 → Run tests ❌
        └─ Replay #1
             → Edit auth.ts
             → Run tests ✅
```

---

## 7. Recovery Policy Model

### 7.1 Policy definitions

#### rerun

The node can be executed again safely under the restored state.

Examples:

- `npm test`
- `pytest`
- `tsc --noEmit`
- `eslint`
- formatters
- local pure scripts

#### reuse_cached

The node should not be rerun by default. Instead, Runback should reuse its captured output.

Examples:

- WebFetch result
- WebSearch result
- repository scan output
- file read output at a known file hash
- LLM planning output
- documentation lookup

#### restore_checkpoint

The node mutated local state, and replay should restore the workspace to a checkpoint rather than rerun the mutation blindly.

Examples:

- Edit file
- Write file
- Generate file
- Modify lockfile
- Apply patch

#### requires_approval

The node may have an external or irreversible side effect. Runback should never automatically rerun it.

Examples:

- `git push`
- `gh pr create`
- `gh issue comment`
- `npm publish`
- `vercel deploy`
- `docker push`
- `terraform apply`
- `kubectl apply`
- `curl -X POST ...`
- send email
- post Slack message
- write to production database

#### unsafe

The node is destructive or too risky to replay.

Examples:

- `rm -rf`
- `git reset --hard`
- `git clean -fd`
- `dropdb`
- `terraform destroy`
- `kubectl delete`
- `DELETE FROM users`

#### unknown

Runback cannot confidently classify the node.

Default behavior:

- Do not auto-replay.
- Show warning.
- Ask user to manually classify or approve.

### 7.2 Recovery policy examples by Claude Code tool

| Tool | Example | Default policy | Notes |
|---|---|---|---|
| Read | read local file | reuse_cached or rerun | Valid if file hash/checkpoint unchanged |
| Grep | search repo | reuse_cached or rerun | Valid if repo checkpoint unchanged |
| Glob | list files | reuse_cached or rerun | Valid if repo checkpoint unchanged |
| Edit | edit code | restore_checkpoint | Mutation should be captured by diff/checkpoint |
| Write | write file | restore_checkpoint | Mutation should be captured by diff/checkpoint |
| Bash | `npm test` | rerun | Verification step |
| Bash | `npm run build` | rerun | Verification step |
| Bash | `gh pr create` | requires_approval | External side effect |
| Bash | `rm -rf` | unsafe | Destructive |
| WebFetch | read docs | reuse_cached | External read can change; use captured output |
| WebSearch | search web | reuse_cached | Non-deterministic; use captured output |
| MCP tool | unknown | unknown / requires_approval | Depends on tool metadata |

---

## 8. Cache Validity Model

Runback should not use one global cache duration. Each node should have cache validity based on source type.

### 8.1 Local repository reads

Examples:

- Read file
- Grep repo
- Glob files
- Inspect package.json

Validity rule:

```text
Valid while the relevant git checkpoint, file hash, or repo state is unchanged.
```

TTL:

```text
Effectively indefinite if content hash matches.
```

Replay behavior:

```text
Reuse cached output by default if file/repo hash matches.
```

### 8.2 External web/API reads

Examples:

- WebFetch documentation page
- WebSearch result
- GitHub issue fetch
- API GET request
- Website HTML fetch

Validity rule:

```text
Time-based + captured output available.
```

Default TTL:

```text
24 hours.
```

Replay behavior:

```text
Reuse cached output by default during replay, with captured_at timestamp and stale warning if expired.
```

For website parsing workflows, cached HTML should be stored as an artifact file and passed to downstream parser nodes by reference. The replay should not refetch the website unless the user explicitly requests a refresh.

Example replay policy:

```text
Fetch website       → reuse_cached
Parse HTML          → rerun using cached HTML artifact
LLM normalize       → rerun or reuse_cached depending on failure
Validate schema     → rerun
Append/upsert table → requires approval unless idempotent
```

### 8.3 LLM planning outputs

Examples:

- Initial plan
- File selection reasoning
- Task breakdown
- Generated approach

Validity rule:

```text
Valid for the run and replay attempts unless user chooses to regenerate.
```

Default TTL:

```text
Run lifetime + 24 hours.
```

Replay behavior:

```text
Reuse cached plan by default to avoid changing trajectory.
```

### 8.4 Test/build outputs

Examples:

- `npm test`
- `pytest`
- `tsc`
- `eslint`

Validity rule:

```text
Stored for debugging but not considered valid for replay verification.
```

Replay behavior:

```text
Rerun.
```

### 8.5 External side effects

Examples:

- PR created
- Slack message posted
- deployment triggered

Validity rule:

```text
Permanent audit record.
```

Replay behavior:

```text
Never auto-replay. Reuse reference or require approval.
```

### 8.6 Cache policy schema

```ts
type CachePolicy = {
  mode: "content_hash" | "ttl" | "run_lifetime" | "permanent_audit";
  ttlSeconds?: number;
  contentHash?: string;
  capturedAt: string;
  allowStaleForReplay: boolean;
};
```

---

## 9. Product User Flows

### 9.1 First-time setup

1. User installs Runback CLI.
2. User runs `runback init` inside a repo.
3. Runback detects Claude Code availability.
4. Runback configures Claude Code hooks for the project.
5. Runback starts or connects to local backend.
6. User opens Runback frontend.
7. Frontend shows runner online and repo connected.

MVP simplification:

- Run all components locally.
- Use SQLite.
- Use project-level `.claude/settings.local.json` or equivalent local hook config.
- Do not require account auth.

### 9.2 Register a flow

1. User opens Runback frontend.
2. User clicks “New Flow.”
3. User enters:
   - Flow name
   - Repository path
   - Prompt
   - Optional schedule
   - Agent: Claude Code
   - Replay mode
   - Side-effect policy
4. Frontend saves Flow and FlowVersion.
5. Flow appears in flow list.

Example:

```text
Name: Fix failing tests
Repo: /Users/prittam/projects/runback-demo
Prompt: Fix the failing auth tests and make the full test suite pass.
Schedule: none
Replay mode: semi-automatic
Side-effect policy: label only
```

### 9.3 Manual trigger

1. User clicks “Run Flow.”
2. Backend creates a Run with status `queued`.
3. Local runner receives the queued run.
4. Runner creates initial checkpoint.
5. Runner launches Claude Code with the flow prompt and environment variables:
   - `RUNBACK_RUN_ID`
   - `RUNBACK_FLOW_ID`
   - `RUNBACK_BACKEND_URL`
   - `RUNBACK_REPO_PATH`
6. Claude Code hooks stream events to Runback backend.
7. Frontend updates the DAG live.

### 9.4 Scheduled trigger

1. Flow has a schedule.
2. Scheduler creates a queued Run at the scheduled time.
3. Local runner heartbeats and polls/pulls the run.
4. If runner is offline:
   - Run remains queued.
   - UI shows “Waiting for runner.”
   - Optional notification is sent.

### 9.5 Inspect a run

1. User opens a completed or failed Run.
2. UI shows DAG.
3. User clicks a node.
4. Node detail panel shows:
   - Tool name
   - Tool input
   - Tool output
   - Error
   - Duration
   - Recovery policy
   - Classification reason
   - Checkpoint before/after
   - Git diff
   - Artifacts
   - Cache status

### 9.6 Replay failed run

1. A node fails, usually Bash test/build command.
2. Runback finds nearest safe recovery boundary.
3. UI shows recommendation:

```text
Recommended recovery point: checkpoint_after_edit_2
Reason:
- Previous repo reads can be reused.
- File state can be restored.
- Failed node was a rerunnable test command.
- No external side effects occurred after checkpoint.

Will reuse:
- repository scan
- file reads
- previous plan
- failed test output

Will rerun:
- test/fix loop
```

4. User clicks “Replay from checkpoint.”
5. Runback restores workspace.
6. Runback generates resume prompt.
7. Runner relaunches Claude Code.
8. A new DAG branch appears.
9. Replay attempt succeeds or fails.

### 9.7 Website-to-table flow

Runback should also support agentic data workflows in the MVP or near-MVP scope.

Example:

```text
Fetch website
→ Parse HTML
→ LLM normalize
→ Validate schema
→ Append/upsert table
```

This flow demonstrates Runback beyond coding-agent test failure recovery. It shows how Runback handles cached external reads, artifact passing, LLM transforms, validation, and side-effectful writes.

Expected behavior:

1. User registers a flow with URL, target schema, and destination table.
2. Agent fetches website.
3. Runback stores raw HTML as an artifact file.
4. Parser node reads cached HTML artifact and outputs cleaned text or structured extraction.
5. LLM normalization node reads parsed artifact and outputs normalized JSON.
6. Validator node checks schema.
7. Table write node appends or upserts normalized records.
8. If normalization fails, replay reuses cached website HTML and reruns parse/normalize without refetching.
9. If table write fails, replay requires idempotency or user approval before rerunning the write.

Recommended DAG:

```text
WebFetch URL
  output: page.html artifact
        ↓
Parse HTML
  input: page.html artifact
  output: extracted_text.txt / extracted.json
        ↓
LLM Normalize
  input: extracted artifact
  output: normalized.json
        ↓
Validate Schema
        ↓
Append/Upsert Table
```

Replay example:

```text
Failed at: LLM Normalize
Recovery recommendation:
- Reuse cached website HTML from original run.
- Rerun parser using page.html.
- Rerun normalization with optional user-injected context.
- Do not refetch website unless requested.
- Do not write to table until validation passes.
```

User-injected replay context example:

```text
The page contains multiple outlets. Extract only Singapore locations and ignore footer links.
```

Important rule:

> Large artifacts should be passed as files or artifact references, not pasted wholesale into the replay prompt.

---

## 10. Frontend Requirements

### 10.1 Information architecture

Main pages:

1. Dashboard
2. Flows
3. Flow detail
4. Run detail
5. Runner status
6. Settings

### 10.2 Dashboard

Dashboard shows:

- Recent runs
- Failed runs
- Scheduled flows
- Runner status
- Replay success rate
- Time/token savings estimate

### 10.3 Flows page

Flow list columns:

- Name
- Repo
- Schedule
- Last run status
- Last run time
- Runner
- Actions: Run, Edit, Disable

### 10.4 Flow detail page

Flow detail shows:

- Prompt
- Repo path
- Agent type
- Schedule
- Side-effect policy
- Cache policy
- Replay mode
- Flow versions
- Historical runs

### 10.5 Run detail page

Run detail is the core product UI.

Recommended layout:

```text
Left: run metadata and node list
Center: dynamic DAG
Right: node detail panel
Bottom: logs, artifacts, diffs
Top: replay controls and status
```

### 10.6 DAG visualization

DAG node types:

- Prompt
- Tool call
- File mutation
- Checkpoint
- Artifact
- Error
- Replay attempt
- Stop/completion

Node status:

- Pending
- Running
- Success
- Failed
- Skipped
- Reused
- Waiting for approval

Recovery policy color coding:

| Policy | Suggested visual treatment |
|---|---|
| rerun | blue badge |
| reuse_cached | purple badge |
| restore_checkpoint | orange badge |
| requires_approval | yellow badge |
| unsafe | dark/red badge |
| unknown | gray badge |

Execution status should remain visually distinct from recovery policy. For example, a failed `npm test` node can be red for status and blue-labeled as rerunnable.

### 10.7 Node detail panel

Must show:

- Node label
- Event type
- Tool name
- Status
- Recovery policy
- Classification reason
- Start/end/duration
- Tool input
- Tool output
- Error
- Checkpoint before
- Checkpoint after
- Artifacts
- Git diff
- Cache validity
- Replay action
- Manual policy override

### 10.8 Replay recommendation panel

When a failed node is selected, show:

- Recommended recovery point
- Why this recovery point was chosen
- Steps to reuse
- Steps to rerun
- Steps that require approval
- Side-effect warnings
- Resume prompt preview
- Button: “Replay from checkpoint”

### 10.9 Artifact viewer

Artifact viewer should support:

- Logs
- JSON
- Markdown
- Git diff
- File preview
- Test output
- Transcript path/reference

MVP should prioritize:

1. Tool output logs
2. Error logs
3. Git diffs
4. Resume prompt preview

### 10.10 Runner status UI

Show:

- Runner name
- Online/offline
- Last heartbeat
- Current run
- Available repos
- Claude Code availability
- Hook status
- Backend connection status

This is important because scheduled flows depend on a local runner.

---

## 11. CLI and Local Runner Requirements

### 11.1 Why a local runner is required

Runback needs a component running on the developer’s machine because Claude Code, the repository, git state, filesystem, dependencies, and secrets are local.

The backend/frontend cannot safely or directly execute Claude Code on the user’s repo unless running locally.

### 11.2 CLI commands

Recommended MVP commands:

```bash
runback init
runback dev
runback run "Fix the failing tests"
runback claude "Fix the failing tests"
runback ui
runback runner
runback replay <run-id> <node-id>
```

#### `runback init`

- Detects git repo.
- Detects Claude Code installation.
- Creates Runback config.
- Installs project-local Claude Code hooks.
- Verifies backend connectivity.

#### `runback dev`

- Starts local backend.
- Starts frontend.
- Starts runner.
- Uses SQLite.

#### `runback claude <prompt>`

- Creates ad hoc Flow/Run.
- Creates initial checkpoint.
- Launches Claude Code with prompt.
- Streams hook events.

#### `runback runner`

- Starts background runner.
- Sends heartbeat.
- Polls or receives queued runs.
- Executes flows.

#### `runback replay <run-id> <node-id>`

- Finds recovery point.
- Restores checkpoint.
- Generates resume prompt.
- Launches Claude Code.
- Creates replay branch.

### 11.3 Runner responsibilities

The runner must:

- Maintain heartbeat.
- Pick up queued runs.
- Launch Claude Code.
- Set environment variables.
- Manage workspace/checkpoints.
- Stream hook events.
- Store large artifacts locally or upload to backend.
- Restore checkpoints.
- Launch replay attempts.
- Report run status.

### 11.4 Run boundary

For MVP, Runback should launch Claude Code itself:

```bash
runback claude "Fix the failing tests"
```

This gives clean run boundaries and makes replay easier.

Long-term, Runback can support passive observation of existing Claude sessions.

---

## 12. Claude Code Hook Integration

### 12.1 Hook strategy

Runback should use Claude Code hooks to capture lifecycle events. Claude Code hooks can be command hooks, HTTP hooks, MCP hooks, prompt hooks, or agent hooks. For MVP, use HTTP hooks if the local backend is running and command hooks as a fallback.

Recommended MVP:

```text
Claude Code hook event
→ HTTP POST localhost /api/hooks/claude
→ backend normalizes event
→ DB update
→ frontend live update
```

Fallback:

```text
Claude Code hook event
→ local command writes JSONL event
→ backend ingests JSONL
```

### 12.2 Required hook events

P0:

- `UserPromptSubmit`
- `PreToolUse`
- `PostToolUse`
- `PostToolUseFailure`
- `Stop`
- `StopFailure`

P1:

- `PostToolBatch`
- `FileChanged`
- `PermissionRequest`
- `PermissionDenied`
- `SessionStart`
- `SessionEnd`

P2:

- `SubagentStart`
- `SubagentStop`
- `TaskCreated`
- `TaskCompleted`
- `PreCompact`
- `PostCompact`
- `CwdChanged`

### 12.3 Event-to-node mapping

| Claude Code event | Runback behavior |
|---|---|
| UserPromptSubmit | Create root prompt node |
| PreToolUse | Create pending tool node |
| PostToolUse | Mark tool node success and attach output |
| PostToolUseFailure | Mark tool node failed and attach error |
| PostToolBatch | Group parallel/batched tool calls |
| FileChanged | Create file mutation/artifact node or attach to nearest tool node |
| PermissionRequest | Create side-effect/approval node |
| PermissionDenied | Mark approval denied |
| Stop | Mark turn/run segment complete |
| StopFailure | Mark run failed due to stop/session/API issue |
| SessionStart | Create session metadata |
| SessionEnd | Complete session metadata |

### 12.4 Tool handling

First-class tools for MVP:

- Bash
- Read
- Grep
- Glob
- Edit
- Write

All other tools:

- Store event.
- Label as unknown initially.
- Allow manual policy override.

### 12.5 Hook event metadata to store

For each event, store:

- run_id
- flow_id
- session_id
- transcript_path
- cwd
- event_name
- event timestamp
- tool_name
- tool_use_id
- tool_input
- tool_response
- error
- duration
- raw payload path or JSON
- environment metadata

---

## 13. Checkpointing Design

### 13.1 MVP checkpoint backend

Recommended MVP implementation:

1. Use a temporary git worktree or copied repository for each run.
2. Create checkpoints using git commits, hidden refs, or patch snapshots inside the run workspace.
3. Never mutate the user’s main working branch without explicit approval.

For hackathon speed, copied repo may be simplest.

For product credibility, PRD should state:

> Runback stores checkpoints in isolated workspaces using git worktrees, hidden refs, or patch snapshots. It avoids mutating the user's active branch unless explicitly configured.

### 13.2 Checkpoint triggers

Create checkpoints:

- At run start.
- Before Edit/Write.
- After successful Edit/Write.
- Before test/build/lint/typecheck Bash commands.
- On failure.
- Before replay.
- After successful replay.

### 13.3 Checkpoint metadata

Store:

- checkpoint_id
- run_id
- node_id
- branch_id
- label
- git commit/hash/ref
- patch path
- created_at
- repo path
- file hashes
- diff summary
- restore command metadata

### 13.4 Restore behavior

On replay:

1. Stop active run if needed.
2. Determine source checkpoint.
3. Save current state as pre-replay checkpoint.
4. Restore workspace to source checkpoint.
5. Generate resume prompt.
6. Launch Claude Code.
7. Create replay branch.

### 13.5 Checkpoint safety

Runback should never silently destroy user work.

Before restore:

- Detect uncommitted changes in run workspace.
- Save patch snapshot.
- Warn if restoring active user workspace.
- Prefer isolated worktree/copy.

---

## 14. Replay Design

### 14.1 Replay semantics

Runback supports semantic replay from safe recovery boundaries, not deterministic token-level replay.

Semantic replay means:

- Restore the workspace to a known checkpoint.
- Reuse trusted prior outputs.
- Rerun only necessary verification/fix steps.
- Avoid or require approval for side-effectful steps.
- Create a new branch in the DAG.

### 14.2 Recovery point selection

When user selects a failed node, Runback should find the nearest safe recovery boundary by evaluating:

- Is there a checkpoint before the failed node?
- Were there side effects after the checkpoint?
- Are prior reads cache-valid?
- Is the failed node rerunnable?
- Is the workspace restorable?
- Are there unsafe nodes in the replay path?

### 14.3 Replay recommendation output

Example:

```json
{
  "sourceNodeId": "node_bash_test_123",
  "recommendedCheckpointId": "checkpoint_after_edit_2",
  "confidence": 0.86,
  "reason": [
    "Failed node is a test command and can be rerun.",
    "Nearest checkpoint exists after code edits.",
    "Previous file reads are valid under the same repo state.",
    "No external side effects detected after checkpoint."
  ],
  "reuseNodes": ["read_auth_ts", "grep_auth", "llm_plan"],
  "rerunNodes": ["npm_test", "subsequent_fix_loop"],
  "approvalNodes": [],
  "unsafeNodes": []
}
```

### 14.4 Resume prompt generation

Generated prompt should include:

- Original user task.
- Completed steps.
- Cached outputs summary.
- Restored checkpoint label.
- Failure details.
- Explicit instruction not to redo known-good work unless necessary.
- Side-effect warnings.

Template:

```text
You are resuming a failed Claude Code run from a Runback checkpoint.

Original task:
{{original_prompt}}

Completed steps that should be treated as already done:
{{completed_steps}}

Cached context available from the previous run:
{{cached_context_summary}}

The workspace has been restored to:
{{checkpoint_label}}

The previous attempt failed at:
{{failed_node_label}}

Failure output:
{{failure_output}}

Continue from this point. Do not redo completed repository exploration unless necessary. Use the previous failure log and focus on the next fix/test loop.
```

### 14.5 Replay branching

Replay attempts always create new branches.

Branch metadata:

- branch_id
- parent_branch_id
- source_node_id
- source_checkpoint_id
- replay_attempt_id
- created_at
- status

### 14.6 Replay modes

Supported modes:

#### Manual

User reviews recommendation and resume prompt, then starts replay manually.

#### Semi-automatic

User clicks replay; Runback restores checkpoint and launches Claude Code automatically.

#### Automatic

Runback automatically retries on failure based on policy.

MVP should use semi-automatic replay.

### 14.7 Replay session strategy

When replaying from a failed node, Runback should create a new Claude Code session branch rather than continuing the original session in-place.

Recommended MVP strategy:

```text
Restore checkpoint
→ generate replay context bundle
→ launch Claude Code in a new/forked session
→ create new Runback branch
→ stream replay events into that branch
```

Runback should avoid appending replay attempts to the original failed Claude Code session by default. The original session is the audit trail of what happened. Replay is a new recovery attempt that should be isolated and comparable.

Supported strategies:

#### Continue same session

Runback resumes the existing Claude Code session and appends a new prompt.

Pros:
- Preserves full conversation context.
- Simple mental model for small follow-up fixes.

Cons:
- Pollutes the failed session with replay attempts.
- Harder to compare original path vs replay path.
- More likely to inherit stale assumptions or bad context.
- Harder to guarantee clean recovery from restored workspace state.

#### New clean session

Runback starts a fresh Claude Code session from the restored checkpoint and injects a structured replay prompt.

Pros:
- Cleanest isolation.
- Avoids stale or incorrect context.
- Easier to reason about replay as a new branch.
- Better for deterministic recovery from a checkpoint.

Cons:
- Loses useful conversation context unless Runback reconstructs it.
- Requires a high-quality replay context bundle.

#### Forked session branch

Runback uses Claude Code session branching/forking when available, then injects replay context and runs from the restored checkpoint.

Pros:
- Preserves useful prior session context.
- Leaves the original failed session unchanged.
- Aligns naturally with Runback DAG branching.

Cons:
- Still may carry stale assumptions from the original path.
- Requires careful context injection to tell the agent what changed.

Default recommendation:

```text
MVP: new clean session with Runback-generated replay prompt.
Product target: forked session branch when available, with fallback to clean session.
Avoid: mutating the original failed session by default.
```

### 14.8 User-injected replay context

Runback should allow users to add extra context before replaying a node.

This is important because the user may know why the previous run failed or may want to steer the replay more precisely.

Example user-injected context:

```text
The issue is probably in token refresh logic, not login validation. Do not change the database schema. Focus only on auth/session.ts and the failing test.
```

Replay context should be composed from three layers:

```text
1. Runback-generated context
   - original task
   - completed steps
   - cached outputs
   - restored checkpoint
   - failed node details
   - side-effect warnings

2. User-injected context
   - additional instructions
   - hypotheses
   - constraints
   - files to focus on or avoid

3. Agent execution instruction
   - continue from this checkpoint
   - do not redo known-good work unless necessary
   - rerun verification after changes
```

The user should be able to preview and edit the final resume prompt before replay.

Data model addition:

```ts
type ReplayAttempt = {
  ...
  userContext?: string;
  generatedContext: string;
  finalResumePrompt: string;
};
```

MVP behavior:

- Show a text box in the replay modal: “Add extra context for this replay.”
- Append the user context to the generated replay prompt under a clearly labeled section.
- Store the user context and final prompt as part of the ReplayAttempt.
- Display it in the replay branch metadata.

This feature is highly feasible and should be included in the MVP if time allows.

---

## 15. Classification Design

### 15.1 Recommended approach

Use hybrid classification:

```text
Rule-based classifier first
→ lightweight model for ambiguous cases
→ user override
```

Do not rely entirely on a model for safety decisions.

### 15.2 Rule-based classifier

Rules should inspect:

- tool_name
- tool_input
- Bash command string
- file paths
- known command patterns
- HTTP method
- environment hints
- MCP tool metadata if available

Examples:

```text
Read/Grep/Glob → reuse_cached/rerun based on content hash
Edit/Write → restore_checkpoint
Bash npm test/pytest/tsc/eslint → rerun
WebFetch/WebSearch → reuse_cached
Bash git push/gh pr create/npm publish → requires_approval
Bash rm -rf/git reset --hard/dropdb → unsafe
Unknown MCP tool → unknown or requires_approval
```

### 15.3 Lightweight model classifier

Use only for ambiguous commands such as:

```bash
python scripts/sync_customers.py
node scripts/update-index.js
make deploy-preview
curl https://api.example.com/sync
```

Model output:

```json
{
  "recoveryPolicy": "requires_approval",
  "confidence": 0.72,
  "reason": "The command appears to synchronize customer data and may write to an external system.",
  "sideEffectType": "external_write"
}
```

### 15.4 Safety rule

If confidence is low, choose stricter policy.

```text
unknown read-like → unknown/reuse only with warning
unknown mutation-like → requires_approval
unknown destructive-looking → unsafe
```

### 15.5 Manual override

Users can change policy on a node:

- Mark as rerun
- Mark as reuse cached
- Mark as restore checkpoint
- Mark as requires approval
- Mark as unsafe

Overrides should be stored and used in future similar classifications where appropriate.

---

## 16. Side-effect Policy

### 16.1 Definition

A side effect is any action that changes local or external state, especially if rerunning it may cause duplicate, irreversible, or externally visible effects.

### 16.2 Categories

#### No side effect

- Read file
- Grep
- Glob
- Run tests
- Run linter
- Run typechecker

#### Local checkpointable side effect

- Edit file
- Write file
- Generate local artifact
- Modify lockfile
- Apply patch

#### External side effect

- Git push
- Create PR
- Post Slack message
- Send email
- Deploy
- Publish package
- Write to production DB
- API POST/PUT/PATCH/DELETE

#### Destructive side effect

- rm -rf
- git reset --hard
- dropdb
- terraform destroy
- kubectl delete
- database deletes/truncates

### 16.3 MVP behavior

MVP should:

- Label side-effectful nodes.
- Show warning in node panel.
- Exclude side-effectful nodes from automatic replay.
- Optionally block obviously destructive commands if easy.

P1/P2 should:

- Add approval gates.
- Add organization policies.
- Add side-effect idempotency keys where possible.

### 16.4 Table writes and idempotency

The website-to-table workflow introduces a common side effect: appending records to a table.

A naive append can create duplicates during replay:

```text
Replay normalize
→ append same row again
→ duplicate data
```

Runback should classify table writes based on idempotency.

Recommended behavior:

```text
Append without idempotency key
→ requires_approval

Upsert with deterministic idempotency key
→ rerun_safe_side_effect / allowed with warning

Production database write
→ requires_approval by default
```

Recommended idempotency key format:

```text
source_url + content_hash + normalized_entity_id
```

Example:

```text
https://example.com/menu:sha256abc123:chicken-rice-set
```

The destination table should ideally use an upsert pattern:

```sql
INSERT INTO records (..., idempotency_key)
VALUES (...)
ON CONFLICT (idempotency_key)
DO UPDATE SET ...;
```

Runback should store the idempotency key on the write node and show whether replaying the write is safe.

---

## 17. Backend Requirements

### 17.1 Backend responsibilities

The backend should:

- Store flows, runs, nodes, edges, checkpoints, artifacts, replay attempts, and runners.
- Receive Claude hook events.
- Normalize raw events.
- Classify recovery policy.
- Store artifacts and previews.
- Serve DAG data to frontend.
- Manage run queue.
- Manage schedules.
- Track runner heartbeat.
- Generate replay recommendations.
- Generate resume prompts.

### 17.2 MVP deployment mode

For hackathon:

```text
Local Next.js app + API routes + SQLite + local runner
```

Alternative:

```text
Next.js frontend + FastAPI backend + SQLite/Postgres
```

### 17.3 API endpoints

Recommended endpoints:

```http
POST /api/hooks/claude
GET  /api/flows
POST /api/flows
GET  /api/flows/:id
POST /api/flows/:id/run
GET  /api/runs
GET  /api/runs/:id
GET  /api/runs/:id/dag
GET  /api/runs/:id/nodes/:nodeId
POST /api/runs/:id/replay
POST /api/runs/:id/nodes/:nodeId/policy
POST /api/runners/heartbeat
GET  /api/runners
POST /api/artifacts
GET  /api/artifacts/:id
```

### 17.4 Live updates

Options:

- WebSocket
- Server-sent events
- Polling

MVP:

- Poll every 1–2 seconds or use SSE if easy.

---

## 18. Data Model

### 18.1 Flow

```ts
type Flow = {
  id: string;
  name: string;
  description?: string;
  repoPath: string;
  agent: "claude_code";
  activeVersionId: string;
  schedule?: string;
  enabled: boolean;
  createdAt: string;
  updatedAt: string;
};
```

### 18.2 FlowVersion

```ts
type FlowVersion = {
  id: string;
  flowId: string;
  versionNumber: number;
  prompt: string;
  replayMode: "manual" | "semi_automatic" | "automatic";
  sideEffectPolicy: "label_only" | "require_approval" | "block_dangerous";
  cachePolicyJson: unknown;
  createdAt: string;
};
```

### 18.3 Run

```ts
type Run = {
  id: string;
  flowId?: string;
  flowVersionId?: string;
  runnerId?: string;
  status: "queued" | "running" | "failed" | "success" | "cancelled";
  originalPrompt: string;
  repoPath: string;
  workspacePath?: string;
  rootBranchId: string;
  currentBranchId: string;
  failureNodeId?: string;
  recommendedCheckpointId?: string;
  startedAt?: string;
  endedAt?: string;
  createdAt: string;
};
```

### 18.4 Node

```ts
type Node = {
  id: string;
  runId: string;
  branchId: string;
  claudeToolUseId?: string;
  eventType: string;
  type: "prompt" | "tool" | "checkpoint" | "artifact" | "error" | "replay" | "approval" | "stop";
  label: string;
  toolName?: string;
  inputJson?: unknown;
  outputJson?: unknown;
  error?: string;
  status: "pending" | "running" | "success" | "failed" | "skipped" | "reused" | "waiting_approval";
  recoveryPolicy: "rerun" | "reuse_cached" | "restore_checkpoint" | "requires_approval" | "unsafe" | "unknown";
  classificationReason?: string;
  classificationConfidence?: number;
  checkpointBeforeId?: string;
  checkpointAfterId?: string;
  cachePolicyJson?: unknown;
  startedAt?: string;
  endedAt?: string;
  durationMs?: number;
  rawEventPath?: string;
};
```

### 18.5 Edge

```ts
type Edge = {
  id: string;
  runId: string;
  branchId: string;
  sourceNodeId: string;
  targetNodeId: string;
  edgeType: "sequence" | "replay_branch" | "artifact" | "checkpoint";
};
```

### 18.6 Checkpoint

```ts
type Checkpoint = {
  id: string;
  runId: string;
  branchId: string;
  nodeId?: string;
  label: string;
  backend: "git_commit" | "hidden_ref" | "patch" | "worktree" | "copy";
  gitRef?: string;
  gitCommitHash?: string;
  patchPath?: string;
  workspacePath: string;
  diffSummary?: string;
  fileHashesJson?: unknown;
  createdAt: string;
};
```

### 18.7 Artifact

```ts
type Artifact = {
  id: string;
  runId: string;
  nodeId?: string;
  producedByNodeId?: string;
  type:
    | "log"
    | "diff"
    | "file"
    | "html"
    | "text"
    | "transcript"
    | "json"
    | "markdown"
    | "screenshot"
    | "patch";
  path?: string;
  sourceUrl?: string;
  description?: string;
  contentPreview?: string;
  contentHash?: string;
  sizeBytes?: number;
  cachePolicyJson?: unknown;
  createdAt: string;
};
```

### 18.7.1 NodeArtifactEdge

Runback should explicitly track which nodes consume and produce artifacts.

```ts
type NodeArtifactEdge = {
  id: string;
  runId: string;
  nodeId: string;
  artifactId: string;
  direction: "input" | "output";
  required: boolean;
  createdAt: string;
};
```

This allows Runback to answer:

- Which artifact did this node read?
- Which node produced this artifact?
- Which downstream nodes depend on this artifact?
- Can replay reuse this artifact instead of regenerating it?
- Is the artifact stale, pinned, or content-hash valid?

### 18.8 ReplayAttempt

```ts
type ReplayAttempt = {
  id: string;
  runId: string;
  sourceNodeId: string;
  sourceCheckpointId: string;
  parentBranchId: string;
  newBranchId: string;
  resumePrompt: string;
  status: "created" | "running" | "failed" | "success";
  recommendationJson?: unknown;
  createdAt: string;
  startedAt?: string;
  endedAt?: string;
};
```

### 18.9 Runner

```ts
type Runner = {
  id: string;
  name: string;
  machineId?: string;
  status: "online" | "offline" | "busy";
  lastHeartbeatAt?: string;
  currentRunId?: string;
  availableReposJson?: unknown;
  claudeCodeAvailable: boolean;
  version: string;
  createdAt: string;
};
```

---

## 19. Scheduling and Runner Queue

### 19.1 Scheduling model

A scheduled Flow creates queued Runs.

The backend scheduler should:

- Evaluate flow schedules.
- Create queued Run records.
- Assign runs to available runners if possible.
- Mark runs as waiting if no runner is online.

### 19.2 Runner heartbeat

Local runner sends heartbeat every 10–30 seconds.

Heartbeat includes:

- runner_id
- status
- current_run_id
- available repo paths or repo aliases
- Claude Code availability
- version

### 19.3 Queue model

Run queue status:

- queued
- assigned
- running
- failed
- success
- cancelled
- waiting_for_runner

### 19.4 MVP simplification

Scheduling can be P1. For hackathon, manual triggering is enough if replay demo is strong.

---

## 20. Security, Privacy, and Secrets

### 20.1 Sensitive data risks

Runback may capture:

- Source code
- Tool inputs/outputs
- Environment information
- Terminal logs
- API responses
- File paths
- Secrets accidentally printed in logs
- Claude transcripts

### 20.2 MVP security principles

For MVP:

- Run locally by default.
- Store data in local SQLite.
- Do not upload source code to hosted services.
- Do not store raw environment variables.
- Redact common secrets from logs.
- Allow users to delete run data.

### 20.3 Secret redaction

Redact patterns such as:

- API keys
- Bearer tokens
- AWS keys
- GitHub tokens
- OpenAI/Anthropic keys
- Private keys
- `.env` values

### 20.4 Access control

MVP local mode does not need multi-user auth.

Future hosted mode should support:

- User accounts
- Organization workspaces
- Role-based access
- Project-level permissions
- Runner registration tokens

---

## 21. Reliability and Edge Cases

### 21.1 Duplicate hook events

Use idempotency keys:

- run_id
- event_name
- tool_use_id
- event timestamp
- raw event hash

### 21.2 Hook receiver offline

If HTTP hook receiver is unavailable:

- Command hook fallback writes JSONL.
- Runner ingests buffered events later.
- UI shows event delay.

### 21.3 Claude Code run exits unexpectedly

Runback should:

- Mark run failed.
- Save final checkpoint.
- Attach logs.
- Recommend replay if checkpoint exists.

### 21.4 Checkpoint restore conflict

If workspace has uncommitted changes:

- Save patch.
- Warn user.
- Prefer isolated workspace.

### 21.5 Classification uncertainty

If node is unknown:

- Do not auto-replay.
- Show warning.
- Ask for override.

### 21.6 Large outputs

Store previews in DB and full output as artifact files.

### 21.7 Long-running commands

Track:

- start time
- heartbeat
- timeout
- partial logs
- interrupted status

---

## 22. Success Metrics

### 22.1 Hackathon demo success

The MVP succeeds if it can show:

1. Claude Code run captured through hooks.
2. Dynamic DAG of tool calls.
3. Logs/output per node.
4. File diffs/artifacts per node.
5. Recovery policy labels.
6. Checkpoint created before/after file mutation.
7. Failed test/build node.
8. Replay recommendation.
9. Replay branch created.
10. Replay run succeeds or visibly resumes from restored checkpoint.

### 22.2 Product metrics

Long-term metrics:

- Runs captured
- Runs failed
- Runs replayed
- Replay success rate
- Average time saved per replay
- Average nodes skipped/reused per replay
- Number of side effects detected
- Number of unsafe replays prevented
- User retention
- Flows scheduled
- Runs per flow

### 22.3 Developer experience metrics

- Time from install to first captured run
- Time from failure to replay
- Percentage of failed runs with recommended recovery point
- Accuracy of recovery policy classification
- Manual override rate

---

## 23. MVP Scope

### 23.1 P0 MVP

Must build:

1. Local Runback app.
2. Claude Code hook receiver.
3. CLI command to launch Claude Code.
4. Event ingestion and normalization.
5. SQLite/Postgres storage.
6. Dynamic DAG UI.
7. Node detail panel.
8. Tool logs and outputs.
9. Basic artifact storage as files plus metadata.
10. Node input/output artifact references.
11. Git/workspace checkpointing.
12. Rule-based recovery policy classifier.
13. Failed node detection.
14. Replay recommendation.
15. Semi-automatic replay that restores checkpoint and relaunches Claude Code.
16. Replay branch visualization.
17. Compact replay context generation with optional user-injected context.

Optional but strong MVP second flow:

18. Website-to-table demo flow:
    - fetch website
    - cache HTML artifact
    - parse artifact
    - LLM normalize
    - validate schema
    - append/upsert table with idempotency key

### 23.2 P1 after MVP

Should build:

1. Flow registration.
2. Manual flow trigger.
3. Flow versioning.
4. Runner heartbeat.
5. Run queue.
6. Basic scheduling.
7. Cache validity display.
8. Manual policy override.
9. Side-effect warnings.
10. Lightweight model classifier for ambiguous commands.

### 23.3 P2 future

Could build:

1. Approval gates.
2. Hosted backend.
3. Team workspaces.
4. Additional coding-agent adapters.
5. Claude Agent SDK integration.
6. Distributed runners.
7. Advanced replay analytics.
8. Replay diff comparison.
9. Organization policy management.

---

## 24. MVP Demo Script

### 24.1 Setup

Use a demo repo with a failing test or intentionally buggy implementation.

### 24.2 User action

```bash
runback claude "Fix the failing auth test and make the test suite pass."
```

### 24.3 Claude Code behavior

Claude Code:

1. Reads files.
2. Greps for auth implementation.
3. Edits source file.
4. Runs tests.
5. Tests fail.
6. Attempts or waits.

### 24.4 Runback visualization

Runback shows:

```text
Prompt
→ Read auth.ts
→ Read auth.test.ts
→ Grep auth
→ Edit auth.ts
→ Checkpoint after edit
→ Bash npm test ❌
```

The failed Bash node shows:

- Command
- stdout/stderr
- error
- duration
- policy: rerun
- recommended checkpoint: after edit

### 24.5 Replay

User clicks:

```text
Replay from checkpoint_after_edit
```

Runback:

1. Restores workspace.
2. Generates resume prompt.
3. Relaunches Claude Code.
4. Creates branch.

DAG becomes:

```text
Prompt
→ Read auth.ts
→ Read auth.test.ts
→ Grep auth
→ Edit auth.ts
→ Checkpoint after edit
→ Bash npm test ❌
        └─ Replay #1
             → Edit auth.ts
             → Bash npm test ✅
```

### 24.6 Demo punchline

Runback did not restart from scratch. It reused known-good repository exploration and resumed from a safe checkpoint.

---

## 25. Technical Implementation Plan

### 25.1 Suggested stack

MVP stack:

- Frontend: Next.js + React Flow
- Backend: Next.js API routes or FastAPI
- DB: SQLite for hackathon, Postgres later
- CLI: Node.js/TypeScript or Python
- Runner: same CLI process
- Checkpoints: copied repo or git worktree + commits/patches
- Hook receiver: local HTTP endpoint
- Live updates: polling or SSE

### 25.2 Implementation phases

#### Phase 1: Basic event capture

- Install Claude Code hooks.
- Receive hook JSON.
- Store raw events.
- Display event list.

#### Phase 2: DAG conversion

- Normalize events into nodes.
- Link nodes sequentially.
- Use tool_use_id to update pending nodes.
- Display DAG.

#### Phase 3: Artifacts/logs

- Store tool inputs/outputs.
- Store errors.
- Store output previews.
- Show node detail panel.

#### Phase 4: Checkpoints

- Create initial checkpoint.
- Create checkpoints around Edit/Write and test commands.
- Store checkpoint metadata.
- Show checkpoint badges.

#### Phase 5: Recovery policy

- Implement rule-based classifier.
- Add policy badges.
- Add classification reason.

#### Phase 6: Replay

- Select failed node.
- Find checkpoint.
- Generate resume prompt.
- Restore workspace.
- Relaunch Claude Code.
- Create replay branch.

#### Phase 7: Flows

- Register flows.
- Trigger flows from UI.
- Add flow run history.

#### Phase 8: Scheduling and runner heartbeat

- Add runner process.
- Add heartbeat.
- Add queued runs.
- Add simple schedules.

---

## 26. Risks and Mitigations

### 26.1 Risk: replay is not truly deterministic

Mitigation:

- Position as semantic replay.
- Use cached outputs and checkpoints.
- Avoid claiming token-level deterministic replay.

### 26.2 Risk: hooks do not expose enough internal context

Mitigation:

- Focus on execution-level replay.
- Store tool calls, outputs, diffs, and checkpoints.
- Parse transcript later if needed.

### 26.3 Risk: checkpointing corrupts user workspace

Mitigation:

- Use isolated worktree/copy for MVP.
- Save patches before restore.
- Never mutate active branch silently.

### 26.4 Risk: command classification is wrong

Mitigation:

- Rule-first classifier.
- Conservative defaults.
- Manual override.
- Side-effect approval gates later.

### 26.5 Risk: scheduling expands scope too much

Mitigation:

- Keep scheduling P1.
- MVP should focus on run capture and replay.

### 26.6 Risk: frontend becomes too complex

Mitigation:

- Prioritize run detail DAG and node panel.
- Defer analytics/dashboard polish.

---

## 27. Open Questions

1. Should MVP use copied repo or git worktree for checkpoints?
2. Should the hook receiver be HTTP-only or HTTP + JSONL fallback?
3. Should flow scheduling be included in hackathon MVP or deferred?
4. Should Runback block obviously destructive commands in MVP or only label them?
5. Should replay launch Claude Code automatically or show a generated command first?
6. How much Claude transcript parsing is needed for useful resume prompts?
7. Should cached LLM planning outputs be summarized by Runback or stored verbatim?
8. Should users be able to edit the resume prompt before replay?
9. Should Runback support project-level hook installation only, or also user-level hooks?
10. Should Runback store full artifacts in DB, filesystem, or object storage?

---

## 28. Recommended Decisions

For the current hackathon/product direction, recommended defaults are:

1. **Integration:** Claude Code hooks first.
2. **Run boundary:** Runback launches Claude Code for MVP.
3. **Replay mode:** Semi-automatic.
4. **Checkpoint backend:** Copied repo or git worktree for MVP.
5. **DAG behavior:** Always branch on replay.
6. **Classifier:** Rule-based first, lightweight model for ambiguous cases.
7. **Side effects:** Label only for MVP, approval gates later.
8. **Scheduling:** P1, not core hackathon demo.
9. **Cache TTL:** Source-specific, not global.
10. **Positioning:** Checkpointing and replay first, observability second.

---

## 29. Final Product Definition

Runback is a checkpointing and replay layer for Claude Code workflows. Users can register or trigger agent flows, observe execution as an Airflow-style dynamic DAG, inspect logs and artifacts per tool call, and recover failed runs from safe checkpoints. Runback uses Claude Code hooks to capture tool calls, git/workspace checkpoints to preserve recoverable state, and recovery policies to decide whether nodes should be rerun, reused from cache, restored from checkpoint, require approval, or be treated as unsafe.

The core user value is simple:

> When a long-running agent workflow fails, Runback lets you resume from the right point instead of starting over.
