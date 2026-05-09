"""`runback replay` tests."""
from __future__ import annotations

from click.testing import CliRunner
from runback.__main__ import cli


def test_replay_posts_to_backend(monkeypatch, httpx_mock) -> None:
    monkeypatch.setenv("RUNBACK_BACKEND_URL", "http://127.0.0.1:8000")
    httpx_mock.add_response(
        method="POST",
        url="http://127.0.0.1:8000/api/runs/run_a/replay",
        json={"id": "ra_1", "new_branch_id": "b_replay_1"},
        status_code=202,
    )
    result = CliRunner().invoke(cli, ["replay", "run_a", "n1"])
    assert result.exit_code == 0, result.output
    assert "b_replay_1" in result.output


def test_replay_handles_backend_error(monkeypatch, httpx_mock) -> None:
    monkeypatch.setenv("RUNBACK_BACKEND_URL", "http://127.0.0.1:8000")
    httpx_mock.add_response(
        method="POST",
        url="http://127.0.0.1:8000/api/runs/run_z/replay",
        status_code=500,
        text="kaboom",
    )
    result = CliRunner().invoke(cli, ["replay", "run_z", "n1"])
    assert result.exit_code != 0
    assert "500" in result.output
