"""Runner-side runtime configuration."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _runner_socket() -> Path:
    value = os.environ.get("RUNBACK_RUNNER_SOCKET") or os.environ.get(
        "RUNBACK_RUNNER_SOCKET_PATH", "/tmp/runback-runner.sock"
    )
    return Path(value)


@dataclass
class RunnerSettings:
    backend_url: str = field(
        default_factory=lambda: os.environ.get("RUNBACK_BACKEND_URL", "http://127.0.0.1:8000")
    )
    runtime_root: Path = field(
        default_factory=lambda: Path(os.environ.get("RUNBACK_RUNTIME_ROOT", ".runback")).resolve()
    )
    runner_socket: Path = field(default_factory=_runner_socket)
    web_port: int = field(default_factory=lambda: int(os.environ.get("RUNBACK_WEB_PORT", "3000")))
    server_port: int = field(
        default_factory=lambda: int(os.environ.get("RUNBACK_SERVER_PORT", "8000"))
    )


def get_settings() -> RunnerSettings:
    return RunnerSettings()


def run_dir(run_id: str, settings: RunnerSettings | None = None) -> Path:
    s = settings or get_settings()
    return s.runtime_root / "runs" / run_id


def workspace_dir(run_id: str, settings: RunnerSettings | None = None) -> Path:
    return run_dir(run_id, settings) / "ws"


def hooks_bin_dir(settings: RunnerSettings | None = None) -> Path:
    s = settings or get_settings()
    return s.runtime_root / "bin"
