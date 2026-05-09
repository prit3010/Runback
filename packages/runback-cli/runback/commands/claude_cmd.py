"""`runback claude` command."""
from __future__ import annotations

import json
import socket
import sys
from pathlib import Path

import click
import ulid

from runback.config import get_settings


@click.command("claude")
@click.argument("prompt", required=True)
def claude(prompt: str) -> None:
    """Launch a one-shot Claude Code run captured by Runback."""
    settings = get_settings()
    sock_path = settings.runner_socket
    if not sock_path.exists():
        click.secho(
            f"error: runner socket not found at {sock_path}. "
            "Start `runback runner` or `runback dev`.",
            fg="red",
            err=True,
        )
        sys.exit(2)
    body = {
        "action": "start_run",
        "request_id": f"req_{ulid.new().str.lower()}",
        "prompt": prompt,
        "repo_path": str(Path.cwd().resolve()),
    }
    try:
        response = _send(sock_path, body)
    except OSError as exc:
        click.secho(f"error: cannot reach runner: {exc}", fg="red", err=True)
        sys.exit(2)
    if not response.get("ok"):
        click.secho(f"runner error: {response.get('error')}", fg="red", err=True)
        sys.exit(1)
    click.secho(f"started run {response.get('run_id')} (pid {response.get('pid')})", fg="green")


def _send(sock_path: Path, body: dict[str, object]) -> dict[str, object]:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(10)
    try:
        sock.connect(str(sock_path))
        sock.sendall((json.dumps(body) + "\n").encode())
        data = b""
        while not data.endswith(b"\n"):
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
    finally:
        sock.close()
    return json.loads(data.decode().strip())
