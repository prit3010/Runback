"""Shared test fixtures."""
from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

os.environ.setdefault("RUNBACK_DB_PATH", "/tmp/runback-server-tests.db")
os.environ.setdefault("RUNBACK_RUNTIME_ROOT", "/tmp/runback-server-tests")

from runback_server.db import create_all, engine

# Import ingest-side SQLModel tables so drop/create covers the full server schema.
from runback_server.ingest.archive import EventDedup  # noqa: F401
from runback_server.ingest.groups import TodoState  # noqa: F401
from sqlmodel import SQLModel


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
