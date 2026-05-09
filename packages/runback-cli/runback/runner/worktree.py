"""Git worktree and hidden-ref primitives."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class WorktreeError(RuntimeError):
    """Failure in a worktree primitive."""


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=check,
        )
    except subprocess.CalledProcessError as exc:
        raise WorktreeError(f"git {' '.join(args)} failed: {exc.stderr.strip()}") from exc


def _is_git_repo(path: Path) -> bool:
    if not path.exists():
        return False
    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        cwd=str(path),
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def create_worktree(*, repo_root: Path, worktree_path: Path, base_ref: str) -> None:
    if not _is_git_repo(repo_root):
        raise WorktreeError(f"not a git repo: {repo_root}")
    if worktree_path.exists():
        raise WorktreeError(f"worktree path already exists: {worktree_path}")
    worktree_path.parent.mkdir(parents=True, exist_ok=True)
    _git(repo_root, "worktree", "add", "--detach", str(worktree_path), base_ref)


def list_worktrees(*, repo_root: Path) -> list[dict[str, str]]:
    proc = _git(repo_root, "worktree", "list", "--porcelain")
    entries: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if not line.strip():
            if current:
                entries.append(current)
                current = {}
            continue
        if line.startswith("worktree "):
            current["path"] = line.split(" ", 1)[1]
        elif line.startswith("HEAD "):
            current["head"] = line.split(" ", 1)[1]
        elif line.startswith("branch "):
            current["branch"] = line.split(" ", 1)[1]
        elif line == "detached":
            current["detached"] = "true"
    if current:
        entries.append(current)
    return entries


def update_hidden_ref(*, worktree_path: Path, ref_name: str, target: str) -> None:
    if not ref_name.startswith("refs/runback/"):
        raise WorktreeError(f"refusing to update non-runback ref: {ref_name}")
    _git(worktree_path, "update-ref", ref_name, target)


def list_runback_refs(*, repo_root: Path, run_id: str) -> list[str]:
    proc = _git(repo_root, "for-each-ref", "--format=%(refname)", f"refs/runback/{run_id}/")
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def delete_hidden_refs(*, repo_root: Path, run_id: str) -> None:
    for ref in list_runback_refs(repo_root=repo_root, run_id=run_id):
        _git(repo_root, "update-ref", "-d", ref)


def is_clean_worktree(worktree_path: Path) -> bool:
    if not _is_git_repo(worktree_path):
        return False
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(worktree_path),
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0 and proc.stdout.strip() == ""


def cleanup_worktree(*, repo_root: Path, worktree_path: Path, run_id: str) -> None:
    if worktree_path.exists():
        try:
            _git(repo_root, "worktree", "remove", "-f", str(worktree_path))
        except WorktreeError:
            _git(repo_root, "worktree", "prune", check=False)
            if worktree_path.exists():
                shutil.rmtree(worktree_path, ignore_errors=True)
    delete_hidden_refs(repo_root=repo_root, run_id=run_id)
