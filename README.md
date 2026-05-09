# Runback

Checkpointing and replay infrastructure for long-horizon Claude Code workflows.

See `docs/superpowers/specs/2026-05-09-runback-mvp-design.md` for the design.

## Repo layout

- `apps/server/` - FastAPI backend (Python 3.11+)
- `apps/web/` - Next.js 15 frontend
- `packages/runback-cli/` - Python CLI + runner daemon
- `docs/contracts/` - frozen interface specs
- `docs/superpowers/specs/` - design docs
- `docs/superpowers/plans/` - implementation plans

## Quickstart

```bash
# Python deps (uses uv)
uv sync

# Node deps (uses pnpm)
pnpm install

# Run tests
pytest && pnpm --filter web typecheck
```
