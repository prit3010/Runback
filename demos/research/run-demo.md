# Demo 2 Walkthrough - Website-to-Report

**Total runtime:** about 3 minutes.

## Prereqs

- Repo cloned, deps installed.
- Runback dev stack running with `uv run runback dev`.

## Setup

```bash
bash demos/research/seed.sh
```

Open http://localhost:3000.

## Run

```bash
bash scripts/demo-2.sh
```

The script re-seeds the fixture, prepends `.fake-bin/` to `PATH`, sets
`RUNBACK_FIXTURE_DIR`, and invokes Runback with `prompt.md`.

## What you should see

1. `UserPromptSubmit` and `Read urls.txt` appear.
2. Five URL groups read cached fixture files.
3. The agent writes `report.md`.
4. Before posting to Slack, it asks for confirmation.
5. The fake Slack post appears in `.fake-slack/` after approval.

## Verify

```bash
test -s demos/research/report.md && echo "report exists"
ls demos/research/.fake-slack/*.txt | wc -l
```

## Reset

```bash
bash demos/research/seed.sh
```
