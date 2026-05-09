"""`runback claude` tests."""
from __future__ import annotations

import json
import socket
import threading
import uuid
from pathlib import Path

from click.testing import CliRunner
from runback.__main__ import cli


def _fake_runner_socket(sock_path: Path, response: dict[str, object]) -> threading.Thread:
    sock_path.parent.mkdir(parents=True, exist_ok=True)
    if sock_path.exists():
        sock_path.unlink()
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(sock_path))
    server.listen(1)

    def serve() -> None:
        conn, _ = server.accept()
        data = b""
        while not data.endswith(b"\n"):
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
        conn.sendall((json.dumps(response) + "\n").encode())
        conn.close()
        server.close()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    return thread


def test_claude_cmd_sends_start_run_to_runner_socket(tmp_path: Path, monkeypatch) -> None:
    sock = _short_socket()
    monkeypatch.setenv("RUNBACK_RUNNER_SOCKET", str(sock))
    monkeypatch.chdir(tmp_path)
    _fake_runner_socket(sock, {"ok": True, "request_id": "x", "run_id": "run_t", "pid": 9999})
    result = CliRunner().invoke(cli, ["claude", "fix the bug"])
    assert result.exit_code == 0, result.output
    assert "run_t" in result.output


def test_claude_cmd_errors_when_runner_not_running(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("RUNBACK_RUNNER_SOCKET", str(_short_socket()))
    result = CliRunner().invoke(cli, ["claude", "x"])
    assert result.exit_code != 0
    assert "runner" in result.output.lower()


def test_claude_cmd_propagates_runner_error(tmp_path: Path, monkeypatch) -> None:
    sock = _short_socket()
    monkeypatch.setenv("RUNBACK_RUNNER_SOCKET", str(sock))
    _fake_runner_socket(
        sock,
        {"ok": False, "request_id": "x", "error": "no claude", "code": "runtime"},
    )
    result = CliRunner().invoke(cli, ["claude", "x"])
    assert result.exit_code != 0
    assert "no claude" in result.output.lower()
def _short_socket() -> Path:
    return Path(f"/tmp/runback-cli-{uuid.uuid4().hex}.sock")
