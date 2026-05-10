# Demo 2 Fixture: Website-to-Report

This is the fixture for `scripts/demo-2.sh`.

- `urls.txt` contains 5 intentionally unreachable URLs.
- `fixtures/page1.html` through `page5.html` are cached HTML pages.
- `prompt.md` tells the agent to read fixtures via `RUNBACK_FIXTURE_DIR`.
- `.fake-bin/slack-cli` writes posts to `.fake-slack/`.
- `seed.sh` clears `.fake-slack/` and deletes generated `report.md`.

## Why fixtures instead of real WebFetch?

Live competitor sites are unstable, slow, and create audit-trail noise. The demo
is about Runback replay, caching, and side-effect behavior, so the fixture
affordance is explicit in `prompt.md`.

## Reset

```bash
bash demos/research/seed.sh
```
