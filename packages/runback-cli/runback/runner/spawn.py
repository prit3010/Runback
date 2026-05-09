"""Spawn `claude` with the argv and environment Runback needs."""
from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ClaudeSpawnSpec:
    run_id: str
    prompt: str
    workspace_path: Path
    hook_forwarder_path: Path
    runback_bin_dir: Path
    permission_mode: str = "bypassPermissions"
    print_mode: bool = True
    extra_env: dict[str, str] | None = None


def spawn_claude(spec: ClaudeSpawnSpec) -> subprocess.Popen:
    """Launch Claude Code in `workspace_path` and return its process handle."""
    claude_bin = shutil.which("claude")
    if claude_bin is None:
        raise FileNotFoundError("`claude` not found on PATH")

    argv = [claude_bin, "--permission-mode", spec.permission_mode]
    if spec.print_mode:
        argv.append("--print")
    argv.append(spec.prompt)

    env = {
        **os.environ,
        "RUNBACK_RUN_ID": spec.run_id,
        "RUNBACK_HOOK_FORWARD": str(spec.hook_forwarder_path),
        "RUNBACK_BIN_DIR": str(spec.runback_bin_dir),
        "PATH": f"{spec.runback_bin_dir}:{os.environ.get('PATH', '')}",
    }
    if spec.extra_env:
        env.update(spec.extra_env)

    return subprocess.Popen(argv, cwd=str(spec.workspace_path), env=env)
