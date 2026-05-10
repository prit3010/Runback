"""Shared fixtures for end-to-end demo tests."""
from __future__ import annotations

import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
API_BASE = "http://127.0.0.1:8000"


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        try:
            sock.connect(("127.0.0.1", port))
            return True
        except OSError:
            return False


def _wait_for_url(url: str, timeout: float = 60.0) -> None:
    deadline = time.monotonic() + timeout
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        try:
            response = httpx.get(url, timeout=1)
            if response.status_code < 500:
                return
        except Exception as exc:  # noqa: BLE001
            last_err = exc
        time.sleep(0.5)
    raise TimeoutError(f"Timed out waiting for {url}; last error: {last_err}")


@pytest.fixture(scope="session")
def runback_stack() -> Iterator[dict[str, str]]:
    """Boot `uv run runback dev` for the duration of the test session."""
    for cmd in ("uv", "claude", "git"):
        if shutil.which(cmd) is None:
            pytest.skip(f"e2e tests require '{cmd}' on PATH")

    proc: subprocess.Popen[str] | None = None
    if not _port_open(8000):
        env = {**os.environ, "RUNBACK_DEMO_MODE": "1"}
        proc = subprocess.Popen(
            ["uv", "run", "runback", "dev"],
            cwd=str(REPO_ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            preexec_fn=os.setsid if sys.platform != "win32" else None,
        )
        try:
            _wait_for_url(f"{API_BASE}/api/runs", timeout=120)
        except TimeoutError:
            if proc.poll() is not None:
                logs = proc.stdout.read() if proc.stdout else ""
                pytest.fail(f"runback dev exited early. logs:\n{logs}")
            raise

    yield {"api": API_BASE}

    if proc is not None:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            proc.wait(timeout=10)
        except Exception:  # noqa: BLE001
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception:  # noqa: BLE001
                pass


@pytest.fixture
def latest_run_id(runback_stack: dict[str, str]) -> Callable[..., str]:
    def _poll(timeout: float = 600.0, terminal_states: tuple[str, ...] = ("success", "failed", "paused")) -> str:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            response = httpx.get(f"{runback_stack['api']}/api/runs", timeout=5)
            response.raise_for_status()
            items = response.json()
            if items:
                run = items[0]
                if run.get("status") in terminal_states:
                    return run["id"]
            time.sleep(2)
        raise TimeoutError(f"No run reached terminal state within {timeout}s")

    return _poll


@pytest.fixture
def side_effects(runback_stack: dict[str, str]) -> Callable[[str, str | None], list[dict]]:
    def _get(run_id: str, kind: str | None = None) -> list[dict]:
        response = httpx.get(f"{runback_stack['api']}/api/runs/{run_id}/dag", timeout=5)
        response.raise_for_status()
        rows = response.json().get("side_effects", [])
        return [row for row in rows if row.get("kind") == kind] if kind else rows

    return _get


@pytest.fixture
def reset_demo_backlog() -> Iterator[None]:
    seed = REPO_ROOT / "demos" / "backlog" / "seed.sh"
    subprocess.run(["bash", str(seed)], check=True)
    yield
    subprocess.run(["bash", str(seed)], check=True)


@pytest.fixture
def reset_demo_research() -> Iterator[None]:
    seed = REPO_ROOT / "demos" / "research" / "seed.sh"
    subprocess.run(["bash", str(seed)], check=True)
    yield
    subprocess.run(["bash", str(seed)], check=True)
