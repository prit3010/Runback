"""Real impls of GET /api/runs and GET /api/runs/{runId}."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from runback_server.db import create_all, engine
from runback_server.main import app
from runback_server.models import Run


@pytest.fixture(autouse=True)
def fresh_db():
    create_all()
    with Session(engine) as s:
        for row in s.exec(select(Run)).all():
            s.delete(row)
        s.commit()


@pytest.fixture
def client():
    return TestClient(app)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _seed_run(rid: str, status: str = "running", offset_minutes: int = 0) -> None:
    with Session(engine) as s:
        s.add(
            Run(
                id=rid,
                run_kind="ad_hoc",
                status=status,
                original_prompt=f"prompt {rid}",
                repo_path="/tmp/x",
                root_branch_id=f"branch_{rid}",
                current_branch_id=f"branch_{rid}",
                started_at=_now() - timedelta(minutes=offset_minutes),
                created_at=_now() - timedelta(minutes=offset_minutes),
            )
        )
        s.commit()


def test_list_runs_empty(client):
    r = client.get("/api/runs")
    assert r.status_code == 200
    assert r.json() == []


def test_list_runs_returns_all_ordered_newest_first(client):
    _seed_run("run_a", offset_minutes=10)
    _seed_run("run_b", offset_minutes=5)
    _seed_run("run_c", offset_minutes=0)
    r = client.get("/api/runs")
    assert r.status_code == 200
    rows = r.json()
    assert [row["id"] for row in rows] == ["run_c", "run_b", "run_a"]
    for row in rows:
        for k in (
            "id",
            "run_kind",
            "status",
            "original_prompt",
            "repo_path",
            "root_branch_id",
            "current_branch_id",
            "created_at",
        ):
            assert k in row


def test_list_runs_filters_by_status(client):
    _seed_run("run_a", status="running", offset_minutes=2)
    _seed_run("run_b", status="success", offset_minutes=1)
    _seed_run("run_c", status="failed", offset_minutes=0)
    r = client.get("/api/runs?status=success")
    assert r.status_code == 200
    rows = r.json()
    assert {row["id"] for row in rows} == {"run_b"}


def test_get_run_returns_404_when_missing(client):
    r = client.get("/api/runs/missing")
    assert r.status_code == 404


def test_get_run_returns_full_row(client):
    _seed_run("run_x", status="running")
    r = client.get("/api/runs/run_x")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == "run_x"
    assert body["status"] == "running"
    assert body["original_prompt"] == "prompt run_x"
