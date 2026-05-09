"""Shared test fixtures."""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_runback_dir(monkeypatch, tmp_path) -> Iterator[Path]:
    runback_dir = tmp_path / ".runback"
    runback_dir.mkdir()
    monkeypatch.setenv("RUNBACK_DB_PATH", str(runback_dir / "runback.db"))
    monkeypatch.setenv("RUNBACK_RUNTIME_ROOT", str(runback_dir))
    yield runback_dir
