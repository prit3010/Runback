"""POST /api/runs/{run_id}/nodes/{node_id}/policy."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from runback_server.db import engine
from runback_server.ingest.ids import branch_id, node_id, run_id
from runback_server.main import app
from runback_server.models import Node, Run
from sqlmodel import Session


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _mk_run_node(session: Session) -> tuple[Run, Node]:
    b = branch_id()
    run = Run(
        id=run_id(),
        run_kind="ad_hoc",
        status="running",
        original_prompt="(test)",
        repo_path="/tmp",
        workspace_path="/tmp",
        root_branch_id=b,
        current_branch_id=b,
        started_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )
    node = Node(
        id=node_id(),
        run_id=run.id,
        branch_id=b,
        event_type="PreToolUse",
        type="tool",
        label="Bash: do_thing",
        tool_name="Bash",
        status="running",
        recovery_policy="unknown",
        classification_reason="(initial)",
        started_at=datetime.now(UTC),
    )
    session.add(run)
    session.flush()
    session.add(node)
    session.commit()
    return run, node


def test_override_endpoint_updates_node(client):
    with Session(engine) as session:
        run, node = _mk_run_node(session)
        rid = run.id
        nid = node.id

    response = client.post(
        f"/api/runs/{rid}/nodes/{nid}/policy",
        json={"recovery_policy": "rerun", "reason": "I confirmed it's safe"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["recovery_policy"] == "rerun"
    assert body["classification_reason"].startswith("[OVERRIDE]")

    with Session(engine) as session:
        saved = session.get(Node, nid)
        assert saved.recovery_policy == "rerun"
        assert saved.classification_reason.startswith("[OVERRIDE]")


def test_override_endpoint_rejects_invalid_policy(client):
    with Session(engine) as session:
        run, node = _mk_run_node(session)
        rid = run.id
        nid = node.id
    response = client.post(
        f"/api/runs/{rid}/nodes/{nid}/policy",
        json={"recovery_policy": "not_real", "reason": "x"},
    )
    assert response.status_code == 400
    assert "recovery_policy" in response.text.lower()


def test_override_endpoint_rejects_missing_reason(client):
    with Session(engine) as session:
        run, node = _mk_run_node(session)
        rid = run.id
        nid = node.id
    response = client.post(
        f"/api/runs/{rid}/nodes/{nid}/policy",
        json={"recovery_policy": "rerun"},
    )
    assert response.status_code in (400, 422)


def test_override_endpoint_rejects_empty_reason(client):
    with Session(engine) as session:
        run, node = _mk_run_node(session)
        rid = run.id
        nid = node.id
    response = client.post(
        f"/api/runs/{rid}/nodes/{nid}/policy",
        json={"recovery_policy": "rerun", "reason": ""},
    )
    assert response.status_code in (400, 422)
