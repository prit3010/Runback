"""Spawn primitive tests.

These use a fake `claude` binary so CI and local development do not require the
real Claude Code CLI to be installed.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from runback.runner.spawn import ClaudeSpawnSpec, spawn_claude


@pytest.fixture
def fake_claude(tmp_path: Path) -> Path:
    """A fake `claude` executable that records argv + env to JSON and exits 0."""
    bin_dir = tmp_path / "fake-bin"
    bin_dir.mkdir()
    fake = bin_dir / "claude"
    record = tmp_path / "claude-invocation.json"
    fake.write_text(
        f"""#!/usr/bin/env python3
import json, os, sys
out = {{
    "argv": sys.argv,
    "env_RUNBACK_RUN_ID": os.environ.get("RUNBACK_RUN_ID"),
    "env_RUNBACK_HOOK_FORWARD": os.environ.get("RUNBACK_HOOK_FORWARD"),
    "env_PATH_starts_with_runback": os.environ.get("PATH", "").startswith(
        os.environ.get("RUNBACK_BIN_DIR", "/never")
    ),
    "cwd": os.getcwd(),
}}
with open({str(record)!r}, "w") as f:
    json.dump(out, f)
sys.exit(0)
"""
    )
    fake.chmod(0o755)
    return bin_dir


def test_spawn_claude_records_correct_argv_env_and_cwd(
    tmp_path: Path, fake_claude: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    bin_dir = tmp_path / "rb-bin"
    bin_dir.mkdir()
    forwarder = bin_dir / "forward-hook.sh"
    forwarder.write_text("#!/bin/sh\nexit 0\n")
    forwarder.chmod(0o755)

    monkeypatch.setenv("PATH", f"{fake_claude}:{os.environ['PATH']}")
    monkeypatch.setenv("RUNBACK_BIN_DIR", str(bin_dir))

    spec = ClaudeSpawnSpec(
        run_id="run_x",
        prompt="say hi",
        workspace_path=workspace,
        hook_forwarder_path=forwarder,
        runback_bin_dir=bin_dir,
        permission_mode="bypassPermissions",
        print_mode=True,
    )
    proc = spawn_claude(spec)
    proc.wait(timeout=5)
    assert proc.returncode == 0

    record = json.loads((tmp_path / "claude-invocation.json").read_text())
    assert "claude" in record["argv"][0]
    assert "--print" in record["argv"]
    assert "--permission-mode" in record["argv"]
    assert "bypassPermissions" in record["argv"]
    assert "say hi" in record["argv"]
    assert record["env_RUNBACK_RUN_ID"] == "run_x"
    assert record["env_RUNBACK_HOOK_FORWARD"] == str(forwarder)
    assert Path(record["cwd"]).resolve() == workspace.resolve()


def test_spawn_claude_without_print_mode_omits_flag(
    tmp_path: Path, fake_claude: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    forwarder = tmp_path / "fwd.sh"
    forwarder.write_text("#!/bin/sh\n")
    forwarder.chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake_claude}:{os.environ['PATH']}")
    spec = ClaudeSpawnSpec(
        run_id="run_y",
        prompt="x",
        workspace_path=workspace,
        hook_forwarder_path=forwarder,
        runback_bin_dir=tmp_path,
        permission_mode="bypassPermissions",
        print_mode=False,
    )
    proc = spawn_claude(spec)
    proc.wait(timeout=5)
    record = json.loads((tmp_path / "claude-invocation.json").read_text())
    assert "--print" not in record["argv"]


def test_spawn_claude_raises_on_missing_binary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    forwarder = tmp_path / "fwd.sh"
    forwarder.write_text("#!/bin/sh\n")
    forwarder.chmod(0o755)
    monkeypatch.setenv("PATH", "/nonexistent")
    spec = ClaudeSpawnSpec(
        run_id="run_z",
        prompt="x",
        workspace_path=workspace,
        hook_forwarder_path=forwarder,
        runback_bin_dir=tmp_path,
        permission_mode="bypassPermissions",
        print_mode=True,
    )
    with pytest.raises(FileNotFoundError):
        spawn_claude(spec)
