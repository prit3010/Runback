"""Shared pytest fixtures for runner tests."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def tmp_git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "src"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    (repo / "README.md").write_text("hello\n")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-qm", "initial")
    return repo


@pytest.fixture
def tmp_runback_root(tmp_path: Path) -> Path:
    rb = tmp_path / ".runback"
    rb.mkdir()
    (rb / "runs").mkdir()
    (rb / "bin").mkdir()
    return rb
