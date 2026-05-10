# Pre-Release Bug Bash Checklist

Run this checklist before tagging a release. Mark an item `[x]` only when the
pass criteria are verified.

**Last full pass:** Not yet run.

## Section A - DAG rendering

- [ ] **A1.** Empty run page shows a waiting placeholder.
- [ ] **A2.** First node renders within 1 second of `UserPromptSubmit`.
- [ ] **A3.** A run with 50 nodes renders smoothly.
- [ ] **A4.** A run with 100+ nodes remains navigable.
- [ ] **A5.** Edge direction is correct.
- [ ] **A6.** Auto-layout does not overlap node labels.

## Section B - Color codes

- [ ] **B1.** `reuse_cached` nodes are cyan.
- [ ] **B2.** `rerun` nodes are orange.
- [ ] **B3.** `restore_checkpoint` nodes are blue.
- [ ] **B4.** `requires_approval` nodes are red.
- [ ] **B5.** `unsafe` nodes are dark red with a stop icon.
- [ ] **B6.** Failed nodes show a red border.

## Section C - Groups

- [ ] **C1.** `TodoWrite` with `Ticket #N` opens a group.
- [ ] **C2.** Completed TodoWrite closes the group.
- [ ] **C3.** Collapsed groups show child count.
- [ ] **C4.** Expanding a group reveals child nodes.
- [ ] **C5.** Replay creates a sibling group.

## Section D - Node detail panel

- [ ] **D1.** Clicking a node opens the detail panel.
- [ ] **D2.** Tool input is rendered as JSON.
- [ ] **D3.** Tool output preview is truncated safely.
- [ ] **D4.** Edit nodes show a diff.
- [ ] **D5.** Failed nodes show error output.
- [ ] **D6.** Policy and classification reason are visible.
- [ ] **D7.** Manual policy override persists.

## Section E - Replay modal

- [ ] **E1.** Failed node shows replay CTA.
- [ ] **E2.** Modal lists recovery point.
- [ ] **E3.** Modal lists reused nodes.
- [ ] **E4.** Modal lists rerun nodes.
- [ ] **E5.** Executed side effects are marked as not re-fired.
- [ ] **E6.** Resume prompt is editable.
- [ ] **E7.** Edited resume prompt is passed to the replay run.
- [ ] **E8.** Cancel closes without launching replay.
- [ ] **E9.** Replay is disabled when no checkpoint exists.

## Section F - Side-effect ledger

- [ ] **F1.** `gh pr create` records a `gh_pr_create` row.
- [ ] **F2.** `slack-cli post` records a `slack_post` row.
- [ ] **F3.** Duplicate commands reuse existing ledger rows.
- [ ] **F4.** Changed Slack message creates a new key.
- [ ] **F5.** Ledger panel sorts rows consistently.
- [ ] **F6.** Ledger row links to source node.

## Section G - Checkpoints

- [ ] **G1.** Run-start checkpoint is visible.
- [ ] **G2.** Pre-edit checkpoints are created.
- [ ] **G3.** Pre-test checkpoints are created.
- [ ] **G4.** Checkpoint shows underlying git ref.
- [ ] **G5.** Restoring a checkpoint leaves clean status.

## Section H - Live updates

- [ ] **H1.** Second tab shows the same DAG.
- [ ] **H2.** SSE reconnects after sleep.
- [ ] **H3.** Backgrounded tab reconciles missed state.
- [ ] **H4.** Dashboard status updates without refresh.

## Section I - Error states

- [ ] **I1.** Backend down gives a clear CLI error.
- [ ] **I2.** Backend recovery accepts later hooks.
- [ ] **I3.** Malformed hook returns 400.
- [ ] **I4.** Killed Claude subprocess marks run failed.
- [ ] **I5.** Replay with no checkpoint returns a clear error.

## Section J - Demo-specific

- [ ] **J1.** Backlog seed is idempotent.
- [ ] **J2.** Research seed is idempotent.
- [ ] **J3.** `scripts/demo-1.sh` exits 0 when stack is up.
- [ ] **J4.** `scripts/demo-1.sh` exits non-zero when stack is down.
- [ ] **J5.** `scripts/demo-2.sh` exits 0 when stack is up.
- [ ] **J6.** `gh` stub blocks duplicate PRs.
- [ ] **J7.** `slack-cli` stub blocks duplicate posts.
- [ ] **J8.** `RUNBACK_FIXTURE_DIR` is honored.
- [ ] **J9.** `RUNBACK_DEMO_MODE=1` is present in demo env.

## Section K - CLI behavior

- [ ] **K1.** `runback --help` lists core commands.
- [ ] **K2.** `runback claude` without prompt errors clearly.
- [ ] **K3.** `runback init` is idempotent.
- [ ] **K4.** `runback dev` shuts down cleanly on SIGINT.

## Section L - Concurrency

- [ ] **L1.** Two runs create separate worktrees.
- [ ] **L2.** Hidden refs are unique per run.
- [ ] **L3.** Concurrent SQLite writes do not lock out each other.
- [ ] **L4.** Two replays create distinct branch IDs.

## Sign-off

```text
[ ] All blocking items pass
[ ] Triaged non-blockers logged as issues
[ ] Operator:
[ ] Date:
```
