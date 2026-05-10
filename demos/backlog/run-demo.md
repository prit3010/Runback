# Demo 1 Walkthrough - Autonomous Backlog Ticket Fixing

**Total runtime:** about 3 minutes.

## Prereqs

- Repo cloned, deps installed with `uv sync`, `pnpm install`, and `(cd demos/backlog && npm install)`.
- Runback dev stack runnable with `uv run runback dev`.

## Setup

```bash
bash demos/backlog/seed.sh
uv run runback dev
```

Open http://localhost:3000 in a browser.

## Run

```bash
bash scripts/demo-1.sh
```

The script re-seeds the fixture, prepends `.fake-bin/` to `PATH`, enables
`RUNBACK_DEMO_MODE=1`, then calls `runback claude` or `uv run runback claude`
from the demo directory.

## What you should see

1. `UserPromptSubmit`, `Read BACKLOG.md`, and `TodoWrite` nodes appear.
2. Tickets #1 through #3 create fake PR ledger files under `.fake-prs/`.
3. Ticket #4 fails on email validation.
4. Open the failed node and replay from the checkpoint with this hint:

   `Hint: the email validation regex should accept + in the local part.`

5. Ticket #4 succeeds, ticket #5 runs, and the final ledger has 5 fake PRs.

## Verify

```bash
ls demos/backlog/.fake-prs/*.json | wc -l
jq -s 'map(.head) | sort' demos/backlog/.fake-prs/*.json
```

## Reset

```bash
bash demos/backlog/seed.sh
```
