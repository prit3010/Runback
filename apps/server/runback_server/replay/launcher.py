"""Unix-socket client for the runner daemon."""

from __future__ import annotations

import json
import socket
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from runback_server.config import get_settings

_DEFAULT_CONNECT_TIMEOUT = 2.0
_DEFAULT_RESPONSE_TIMEOUT = 5.0


class LauncherError(Exception):
    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code


class LauncherTimeoutError(LauncherError):
    """Raised when the runner does not respond in time."""


LauncherTimeout = LauncherTimeoutError


@dataclass
class ReplayLaunchPayload:
    run_id: str
    checkpoint_id: str
    new_branch_id: str
    resume_prompt: str
    replay_id: str

    def to_wire(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["action"] = "replay"
        return payload


def _resolve_socket_path(socket_path: Path | str | None) -> Path:
    if socket_path is not None:
        return Path(socket_path)
    return get_settings().runner_socket_path


def send_replay(
    payload: ReplayLaunchPayload,
    *,
    socket_path: Path | str | None = None,
    connect_timeout: float = _DEFAULT_CONNECT_TIMEOUT,
    response_timeout: float = _DEFAULT_RESPONSE_TIMEOUT,
) -> dict[str, Any]:
    path = _resolve_socket_path(socket_path)
    body = (json.dumps(payload.to_wire(), ensure_ascii=False) + "\n").encode("utf-8")
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(connect_timeout)
    try:
        try:
            sock.connect(str(path))
        except FileNotFoundError as exc:
            raise LauncherError(f"runner socket not found at {path}") from exc
        except ConnectionRefusedError as exc:
            raise LauncherError(f"runner refused connection at {path}") from exc
        except TimeoutError as exc:
            raise LauncherTimeoutError(f"connect timeout to runner at {path}") from exc
        except OSError as exc:
            raise LauncherError(f"runner socket error at {path}: {exc}") from exc

        try:
            sock.sendall(body)
        except OSError as exc:
            raise LauncherError(f"failed to send replay request: {exc}") from exc

        sock.settimeout(response_timeout)
        buf = bytearray()
        try:
            while not buf.endswith(b"\n"):
                chunk = sock.recv(4096)
                if not chunk:
                    break
                buf.extend(chunk)
        except TimeoutError as exc:
            raise LauncherTimeoutError(
                f"timeout waiting for runner response after {response_timeout}s"
            ) from exc
        except OSError as exc:
            raise LauncherError(f"socket read error: {exc}") from exc
    finally:
        try:
            sock.close()
        except OSError:
            pass

    if not buf:
        raise LauncherError("runner closed connection without reply")
    try:
        ack = json.loads(buf.decode("utf-8").rstrip("\n"))
    except json.JSONDecodeError as exc:
        raise LauncherError(f"runner returned malformed JSON: {exc}") from exc
    if not isinstance(ack, dict):
        raise LauncherError(f"runner reply not a JSON object: {ack!r}")
    if not ack.get("ok"):
        raise LauncherError(
            ack.get("error") or "runner reported failure",
            code=ack.get("code"),
        )
    return ack
