# 90-Second Demo Recording Storyboard

Target length: **90 seconds** for the backlog demo's autonomous portion plus
replay. Total runtime including intro and outro is about 2 minutes.

## Setup before recording

1. Terminal A runs `uv run runback dev`.
2. Browser is open to `http://localhost:3000`.
3. Terminal B is in the repo root.
4. Run `bash demos/backlog/seed.sh` immediately before recording.
5. Use 18pt terminal font and browser zoom around 110%.

## Beat sheet

| Time | Surface | Action | Caption |
|------|---------|--------|---------|
| 0:00 | Terminal B | Run `bash scripts/demo-1.sh`. | "Five tickets. One command." |
| 0:05 | Browser | New run appears on dashboard. | "Runback opens a workflow run." |
| 0:09 | Browser | Click the run. DAG begins drawing. | "Every Claude tool call is a node." |
| 0:13 | Browser | Ticket #1 group opens. | "Ticket boundaries become groups." |
| 0:18 | Browser | PR side-effect node appears. | "External actions are classified." |
| 0:25 | Browser | Tickets #2 and #3 complete. | "Three PRs ledgered." |
| 0:38 | Browser | Ticket #4 test node turns red. | "The agent hits a real failure." |
| 0:42 | Browser | Click failed node. | "Replay from the failure." |
| 0:45 | Browser | Replay modal shows recovery point and reuse list. | "Reuse what already happened." |
| 0:50 | Browser | Add regex hint to the resume prompt. | "Add one-line steering." |
| 0:58 | Browser | Click Replay. | "Fresh Claude session, scoped replay." |
| 1:05 | Browser | Ticket #4 succeeds. | "Fixed." |
| 1:12 | Browser | Ticket #5 runs. | "Continue the workflow." |
| 1:18 | Browser | Ledger shows 5 PRs. | "Five PRs. None duplicated." |
| 1:22 | Terminal B | Run `ls demos/backlog/.fake-prs/*.json | wc -l`. | "Verified on disk." |
| 1:25 | Browser | Close-up on side-effect ledger. | "Runback resumes a workflow." |
| 1:30 | Outro | Logo or repo URL. | "" |

## Demo 2 cut-down

| Time | Surface | Action | Caption |
|------|---------|--------|---------|
| 1:30 | Terminal B | Run `bash scripts/demo-2.sh`. | "Different workflow, same machinery." |
| 1:35 | Browser | Five URL groups read cached fixtures. | "Cached fetches." |
| 1:42 | Browser | Synthesis node is replayed. | "Rerun only what is needed." |
| 1:55 | Browser | Slack side-effect remains ledgered. | "External actions never double-fire." |

## Common pitfalls

- Run both `seed.sh` scripts before each take.
- Confirm Terminal B inherits the stubbed `PATH` from the demo driver.
- Pause after editing the resume prompt before clicking Replay.
- Keep the autonomous portion sped up; keep replay at normal speed.

## Editing notes

Use bottom-third captions, 32pt sans-serif text, and speed up the 0:13-0:38
autonomous section at 2x.
