"""End-to-end tests for demo 1."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.slow
def test_demo_1_unattended_first_pass(runback_stack, latest_run_id, side_effects, reset_demo_backlog):
    result = subprocess.run(
        ["bash", str(REPO_ROOT / "scripts" / "demo-1.sh")],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"demo-1.sh failed: {result.stdout}\n{result.stderr}"

    run_id = latest_run_id(timeout=600)
    pr_rows = side_effects(run_id, kind="gh_pr_create")
    assert len(pr_rows) >= 3, f"expected >=3 PRs, got {len(pr_rows)}: {pr_rows}"

    keys = [row["idempotency_key"] for row in pr_rows]
    assert len(keys) == len(set(keys)), f"duplicate idempotency keys: {keys}"

    fake_prs = list((REPO_ROOT / "demos" / "backlog" / ".fake-prs").glob("*.json"))
    assert len(fake_prs) >= 3, f"expected >=3 fake PR files, got {len(fake_prs)}"

    for path in fake_prs:
        data = json.loads(path.read_text())
        assert data.get("fakePR") is True
        assert data.get("url", "").startswith("https://github.com/runback-demo/backlog/pull/")
        assert data.get("head", "").startswith("fix/issue-")


@pytest.mark.slow
def test_demo_1_uses_gh_stub(reset_demo_backlog):
    demo_dir = REPO_ROOT / "demos" / "backlog"
    env = {"PATH": f"{demo_dir / '.fake-bin'}:/usr/bin:/bin"}
    result = subprocess.run(["which", "gh"], env=env, capture_output=True, text=True)
    assert result.returncode == 0
    assert str(demo_dir / ".fake-bin" / "gh") in result.stdout
