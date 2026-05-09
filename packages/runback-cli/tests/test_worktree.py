"""Worktree primitive tests. Real git, no mocks."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from runback.runner.worktree import (
    WorktreeError,
    cleanup_worktree,
    create_worktree,
    delete_hidden_refs,
    is_clean_worktree,
    list_runback_refs,
    list_worktrees,
    update_hidden_ref,
)


def _run(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout


def test_create_worktree_makes_detached_head(tmp_git_repo: Path, tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    create_worktree(repo_root=tmp_git_repo, worktree_path=ws, base_ref="HEAD")
    assert (ws / "README.md").exists()
    assert _run(ws, "rev-parse", "--abbrev-ref", "HEAD").strip() == "HEAD"


def test_create_worktree_alongside_existing_worktrees(
    tmp_git_repo: Path, tmp_path: Path
) -> None:
    other = tmp_path / "user-wt"
    subprocess.run(
        ["git", "worktree", "add", "-b", "user-branch", str(other)],
        cwd=tmp_git_repo,
        check=True,
        capture_output=True,
    )
    ws = tmp_path / "runback-ws"
    create_worktree(repo_root=tmp_git_repo, worktree_path=ws, base_ref="HEAD")
    paths = {w["path"] for w in list_worktrees(repo_root=tmp_git_repo)}
    assert str(other.resolve()) in paths or str(other) in paths
    assert str(ws.resolve()) in paths or str(ws) in paths


def test_create_worktree_rejects_existing_path(tmp_git_repo: Path, tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    with pytest.raises(WorktreeError):
        create_worktree(repo_root=tmp_git_repo, worktree_path=ws, base_ref="HEAD")


def test_create_worktree_rejects_non_git_repo(tmp_path: Path) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()
    with pytest.raises(WorktreeError):
        create_worktree(repo_root=plain, worktree_path=tmp_path / "ws", base_ref="HEAD")


def test_update_hidden_ref_creates_and_overwrites(tmp_git_repo: Path, tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    create_worktree(repo_root=tmp_git_repo, worktree_path=ws, base_ref="HEAD")
    sha = _run(ws, "rev-parse", "HEAD").strip()
    ref = "refs/runback/run_test/0"
    update_hidden_ref(worktree_path=ws, ref_name=ref, target=sha)
    assert sha in _run(tmp_git_repo, "show-ref", ref)

    subprocess.run(["git", "commit", "--allow-empty", "-qm", "next"], cwd=ws, check=True)
    sha2 = _run(ws, "rev-parse", "HEAD").strip()
    update_hidden_ref(worktree_path=ws, ref_name=ref, target=sha2)
    out = _run(tmp_git_repo, "show-ref", ref)
    assert sha2 in out and sha not in out


def test_hidden_refs_invisible_in_branch_listing(tmp_git_repo: Path, tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    create_worktree(repo_root=tmp_git_repo, worktree_path=ws, base_ref="HEAD")
    update_hidden_ref(
        worktree_path=ws,
        ref_name="refs/runback/run_x/0",
        target=_run(ws, "rev-parse", "HEAD").strip(),
    )
    branches = _run(tmp_git_repo, "branch", "-a")
    assert "refs/runback" not in branches
    assert "run_x" not in branches


def test_list_and_delete_runback_refs(tmp_git_repo: Path, tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    create_worktree(repo_root=tmp_git_repo, worktree_path=ws, base_ref="HEAD")
    sha = _run(ws, "rev-parse", "HEAD").strip()
    update_hidden_ref(worktree_path=ws, ref_name="refs/runback/run_a/0", target=sha)
    update_hidden_ref(worktree_path=ws, ref_name="refs/runback/run_a/1", target=sha)
    update_hidden_ref(worktree_path=ws, ref_name="refs/runback/run_b/0", target=sha)
    assert sorted(list_runback_refs(repo_root=tmp_git_repo, run_id="run_a")) == [
        "refs/runback/run_a/0",
        "refs/runback/run_a/1",
    ]
    delete_hidden_refs(repo_root=tmp_git_repo, run_id="run_a")
    assert list_runback_refs(repo_root=tmp_git_repo, run_id="run_a") == []


def test_is_clean_worktree(tmp_git_repo: Path, tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    create_worktree(repo_root=tmp_git_repo, worktree_path=ws, base_ref="HEAD")
    assert is_clean_worktree(ws) is True
    (ws / "dirty.txt").write_text("x")
    assert is_clean_worktree(ws) is False


def test_cleanup_worktree_removes_dir_and_refs(tmp_git_repo: Path, tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    create_worktree(repo_root=tmp_git_repo, worktree_path=ws, base_ref="HEAD")
    sha = _run(ws, "rev-parse", "HEAD").strip()
    update_hidden_ref(worktree_path=ws, ref_name="refs/runback/run_x/0", target=sha)
    cleanup_worktree(repo_root=tmp_git_repo, worktree_path=ws, run_id="run_x")
    assert not ws.exists()
    assert list_runback_refs(repo_root=tmp_git_repo, run_id="run_x") == []
