# Runback

`claude --resume` resumes a conversation. Runback resumes a workflow.

Runback is checkpointing and replay infrastructure for long-horizon Claude Code
workflows. It captures tool calls as a dynamic DAG, snapshots workspace state
at policy-driven points, classifies each step's recovery policy, and lets you
replay from the nearest safe checkpoint with a fresh Claude session. A
side-effect ledger prevents PR creation, Slack posts, deploys, and similar
actions from firing twice on replay.

This MVP ships two demos in `demos/`:

1. **Autonomous backlog ticket fixing** - Claude works through 5 tickets in
   `BACKLOG.md`, opens a fake PR per ticket, fails on ticket #4, and can be
   replayed from the failed checkpoint with a one-line hint.
2. **Website-to-report** - Claude reads 5 cached HTML fixtures, writes a trends
   report, and pauses for approval before posting to a fake Slack CLI.

See `docs/superpowers/specs/2026-05-09-runback-mvp-design.md` for the design.

## Repo layout

```text
runback/
├── apps/server/                 # FastAPI backend
├── apps/web/                    # Next.js frontend
├── packages/runback-cli/        # Python CLI
├── demos/backlog/               # Demo 1 fixture
├── demos/research/              # Demo 2 fixture
├── scripts/                     # one-command demo drivers
├── tests/e2e/                   # slow end-to-end tests
└── docs/                        # contracts, plans, storyboard, bug bash
```

## Install

Prereqs:

- Python 3.11+ and `uv`
- Node.js 20+ and `pnpm` 9+
- Claude Code CLI 2.1.137+
- Git 2.40+

```bash
git clone https://github.com/<your-org>/runback.git
cd runback

uv sync
corepack pnpm install
(cd demos/backlog && npm install)
```

Verify:

```bash
uv run runback --help
uv run pytest -q
corepack pnpm --filter @runback/web test
corepack pnpm --filter @runback/web typecheck
```

## Dev

```bash
uv run runback dev
```

This boots FastAPI on `http://localhost:8000`, Next.js on
`http://localhost:3000`, and the runner daemon on its Unix socket.

In another terminal:

```bash
uv run runback claude "list the files in this repo and tell me what each does"
```

Open `http://localhost:3000` to watch the run DAG.

## Run the demos

Both demos reset to a clean state, prepend fake side-effect CLIs to `PATH`, and
launch Runback with a canonical prompt.

```bash
bash scripts/demo-1.sh
bash scripts/demo-2.sh
bash scripts/dry-run-all.sh
```

Walkthroughs:

- `demos/backlog/run-demo.md`
- `demos/research/run-demo.md`

## Run the tests

```bash
uv run pytest -q
corepack pnpm --filter @runback/web test
uv run pytest tests/e2e -m slow -v
```

The slow e2e suite boots or reuses a Runback stack and requires the Claude CLI.

## Bug bash

Before tagging a release, walk through `docs/bug-bash.md`. It covers DAG
rendering, replay modal behavior, side-effect ledger behavior, demo scripts,
and CLI edge cases.

## Architecture cheat sheet

```text
Developer machine
  runback claude "..."
        |
        v
  runner daemon ---- hook events ----> FastAPI + SQLite
        |                                |
        | worktrees + checkpoints         | SSE
        v                                v
  git workspace                    Next.js DAG UI
```

- **CLI** launches runs and dispatches replays.
- **Runner daemon** owns worktrees, starts Claude, and restores checkpoints.
- **Backend** ingests hooks, normalizes events into the DAG, classifies
  recovery policies, and records side effects.
- **Frontend** renders live run state via SSE.

## Screenshots

Screenshot placeholders live under `docs/screenshots/` and should be replaced
before recording the public demo.

## License

MIT. All demo content is hypothetical and not affiliated with any real company.
