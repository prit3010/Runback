"""Shared test fixtures."""
from __future__ import annotations

import os
import socket
import time
from collections.abc import Iterator
from pathlib import Path
from threading import Thread

import httpx
import pytest
import uvicorn
from tests.fixtures.fake_runner import FakeRunner

os.environ.setdefault("RUNBACK_DB_PATH", "/tmp/runback-server-tests.db")
os.environ.setdefault("RUNBACK_RUNTIME_ROOT", "/tmp/runback-server-tests")

from runback_server.db import create_all, engine

# Import ingest-side SQLModel tables so drop/create covers the full server schema.
from runback_server.ingest.archive import EventDedup  # noqa: F401
from runback_server.ingest.groups import TodoState  # noqa: F401
from runback_server.main import app
from sqlmodel import SQLModel


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def fake_runner(tmp_path):
    runner = FakeRunner(socket_dir=tmp_path)
    yield runner
    runner.stop()


@pytest.fixture(autouse=True)
def isolated_runback_dir(monkeypatch, tmp_path) -> Iterator[Path]:
    runback_dir = tmp_path / ".runback"
    runback_dir.mkdir()
    monkeypatch.setenv("RUNBACK_DB_PATH", str(runback_dir / "runback.db"))
    monkeypatch.setenv("RUNBACK_RUNTIME_ROOT", str(runback_dir))
    SQLModel.metadata.drop_all(engine)
    create_all()
    yield runback_dir
    SQLModel.metadata.drop_all(engine)


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_ready(url: str, timeout: float = 5.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            httpx.get(url, timeout=0.5)
            return
        except Exception:
            time.sleep(0.05)
    raise RuntimeError(f"server not ready at {url}")


@pytest.fixture
def live_server_url() -> Iterator[str]:
    """Run the ASGI app over real HTTP for streaming response tests.

    httpx.ASGITransport buffers the whole response before returning, so it cannot
    exercise unbounded SSE streams. A localhost Uvicorn server gives tests real
    streaming semantics while staying in-process.
    """
    port = _free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = Thread(target=server.run, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"
    _wait_ready(f"{base_url}/openapi.json")
    yield base_url
    server.should_exit = True
    thread.join(timeout=2)
