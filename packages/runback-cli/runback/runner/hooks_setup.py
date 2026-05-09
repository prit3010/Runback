"""Hook-installation primitive."""
from __future__ import annotations

import json
import stat
from importlib import resources
from pathlib import Path
from typing import Any


def _template() -> dict[str, Any]:
    text = resources.files("runback.hooks").joinpath("settings_template.json").read_text()
    return json.loads(text)


def install_forwarder(*, bin_dir: Path) -> Path:
    bin_dir.mkdir(parents=True, exist_ok=True)
    src = resources.files("runback.hooks").joinpath("forward-hook.sh")
    dest = bin_dir / "forward-hook.sh"
    dest.write_text(src.read_text())
    dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return dest


def merge_hook_config(existing: dict[str, Any] | None) -> dict[str, Any]:
    template = _template()
    out = dict(existing or {})
    out_hooks = dict(out.get("hooks", {}))
    for event, entries in template["hooks"].items():
        existing_entries = list(out_hooks.get(event, []))
        already_installed = any(
            any(hook.get("command") == "$RUNBACK_HOOK_FORWARD" for hook in entry.get("hooks", []))
            for entry in existing_entries
        )
        out_hooks[event] = existing_entries if already_installed else existing_entries + entries
    out["hooks"] = out_hooks
    return out


def install_settings_local(*, workspace: Path) -> Path:
    cfg_dir = workspace / ".claude"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    path = cfg_dir / "settings.local.json"
    existing: dict[str, Any] | None = None
    if path.exists():
        try:
            existing = json.loads(path.read_text())
        except json.JSONDecodeError:
            existing = None
    path.write_text(json.dumps(merge_hook_config(existing), indent=2) + "\n")
    return path


def setup_hooks(*, workspace: Path, runback_bin_dir: Path) -> Path:
    forwarder = install_forwarder(bin_dir=runback_bin_dir)
    install_settings_local(workspace=workspace)
    return forwarder
