"""Unix-socket IPC server tests."""
from __future__ import annotations

import json
import socket
import uuid
from pathlib import Path
from typing import Any

import anyio
import pytest
from runback.runner.ipc import IpcRequest, IpcServer


class Recorder:
    def __init__(self) -> None:
        self.received: list[IpcRequest] = []

    async def handle(self, req: IpcRequest) -> dict[str, Any]:
        self.received.append(req)
        if req.action == "start_run":
            return {"ok": True, "request_id": req.request_id, "run_id": "run_test", "pid": 1}
        if req.action == "replay":
            return {"ok": True, "request_id": req.request_id, "pid": 2}
        return {"ok": True, "request_id": req.request_id}


def _send_request(sock_path: Path, body: dict[str, Any] | bytes) -> dict[str, Any]:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(str(sock_path))
    payload = body if isinstance(body, bytes) else json.dumps(body).encode()
    sock.sendall(payload + b"\n")
    data = b""
    while not data.endswith(b"\n"):
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk
    sock.close()
    return json.loads(data.decode().strip())


async def _wait_socket(sock: Path) -> None:
    for _ in range(50):
        if sock.exists():
            return
        await anyio.sleep(0.05)
    raise AssertionError("socket was not created")


@pytest.mark.anyio("asyncio")
async def test_start_run_request_response(tmp_path: Path) -> None:
    sock = _short_socket()
    handler = Recorder()
    server = IpcServer(socket_path=sock, handler=handler.handle)
    async with anyio.create_task_group() as tg:
        tg.start_soon(server.serve_forever)
        await _wait_socket(sock)
        resp = await anyio.to_thread.run_sync(
            _send_request,
            sock,
            {"action": "start_run", "request_id": "r1", "prompt": "hi", "repo_path": "/x"},
        )
        assert resp["ok"] is True
        assert handler.received[0].body["prompt"] == "hi"
        await server.stop()
        tg.cancel_scope.cancel()


@pytest.mark.anyio("asyncio")
async def test_replay_request_response(tmp_path: Path) -> None:
    sock = _short_socket()
    handler = Recorder()
    server = IpcServer(socket_path=sock, handler=handler.handle)
    async with anyio.create_task_group() as tg:
        tg.start_soon(server.serve_forever)
        await _wait_socket(sock)
        resp = await anyio.to_thread.run_sync(
            _send_request,
            sock,
            {"action": "replay", "replay_id": "r2", "run_id": "run_a"},
        )
        assert resp["ok"] is True
        assert handler.received[0].request_id == "r2"
        await server.stop()
        tg.cancel_scope.cancel()


@pytest.mark.anyio("asyncio")
async def test_malformed_json_returns_bad_request(tmp_path: Path) -> None:
    sock = _short_socket()
    server = IpcServer(socket_path=sock, handler=Recorder().handle)
    async with anyio.create_task_group() as tg:
        tg.start_soon(server.serve_forever)
        await _wait_socket(sock)
        resp = await anyio.to_thread.run_sync(_send_request, sock, b"not json")
        assert resp["ok"] is False
        assert resp["code"] == "bad_request"
        await server.stop()
        tg.cancel_scope.cancel()
def _short_socket() -> Path:
    return Path(f"/tmp/runback-test-{uuid.uuid4().hex}.sock")

