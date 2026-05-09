"""Checkpoint primitive: create and restore."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runback.http import BackendClient
from runback.runner.worktree import WorktreeError, is_clean_worktree, update_hidden_ref


@dataclass
class CheckpointSpec:
    run_id: str
    branch_id: str
    n: int
    label: str
    repo_root: Path
    workspace_path: Path
    node_id: str | None


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "user.email=runback@local", "-c", "user.name=runback", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
    )


def _ref_for(run_id: str, n: int) -> str:
    return f"refs/runback/{run_id}/{n}"


def create_checkpoint(spec: CheckpointSpec, client: BackendClient | None = None) -> dict[str, Any]:
    if not spec.workspace_path.exists():
        raise WorktreeError(f"workspace missing: {spec.workspace_path}")
    if is_clean_worktree(spec.workspace_path):
        _git(spec.workspace_path, "commit", "--allow-empty", "-qm", f"runback: {spec.label}")
    else:
        _git(spec.workspace_path, "add", "-A")
        _git(spec.workspace_path, "commit", "-qm", f"runback: {spec.label}")

    head = _git(spec.workspace_path, "rev-parse", "HEAD").stdout.strip()
    ref_name = _ref_for(spec.run_id, spec.n)
    update_hidden_ref(worktree_path=spec.workspace_path, ref_name=ref_name, target=head)

    body = {
        "label": spec.label,
        "backend": "hidden_ref",
        "git_ref": ref_name,
        "git_commit_hash": head,
        "workspace_path": str(spec.workspace_path),
        "branch_id": spec.branch_id,
        "node_id": spec.node_id,
    }
    if client is None:
        with BackendClient() as owned_client:
            return owned_client.post_checkpoint(run_id=spec.run_id, checkpoint=body)
    return client.post_checkpoint(run_id=spec.run_id, checkpoint=body)


def restore_checkpoint(*, workspace_path: Path, ref_name: str) -> None:
    _git(workspace_path, "reset", "--hard", ref_name)
    _git(workspace_path, "clean", "-fd")
