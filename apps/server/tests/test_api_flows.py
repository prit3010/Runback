"""Real impls for /api/flows CRUD + /api/flows/{flowId}/run."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from runback_server.db import create_all, engine
from runback_server.main import app
from runback_server.models import Flow, FlowVersion, Run


@pytest.fixture(autouse=True)
def fresh_db():
    create_all()
    with Session(engine) as s:
        for row in s.exec(select(Run)).all():
            s.delete(row)
        for row in s.exec(select(FlowVersion)).all():
            s.delete(row)
        for row in s.exec(select(Flow)).all():
            s.delete(row)
        s.commit()


@pytest.fixture
def client():
    return TestClient(app)


def test_list_flows_empty(client):
    r = client.get("/api/flows")
    assert r.status_code == 200
    assert r.json() == []


def test_create_flow_writes_flow_and_first_version(client):
    body = {
        "name": "backlog fixer",
        "description": "Auto-fix tickets in BACKLOG.md",
        "repo_path": "/tmp/demos/backlog",
        "prompt": "Process every open auto-fix ticket in BACKLOG.md.",
        "replay_mode": "semi_automatic",
        "side_effect_policy": "label_only",
    }
    r = client.post("/api/flows", json=body)
    assert r.status_code == 201
    flow = r.json()
    assert flow["name"] == "backlog fixer"
    assert flow["repo_path"] == "/tmp/demos/backlog"
    assert flow["agent"] == "claude_code"
    assert flow["enabled"] is True
    assert flow["active_version_id"]
    assert flow["id"]

    with Session(engine) as s:
        flows = s.exec(select(Flow)).all()
        versions = s.exec(select(FlowVersion)).all()
    assert len(flows) == 1
    assert len(versions) == 1
    assert versions[0].flow_id == flow["id"]
    assert versions[0].id == flow["active_version_id"]
    assert versions[0].prompt == body["prompt"]
    assert versions[0].replay_mode == "semi_automatic"
    assert versions[0].side_effect_policy == "label_only"
    assert versions[0].version_number == 1


def test_create_flow_uses_default_replay_mode_and_policy_when_omitted(client):
    body = {
        "name": "minimal",
        "repo_path": "/tmp/x",
        "prompt": "do thing",
    }
    r = client.post("/api/flows", json=body)
    assert r.status_code == 201
    with Session(engine) as s:
        v = s.exec(select(FlowVersion)).one()
    assert v.replay_mode == "manual"
    assert v.side_effect_policy == "label_only"


def test_create_flow_rejects_missing_required_fields(client):
    r = client.post("/api/flows", json={"name": "no_prompt", "repo_path": "/tmp/x"})
    assert r.status_code in (400, 422)


def test_list_flows_returns_flows_newest_first(client):
    for name in ("a", "b", "c"):
        client.post(
            "/api/flows",
            json={
                "name": name,
                "repo_path": "/tmp/x",
                "prompt": "p",
            },
        )
    r = client.get("/api/flows")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 3
    assert rows[0]["name"] == "c"
    assert rows[2]["name"] == "a"


def test_get_flow_returns_flow_or_404(client):
    cr = client.post(
        "/api/flows",
        json={
            "name": "x",
            "repo_path": "/tmp/x",
            "prompt": "p",
        },
    ).json()
    fid = cr["id"]

    r = client.get(f"/api/flows/{fid}")
    assert r.status_code == 200
    assert r.json()["id"] == fid

    r = client.get("/api/flows/no_such_flow")
    assert r.status_code == 404


def test_run_flow_creates_queued_run_referencing_active_version(client):
    cr = client.post(
        "/api/flows",
        json={
            "name": "x",
            "repo_path": "/tmp/repo",
            "prompt": "go",
        },
    ).json()
    fid = cr["id"]
    fvid = cr["active_version_id"]

    r = client.post(f"/api/flows/{fid}/run")
    assert r.status_code == 202
    body = r.json()
    assert body["flow_id"] == fid
    assert body["flow_version_id"] == fvid
    assert body["status"] == "queued"
    assert body["run_kind"] == "registered_flow"
    assert body["original_prompt"] == "go"
    assert body["repo_path"] == "/tmp/repo"
    assert body["root_branch_id"] == body["current_branch_id"]
    assert body["id"].startswith("run_")

    with Session(engine) as s:
        runs = s.exec(select(Run)).all()
    assert len(runs) == 1
    assert runs[0].id == body["id"]


def test_run_flow_404_when_flow_missing(client):
    r = client.post("/api/flows/no_flow/run")
    assert r.status_code == 404
