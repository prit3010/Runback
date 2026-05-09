"""Hook-setup primitive tests."""
from __future__ import annotations

import json
import os
from pathlib import Path

from runback.runner.hooks_setup import (
    install_forwarder,
    install_settings_local,
    merge_hook_config,
    setup_hooks,
)


def test_install_forwarder_copies_and_chmod(tmp_path: Path) -> None:
    path = install_forwarder(bin_dir=tmp_path / "bin")
    assert path.exists()
    assert os.access(path, os.X_OK)
    assert "RUNBACK_RUN_ID" in path.read_text()
    assert "/api/hooks/claude" in path.read_text()


def test_install_settings_local_writes_fresh_config(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    path = install_settings_local(workspace=workspace)
    cfg = json.loads(path.read_text())
    for event in ("UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop"):
        assert event in cfg["hooks"]


def test_merge_preserves_existing_user_hooks() -> None:
    merged = merge_hook_config(
        {
            "hooks": {
                "PreToolUse": [
                    {"matcher": "*", "hooks": [{"type": "command", "command": "echo user"}]}
                ]
            },
            "permissions": {"allow_bash": False},
        }
    )
    pre = merged["hooks"]["PreToolUse"]
    assert any("user" in entry["hooks"][0]["command"] for entry in pre)
    assert any("RUNBACK_HOOK_FORWARD" in entry["hooks"][0]["command"] for entry in pre)
    assert merged["permissions"]["allow_bash"] is False


def test_setup_hooks_end_to_end(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    forwarder = setup_hooks(workspace=workspace, runback_bin_dir=tmp_path / ".runback" / "bin")
    assert forwarder.exists()
    cfg = json.loads((workspace / ".claude" / "settings.local.json").read_text())
    assert cfg["hooks"]["PreToolUse"][-1]["hooks"][0]["command"] == "$RUNBACK_HOOK_FORWARD"
