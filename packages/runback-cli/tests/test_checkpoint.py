"""Checkpoint primitive tests."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from runback.http import BackendError
from runback.runner.checkpoint import CheckpointSpec, create_checkpoint, restore_checkpoint
from runback.runner.worktree import create_worktree


def _git_head(path: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=path, capture_output=True, text=True, check=True
    ).stdout.strip()


def test_create_checkpoint_writes_commit_ref_and_posts_row(
    tmp_git_repo: Path, tmp_path: Path, httpx_mock
) -> None:
    ws = tmp_path / "ws"
    create_worktree(repo_root=tmp_git_repo, worktree_path=ws, base_ref="HEAD")
    httpx_mock.add_response(
        method="POST",
        url="http://127.0.0.1:8000/api/runs/run_t/checkpoints",
        json={"id": "cp_xyz", "git_ref": "refs/runback/run_t/0"},
        status_code=201,
    )
    row = create_checkpoint(
        CheckpointSpec(
            run_id="run_t",
            branch_id="branch_root",
            n=0,
            label="test cp",
            repo_root=tmp_git_repo,
            workspace_path=ws,
            node_id=None,
        )
    )
    assert row["id"] == "cp_xyz"
    assert _git_head(ws) in subprocess.run(
        ["git", "show-ref", "refs/runback/run_t/0"],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def test_create_checkpoint_commits_dirty_changes(
    tmp_git_repo: Path, tmp_path: Path, httpx_mock
) -> None:
    ws = tmp_path / "ws"
    create_worktree(repo_root=tmp_git_repo, worktree_path=ws, base_ref="HEAD")
    (ws / "new.txt").write_text("data")
    httpx_mock.add_response(
        method="POST",
        url="http://127.0.0.1:8000/api/runs/run_d/checkpoints",
        json={"id": "cp_d"},
        status_code=201,
    )
    create_checkpoint(
        CheckpointSpec("run_d", "b", 0, "dirty", tmp_git_repo, ws, None)
    )
    assert "new.txt" in subprocess.run(
        ["git", "show", "--name-only", "--format=", "HEAD"],
        cwd=ws,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def test_create_checkpoint_propagates_backend_error(
    tmp_git_repo: Path, tmp_path: Path, httpx_mock
) -> None:
    ws = tmp_path / "ws"
    create_worktree(repo_root=tmp_git_repo, worktree_path=ws, base_ref="HEAD")
    httpx_mock.add_response(
        method="POST",
        url="http://127.0.0.1:8000/api/runs/run_f/checkpoints",
        status_code=500,
        text="boom",
    )
    with pytest.raises(BackendError):
        create_checkpoint(CheckpointSpec("run_f", "b", 0, "x", tmp_git_repo, ws, None))


def test_restore_checkpoint_resets_and_cleans(
    tmp_git_repo: Path, tmp_path: Path, httpx_mock
) -> None:
    ws = tmp_path / "ws"
    create_worktree(repo_root=tmp_git_repo, worktree_path=ws, base_ref="HEAD")
    httpx_mock.add_response(
        method="POST",
        url="http://127.0.0.1:8000/api/runs/run_r/checkpoints",
        json={"id": "cp_r"},
        status_code=201,
    )
    create_checkpoint(CheckpointSpec("run_r", "b", 0, "r", tmp_git_repo, ws, None))
    (ws / "after.txt").write_text("after")
    (ws / "untracked.txt").write_text("untracked")
    subprocess.run(["git", "add", "after.txt"], cwd=ws, check=True)
    restore_checkpoint(workspace_path=ws, ref_name="refs/runback/run_r/0")
    assert not (ws / "after.txt").exists()
    assert not (ws / "untracked.txt").exists()
