"""Policy override missing-row error paths."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from runback_server.db import engine
from runback_server.ingest.ids import branch_id, run_id
from runback_server.main import app
from runback_server.models import Run
from sqlmodel import Session


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_override_missing_run_returns_404(client):
    response = client.post(
        "/api/runs/run_does_not_exist/nodes/node_x/policy",
        json={"recovery_policy": "rerun", "reason": "x"},
    )
    assert response.status_code == 404
    assert "run" in response.text.lower()


def test_override_missing_node_returns_404(client):
    with Session(engine) as session:
        branch = branch_id()
        rid = run_id()
        session.add(
            Run(
                id=rid,
                run_kind="ad_hoc",
                status="running",
                original_prompt="(test)",
                repo_path="/tmp",
                workspace_path="/tmp",
                root_branch_id=branch,
                current_branch_id=branch,
                started_at=datetime.now(UTC),
                created_at=datetime.now(UTC),
            )
        )
        session.commit()

    response = client.post(
        f"/api/runs/{rid}/nodes/node_not_here/policy",
        json={"recovery_policy": "rerun", "reason": "x"},
    )
    assert response.status_code == 404
    assert "node" in response.text.lower()
