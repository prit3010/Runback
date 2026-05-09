"""Runner daemon tests."""
from __future__ import annotations

import json
import os
import re
import socket
import uuid
from pathlib import Path

import anyio
import pytest
from runback.runner.daemon import RunnerDaemon


@pytest.fixture
def fake_claude(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "fake-claude"
    bin_dir.mkdir()
    fake = bin_dir / "claude"
    fake.write_text("#!/bin/sh\necho fake claude ran\nsleep 0.05\n")
    fake.chmod(0o755)
    return bin_dir


def _send(sock: Path, body: dict[str, object]) -> dict[str, object]:
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(str(sock))
    client.sendall((json.dumps(body) + "\n").encode())
    data = b""
    while not data.endswith(b"\n"):
        chunk = client.recv(4096)
        if not chunk:
            break
        data += chunk
    client.close()
    return json.loads(data.decode().strip())


async def _wait_socket(sock: Path) -> None:
    for _ in range(50):
        if sock.exists():
            return
        await anyio.sleep(0.05)
    raise AssertionError("socket not created")


@pytest.mark.anyio("asyncio")
async def test_start_run_provisions_worktree_and_spawns_claude(
    tmp_path: Path, tmp_git_repo: Path, fake_claude: Path, monkeypatch, httpx_mock
) -> None:
    monkeypatch.setenv("PATH", f"{fake_claude}:{os.environ['PATH']}")
    monkeypatch.setenv("RUNBACK_RUNTIME_ROOT", str(tmp_path / ".runback"))
    httpx_mock.add_response(
        method="POST",
        url="http://127.0.0.1:8000/api/runs",
        json={"id": "x"},
        status_code=201,
    )
    httpx_mock.add_response(
        method="POST",
        url=re.compile(r"http://127\.0\.0\.1:8000/api/runs/.*/checkpoints"),
        json={"id": "cp_x"},
        status_code=201,
    )
    httpx_mock.add_response(
        method="GET",
        url=re.compile(r"http://127\.0\.0\.1:8000/api/runs/.*/dag"),
        json={"nodes": []},
        status_code=200,
        is_reusable=True,
        is_optional=True,
    )
    sock = _short_socket()
    daemon = RunnerDaemon(socket_path=sock)
    async with anyio.create_task_group() as tg:
        tg.start_soon(daemon.serve_forever)
        await _wait_socket(sock)
        resp = await anyio.to_thread.run_sync(
            _send,
            sock,
            {
                "action": "start_run",
                "request_id": "rq1",
                "prompt": "hi",
                "repo_path": str(tmp_git_repo),
            },
        )
        assert resp["ok"] is True, resp
        ws = tmp_path / ".runback" / "runs" / str(resp["run_id"]) / "ws"
        assert (ws / "README.md").exists()
        assert int(resp["pid"]) > 0
        await daemon.stop()
        tg.cancel_scope.cancel()


@pytest.mark.anyio("asyncio")
async def test_stop_request_terminates_daemon(tmp_path: Path) -> None:
    sock = _short_socket()
    daemon = RunnerDaemon(socket_path=sock)
    async with anyio.create_task_group() as tg:
        tg.start_soon(daemon.serve_forever)
        await _wait_socket(sock)
        resp = await anyio.to_thread.run_sync(
            _send,
            sock,
            {"action": "stop", "request_id": "rq_stop"},
        )
        assert resp["ok"] is True
        tg.cancel_scope.cancel()
def _short_socket() -> Path:
    return Path(f"/tmp/runback-daemon-{uuid.uuid4().hex}.sock")
