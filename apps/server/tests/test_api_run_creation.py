"""Backend tests for POST /api/runs and POST /api/runs/{id}/checkpoints."""
from __future__ import annotations

from fastapi.testclient import TestClient
from runback_server.main import app


def test_create_run_201() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/runs",
        json={
            "id": "run_a",
            "run_kind": "ad_hoc",
            "status": "queued",
            "original_prompt": "hi",
            "repo_path": "/tmp/x",
            "root_branch_id": "b1",
            "current_branch_id": "b1",
        },
    )
    assert response.status_code == 201
    assert response.json()["id"] == "run_a"


def test_create_run_409_on_duplicate() -> None:
    client = TestClient(app)
    body = {
        "id": "run_b",
        "run_kind": "ad_hoc",
        "status": "queued",
        "original_prompt": "hi",
        "repo_path": "/tmp/x",
        "root_branch_id": "b",
        "current_branch_id": "b",
    }
    assert client.post("/api/runs", json=body).status_code == 201
    assert client.post("/api/runs", json=body).status_code == 409


def test_create_run_400_on_missing_fields() -> None:
    client = TestClient(app)
    assert client.post("/api/runs", json={"id": "run_c"}).status_code == 400


def test_create_checkpoint_201() -> None:
    client = TestClient(app)
    client.post(
        "/api/runs",
        json={
            "id": "run_cp",
            "run_kind": "ad_hoc",
            "status": "running",
            "original_prompt": "x",
            "repo_path": "/tmp",
            "root_branch_id": "b",
            "current_branch_id": "b",
        },
    )
    response = client.post(
        "/api/runs/run_cp/checkpoints",
        json={
            "label": "start",
            "backend": "hidden_ref",
            "git_ref": "refs/runback/run_cp/0",
            "git_commit_hash": "abc1234",
            "workspace_path": "/tmp/ws",
            "branch_id": "b",
        },
    )
    assert response.status_code == 201
    assert response.json()["git_ref"] == "refs/runback/run_cp/0"


def test_create_checkpoint_404_unknown_run() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/runs/missing/checkpoints",
        json={
            "label": "x",
            "backend": "hidden_ref",
            "git_ref": "refs/runback/missing/0",
            "git_commit_hash": "abc",
            "workspace_path": "/x",
            "branch_id": "b",
        },
    )
    assert response.status_code == 404
