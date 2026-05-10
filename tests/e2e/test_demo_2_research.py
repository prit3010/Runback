"""End-to-end tests for demo 2."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.slow
def test_demo_2_unattended_first_pass(runback_stack, latest_run_id, side_effects, reset_demo_research):
    result = subprocess.run(
        ["bash", str(REPO_ROOT / "scripts" / "demo-2.sh")],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"demo-2.sh failed: {result.stdout}\n{result.stderr}"

    run_id = latest_run_id(timeout=600, terminal_states=("success", "failed", "paused"))
    slack_rows = side_effects(run_id, kind="slack_post")
    assert len(slack_rows) <= 1, f"expected <=1 slack post, got {len(slack_rows)}: {slack_rows}"

    slack_files = list((REPO_ROOT / "demos" / "research" / ".fake-slack").glob("*.txt"))
    assert len(slack_files) <= 1, f"expected <=1 slack file, got {len(slack_files)}"

    if slack_files:
        body = slack_files[0].read_text()
        assert "channel=#growth" in body
        assert "---" in body

    report = REPO_ROOT / "demos" / "research" / "report.md"
    if report.exists():
        assert report.stat().st_size > 0


@pytest.mark.slow
def test_demo_2_slack_stub_deduplicates(reset_demo_research):
    demo_dir = REPO_ROOT / "demos" / "research"
    env = {
        "PATH": f"{demo_dir / '.fake-bin'}:/usr/bin:/bin",
        "RUNBACK_DEMO_RESEARCH_DIR": str(demo_dir),
    }
    first = subprocess.run(
        ["slack-cli", "post", "--channel", "#growth", "--message", "hello world"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    second = subprocess.run(
        ["slack-cli", "post", "--channel", "#growth", "--message", "hello world"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "posted to #growth" in first.stdout
    assert "duplicate post suppressed" in second.stderr
    assert len(list((demo_dir / ".fake-slack").glob("*.txt"))) == 1
