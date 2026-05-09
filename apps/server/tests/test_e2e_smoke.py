"""End-to-end smoke test for a real Claude Code session."""
from __future__ import annotations

import json
import os
import socket
import subprocess
import time
from pathlib import Path
from threading import Thread

import httpx
import pytest
import uvicorn
from runback_server.db import create_all, engine
from runback_server.main import app
from runback_server.models import Node, Run
from sqlmodel import Session, select

pytestmark = pytest.mark.slow


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_ready(url: str, timeout: float = 5.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            httpx.get(url, timeout=0.5)
            return
        except Exception:
            time.sleep(0.1)
    raise RuntimeError(f"server not ready at {url}")


@pytest.fixture
def running_server(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNBACK_DB_PATH", str(tmp_path / "runback.db"))
    monkeypatch.setenv("RUNBACK_RUNTIME_ROOT", str(tmp_path))
    create_all()
    port = _free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = Thread(target=server.run, daemon=True)
    thread.start()
    _wait_ready(f"http://127.0.0.1:{port}/openapi.json")
    yield port
    server.should_exit = True
    thread.join(timeout=2)


def _build_sandbox(tmp_path: Path, backend_port: int) -> Path:
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    (sandbox / "greeting.txt").write_text("hello world")
    subprocess.run(["git", "init", "-q"], cwd=sandbox, check=True)
    subprocess.run(["git", "config", "user.email", "x@x"], cwd=sandbox, check=True)
    subprocess.run(["git", "config", "user.name", "x"], cwd=sandbox, check=True)
    subprocess.run(["git", "add", "."], cwd=sandbox, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=sandbox, check=True)

    bin_dir = sandbox / ".runback" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    forwarder = bin_dir / "forward-hook.sh"
    forwarder.write_text(
        f"""#!/bin/sh
exec curl -fsS -m 5 -X POST http://127.0.0.1:{backend_port}/api/hooks/claude \\
  -H 'content-type: application/json' \\
  -H "x-runback-run-id: ${{RUNBACK_RUN_ID:-unknown}}" \\
  --data-binary @-
"""
    )
    forwarder.chmod(0o755)

    claude_dir = sandbox / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    hook = [{"matcher": "*", "hooks": [{"type": "command", "command": "$RUNBACK_HOOK_FORWARD"}]}]
    (claude_dir / "settings.local.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "UserPromptSubmit": hook,
                    "PreToolUse": hook,
                    "PostToolUse": hook,
                    "Stop": hook,
                }
            },
            indent=2,
        )
    )
    return sandbox


def test_real_claude_run_produces_dag_rows(running_server, tmp_path):
    if not subprocess.run(["which", "claude"], capture_output=True).stdout.strip():
        pytest.skip("claude CLI not on PATH")

    run_id = "run_e2e_1"
    sandbox = _build_sandbox(tmp_path, running_server)
    env = {
        **os.environ,
        "RUNBACK_RUN_ID": run_id,
        "RUNBACK_HOOK_FORWARD": str(sandbox / ".runback" / "bin" / "forward-hook.sh"),
        "PATH": f"{sandbox}/.runback/bin:" + os.environ["PATH"],
    }
    proc = subprocess.run(
        [
            "claude",
            "--print",
            "--permission-mode",
            "bypassPermissions",
            "Read greeting.txt and tell me the first word. One Read tool call.",
        ],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    combined_output = f"{proc.stdout}\n{proc.stderr}".lower()
    if proc.returncode != 0 and (
        "out of extra usage" in combined_output
        or ("usage" in combined_output and "resets" in combined_output)
    ):
        pytest.skip("claude CLI is installed but currently out of usage quota")
    assert proc.returncode == 0, f"claude failed: {proc.stderr}"

    with Session(engine) as session:
        run = session.get(Run, run_id)
        nodes = session.exec(select(Node).where(Node.run_id == run_id)).all()
    assert run is not None
    assert any(node.type == "tool" and node.tool_name == "Read" for node in nodes)
    assert run.status in {"running", "success"}
