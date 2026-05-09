"""A fake Unix-socket server that mimics Plan 3's runner."""

from __future__ import annotations

import json
import os
import socket
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class FakeRunner:
    socket_dir: Path
    path: Path = field(init=False)
    received: list[dict[str, Any]] = field(default_factory=list)
    _reply: dict[str, Any] = field(default_factory=lambda: {"ok": True, "pid": 12345})
    _thread: threading.Thread | None = None
    _stop: threading.Event = field(default_factory=threading.Event)
    _server: socket.socket | None = None

    def __post_init__(self) -> None:
        candidate = self.socket_dir / f"runback-runner-{os.getpid()}.sock"
        if len(str(candidate)) >= 100:
            candidate = Path(tempfile.gettempdir()) / f"rb-{os.getpid()}-{id(self)}.sock"
        self.path = candidate

    def start(self, *, reply: dict[str, Any] | None = None) -> None:
        if reply is not None:
            self._reply = reply
        self._stop.clear()
        if self.path.exists():
            self.path.unlink()
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(str(self.path))
        server.listen(1)
        server.settimeout(0.2)
        self._server = server
        self._thread = threading.Thread(target=self._serve_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._server is not None:
            try:
                self._server.close()
            except OSError:
                pass
        if self._thread is not None:
            self._thread.join(timeout=1)
        if self.path.exists():
            try:
                self.path.unlink()
            except OSError:
                pass

    def set_reply(self, reply: dict[str, Any]) -> None:
        self._reply = reply

    def _serve_loop(self) -> None:
        assert self._server is not None
        while not self._stop.is_set():
            try:
                conn, _ = self._server.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            with conn:
                try:
                    conn.settimeout(2.0)
                    buf = bytearray()
                    while not buf.endswith(b"\n"):
                        chunk = conn.recv(4096)
                        if not chunk:
                            break
                        buf.extend(chunk)
                    if buf:
                        try:
                            self.received.append(json.loads(buf.decode("utf-8").rstrip("\n")))
                        except json.JSONDecodeError:
                            self.received.append({"_raw": buf.decode("utf-8", "replace")})
                    conn.sendall((json.dumps(self._reply) + "\n").encode("utf-8"))
                except (TimeoutError, OSError):
                    pass
