"""Smoke tests for the fake-runner fixture."""

from __future__ import annotations

import json
import socket


def _round_trip(fake_runner, payload: bytes) -> dict:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(2.0)
    sock.connect(str(fake_runner.path))
    sock.sendall(payload)
    buf = bytearray()
    while not buf.endswith(b"\n"):
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf.extend(chunk)
    sock.close()
    return json.loads(buf.decode("utf-8").rstrip("\n"))


def test_fake_runner_round_trip(fake_runner):
    fake_runner.start(reply={"ok": True, "pid": 7})
    ack = _round_trip(fake_runner, b'{"action":"replay","run_id":"r1"}\n')
    assert ack == {"ok": True, "pid": 7}
    assert fake_runner.received[-1]["action"] == "replay"
    assert fake_runner.received[-1]["run_id"] == "r1"


def test_fake_runner_can_set_reply_after_start(fake_runner):
    fake_runner.start()
    fake_runner.set_reply({"ok": False, "error": "oops", "code": "internal_error"})
    ack = _round_trip(fake_runner, b'{"action":"replay"}\n')
    assert ack["ok"] is False
    assert ack["error"] == "oops"


def test_fake_runner_records_multiple_messages(fake_runner):
    fake_runner.start(reply={"ok": True, "pid": 1})
    for index in range(3):
        _round_trip(fake_runner, (f'{{"action":"replay","i":{index}}}\n').encode())
    assert len(fake_runner.received) == 3
    assert [message["i"] for message in fake_runner.received] == [0, 1, 2]
