"""End-to-end smoke: full stack plus real Claude via `runback claude`.

This is opt-in because it launches the real Claude Code CLI.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

pytestmark = pytest.mark.slow


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_url(url: str, timeout: float = 8.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = httpx.get(url, timeout=0.5)
            if response.status_code < 500:
                return
        except Exception:
            time.sleep(0.1)
    raise RuntimeError(f"not ready: {url}")


def _wait_socket(path: Path, timeout: float = 8.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if path.exists():
            return
        time.sleep(0.05)
    raise RuntimeError(f"socket not created: {path}")


def test_real_claude_run_via_cli(tmp_path: Path) -> None:
    if os.environ.get("RUNBACK_REAL_CLAUDE_E2E") != "1":
        pytest.skip("set RUNBACK_REAL_CLAUDE_E2E=1 to launch the real Claude CLI")
    if subprocess.run(["which", "claude"], capture_output=True).stdout.strip() == b"":
        pytest.skip("claude CLI not on PATH")

    server_port = _free_port()
    runtime = tmp_path / ".runback"
    runtime.mkdir()
    db = runtime / "runback.db"
    sock = Path(f"/tmp/runback-e2e-{os.getpid()}-{server_port}.sock")
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "greeting.txt").write_text("hello world")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A"],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init"],
        cwd=repo,
        check=True,
    )

    env = {
        **os.environ,
        "RUNBACK_DB_PATH": str(db),
        "RUNBACK_RUNTIME_ROOT": str(runtime),
        "RUNBACK_RUNNER_SOCKET": str(sock),
        "RUNBACK_BACKEND_URL": f"http://127.0.0.1:{server_port}",
    }
    subprocess.run(
        [
            sys.executable,
            "-c",
            "from runback_server.models import *; "
            "from runback_server.ingest.archive import EventDedup; "
            "from runback_server.ingest.groups import TodoState; "
            "from runback_server.db import create_all; create_all()",
        ],
        cwd=Path(__file__).resolve().parents[3] / "apps" / "server",
        env=env,
        check=True,
    )
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "runback_server.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(server_port),
        ],
        cwd=Path(__file__).resolve().parents[3] / "apps" / "server",
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    runner = subprocess.Popen(
        [sys.executable, "-m", "runback", "runner"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_url(f"http://127.0.0.1:{server_port}/openapi.json")
        _wait_socket(sock)
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "runback",
                "claude",
                "Read greeting.txt and tell me the first word. Use one Read tool call.",
            ],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert proc.returncode == 0, proc.stderr
        run_id = next(token for token in proc.stdout.split() if token.startswith("run_"))

        deadline = time.time() + 30
        nodes_seen = 0
        while time.time() < deadline:
            response = httpx.get(f"http://127.0.0.1:{server_port}/api/runs/{run_id}/dag")
            if response.status_code == 200:
                nodes_seen = len(response.json().get("nodes", []))
                if nodes_seen >= 1:
                    break
            time.sleep(0.5)
        assert nodes_seen >= 1
        assert (runtime / "runs" / run_id / "ws").exists()
        refs = subprocess.run(["git", "show-ref"], cwd=repo, capture_output=True, text=True)
        assert f"refs/runback/{run_id}/0" in refs.stdout
    finally:
        runner.terminate()
        server.terminate()
        for proc in (runner, server):
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
        try:
            sock.unlink()
        except FileNotFoundError:
            pass
