"""Real impls of GET /api/runners and POST /api/runners/heartbeat."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from runback_server.db import create_all, engine
from runback_server.main import app
from runback_server.models import Runner


@pytest.fixture(autouse=True)
def fresh_db():
    create_all()
    with Session(engine) as s:
        for row in s.exec(select(Runner)).all():
            s.delete(row)
        s.commit()


@pytest.fixture
def client():
    return TestClient(app)


def test_list_runners_empty(client):
    r = client.get("/api/runners")
    assert r.status_code == 200
    assert r.json() == []


def test_heartbeat_inserts_runner_when_unknown(client):
    body = {
        "runner_id": "runner_local",
        "status": "online",
        "version": "0.0.1",
        "claude_code_available": True,
    }
    r = client.post("/api/runners/heartbeat", json=body)
    assert r.status_code == 200
    with Session(engine) as s:
        rows = s.exec(select(Runner)).all()
    assert len(rows) == 1
    assert rows[0].id == "runner_local"
    assert rows[0].status == "online"
    assert rows[0].last_heartbeat_at is not None
    assert rows[0].claude_code_available is True
    assert rows[0].version == "0.0.1"


def test_heartbeat_updates_existing_runner(client):
    client.post(
        "/api/runners/heartbeat",
        json={
            "runner_id": "runner_a",
            "status": "online",
            "version": "0.0.1",
            "claude_code_available": True,
        },
    )
    with Session(engine) as s:
        first = s.exec(select(Runner)).one()
        first_hb = first.last_heartbeat_at

    r = client.post(
        "/api/runners/heartbeat",
        json={
            "runner_id": "runner_a",
            "status": "busy",
            "current_run_id": "run_42",
            "version": "0.0.2",
            "claude_code_available": False,
        },
    )
    assert r.status_code == 200

    with Session(engine) as s:
        rows = s.exec(select(Runner)).all()
    assert len(rows) == 1
    upd = rows[0]
    assert upd.status == "busy"
    assert upd.current_run_id == "run_42"
    assert upd.version == "0.0.2"
    assert upd.claude_code_available is False
    assert upd.last_heartbeat_at is not None
    assert upd.last_heartbeat_at >= first_hb


def test_list_runners_returns_all_with_required_fields(client):
    client.post(
        "/api/runners/heartbeat",
        json={
            "runner_id": "r_a",
            "status": "online",
            "version": "0.0.1",
            "claude_code_available": True,
        },
    )
    client.post(
        "/api/runners/heartbeat",
        json={
            "runner_id": "r_b",
            "status": "offline",
            "version": "0.0.1",
            "claude_code_available": True,
        },
    )
    r = client.get("/api/runners")
    assert r.status_code == 200
    rows = r.json()
    assert {row["id"] for row in rows} == {"r_a", "r_b"}
    for row in rows:
        for k in ("id", "name", "status", "claude_code_available", "version", "created_at"):
            assert k in row


def test_heartbeat_rejects_missing_required_fields(client):
    r = client.post("/api/runners/heartbeat", json={"runner_id": "x"})
    assert r.status_code in (400, 422)


def test_list_runners_orders_by_last_heartbeat_desc(client):
    client.post(
        "/api/runners/heartbeat",
        json={
            "runner_id": "old",
            "status": "online",
            "version": "0.0.1",
            "claude_code_available": True,
        },
    )
    client.post(
        "/api/runners/heartbeat",
        json={
            "runner_id": "new",
            "status": "online",
            "version": "0.0.1",
            "claude_code_available": True,
        },
    )
    r = client.get("/api/runners")
    rows = r.json()
    assert rows[0]["id"] == "new"
    assert rows[1]["id"] == "old"
