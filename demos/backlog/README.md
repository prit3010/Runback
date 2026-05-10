# Demo 1 Fixture: Backlog Ticket Fixing

This is a deliberately broken Node.js app used by `scripts/demo-1.sh`.

- `BACKLOG.md` lists 5 tickets the demo's Claude session works through.
- `src/` contains the app source. Five files have bugs corresponding to the 5 tickets.
- `tests/` has a passing `baseline.test.js` plus 5 failing tests, one per ticket.
- `solutions/` contains the reference fixes, hidden from the agent via `.claudeignore`.
- `.fake-bin/gh` intercepts `gh pr create` so the demo never touches real GitHub.
- `seed.sh` resets to a clean buggy state and is idempotent.

To reset and run manually:

    ./seed.sh
    npm test

The demo is invoked from the repo root via `bash scripts/demo-1.sh`.
