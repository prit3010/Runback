"""`runback init` tests."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from click.testing import CliRunner
from runback.__main__ import cli


def _mk_git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    (path / "f").write_text("x")
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "f"],
        cwd=path,
        check=True,
    )
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init"],
        cwd=path,
        check=True,
    )


def test_init_writes_settings_local_and_forwarder(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _mk_git_repo(repo)
    monkeypatch.chdir(repo)
    monkeypatch.setenv("RUNBACK_RUNTIME_ROOT", str(repo / ".runback"))
    result = CliRunner().invoke(cli, ["init"])
    assert result.exit_code == 0, result.output
    assert os.access(repo / ".runback" / "bin" / "forward-hook.sh", os.X_OK)
    assert "$RUNBACK_HOOK_FORWARD" in (repo / ".claude" / "settings.local.json").read_text()


def test_init_rejects_non_git_repo(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["init"])
    assert result.exit_code != 0
    assert "git" in result.output.lower()
