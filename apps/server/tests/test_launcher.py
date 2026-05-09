"""Replay launcher Unix-socket client tests."""

from __future__ import annotations

import socket
import tempfile
import threading
import time
from pathlib import Path

import pytest
from runback_server.replay.launcher import (
    LauncherError,
    LauncherTimeout,
    ReplayLaunchPayload,
    send_replay,
)

from tests.fixtures.fake_runner import FakeRunner


@pytest.fixture
def fake_runner(tmp_path):
    runner = FakeRunner(socket_dir=tmp_path)
    yield runner
    runner.stop()


def _payload() -> ReplayLaunchPayload:
    return ReplayLaunchPayload(
        run_id="run_1",
        checkpoint_id="cp_0",
        new_branch_id="branch_replay_1",
        resume_prompt="Resume:\n...",
        replay_id="replay_1",
    )


def test_send_replay_succeeds_against_fake_runner(fake_runner):
    fake_runner.start(reply={"ok": True, "pid": 4242})
    ack = send_replay(_payload(), socket_path=fake_runner.path)
    assert ack["ok"] is True
    assert ack["pid"] == 4242
    msg = fake_runner.received[-1]
    assert msg["action"] == "replay"
    assert msg["run_id"] == "run_1"
    assert msg["checkpoint_id"] == "cp_0"
    assert msg["new_branch_id"] == "branch_replay_1"
    assert msg["replay_id"] == "replay_1"
    assert "Resume:" in msg["resume_prompt"]


def test_send_replay_propagates_error_payload(fake_runner):
    fake_runner.start(reply={"ok": False, "error": "worktree missing", "code": "worktree_missing"})
    with pytest.raises(LauncherError) as exc_info:
        send_replay(_payload(), socket_path=fake_runner.path)
    assert "worktree missing" in str(exc_info.value)
    assert exc_info.value.code == "worktree_missing"


def test_send_replay_raises_when_socket_missing(tmp_path):
    missing = Path(tempfile.gettempdir()) / "rb-nope-test.sock"
    if missing.exists():
        missing.unlink()
    with pytest.raises(LauncherError) as exc_info:
        send_replay(_payload(), socket_path=missing, connect_timeout=0.5)
    assert "runner" in str(exc_info.value).lower() or "socket" in str(exc_info.value).lower()


def test_send_replay_times_out_when_runner_hangs(tmp_path):
    sock_path = Path(tempfile.gettempdir()) / "rb-hang-test.sock"
    if sock_path.exists():
        sock_path.unlink()
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(sock_path))
    server.listen(1)
    stop = threading.Event()

    def loop() -> None:
        server.settimeout(0.2)
        while not stop.is_set():
            try:
                conn, _ = server.accept()
            except TimeoutError:
                continue
            with conn:
                conn.recv(4096)
                while not stop.is_set():
                    time.sleep(0.05)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    try:
        with pytest.raises(LauncherTimeout):
            send_replay(
                _payload(), socket_path=sock_path, connect_timeout=0.5, response_timeout=0.5
            )
    finally:
        stop.set()
        server.close()
        if sock_path.exists():
            sock_path.unlink()
        thread.join(timeout=1)


def test_send_replay_serializes_known_keys(fake_runner):
    fake_runner.start(reply={"ok": True, "pid": 1})
    payload = ReplayLaunchPayload(
        run_id="r",
        checkpoint_id="cp",
        new_branch_id="b",
        resume_prompt="x",
        replay_id="rp",
    )
    send_replay(payload, socket_path=fake_runner.path)
    msg = fake_runner.received[-1]
    assert set(msg.keys()) == {
        "action",
        "run_id",
        "checkpoint_id",
        "new_branch_id",
        "resume_prompt",
        "replay_id",
    }
    assert msg["action"] == "replay"


def test_send_replay_handles_unicode_prompt(fake_runner):
    fake_runner.start(reply={"ok": True, "pid": 1})
    payload = ReplayLaunchPayload(
        run_id="r",
        checkpoint_id="cp",
        new_branch_id="b",
        resume_prompt="accents ea c",
        replay_id="rp",
    )
    send_replay(payload, socket_path=fake_runner.path)
    assert "accents" in fake_runner.received[-1]["resume_prompt"]
