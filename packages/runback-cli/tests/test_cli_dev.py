"""`runback runner` and `runback dev` smoke tests."""
from __future__ import annotations

import os
import subprocess
import sys
import time
import uuid
from pathlib import Path


def test_runner_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "runback", "runner", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "daemon" in result.stdout.lower()


def test_runner_creates_socket_then_exits_on_sigint(tmp_path: Path) -> None:
    sock = Path(f"/tmp/runback-runner-{uuid.uuid4().hex}.sock")
    env = {
        **os.environ,
        "RUNBACK_RUNNER_SOCKET": str(sock),
        "RUNBACK_RUNTIME_ROOT": str(tmp_path / ".runback"),
    }
    proc = subprocess.Popen(
        [sys.executable, "-m", "runback", "runner"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        deadline = time.time() + 5
        while time.time() < deadline and not sock.exists():
            time.sleep(0.1)
        assert sock.exists(), "socket never appeared"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
    assert not sock.exists()


def test_dev_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "runback", "dev", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "backend" in result.stdout.lower()
