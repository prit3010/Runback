"""HTTP-level tests for replay endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from runback_server.db import create_all, engine
from runback_server.main import app
from runback_server.models import (
    Artifact,
    Checkpoint,
    Edge,
    Node,
    NodeArtifactEdge,
    ReplayAttempt,
    Run,
    RunGroup,
    SideEffectLog,
)
from sqlmodel import Session, select

from tests.fixtures.replay_dags import DagBuilder


@pytest.fixture(autouse=True)
def fresh_db():
    create_all()
    with Session(engine) as session:
        for model in (
            NodeArtifactEdge,
            Artifact,
            ReplayAttempt,
            SideEffectLog,
            Edge,
            Node,
            Checkpoint,
            RunGroup,
            Run,
        ):
            for row in session.exec(select(model)).all():
                session.delete(row)
        session.commit()


@pytest.fixture
def client():
    return TestClient(app)


def _seed_failed_run(session: Session, *, run_id: str = "run_h") -> str:
    builder = DagBuilder(session, run_id=run_id)
    builder.run(prompt="ship the thing")
    builder.checkpoint("cp_0", label="run start")
    builder.checkpoint("cp_pre_edit", label="checkpoint_pre_edit")
    builder.node("n1", label="Read", policy="reuse_cached")
    builder.node(
        "n2", label="Edit", policy="restore_checkpoint", checkpoint_before_id="cp_pre_edit"
    )
    builder.node(
        "n3",
        label="Bash test",
        policy="rerun",
        status="failed",
        tool_name="Bash",
        error="exit 1",
        output_preview="FAIL src/x",
    )
    builder.chain("n1", "n2", "n3")
    builder.commit()
    return "n3"


def test_get_recommendation_returns_full_schema(client):
    with Session(engine) as session:
        failed = _seed_failed_run(session)
    response = client.get("/api/runs/run_h/replay/recommendation", params={"nodeId": failed})
    assert response.status_code == 200
    body = response.json()
    for key in (
        "source_node_id",
        "recommended_checkpoint_id",
        "confidence",
        "reason",
        "reuse_node_ids",
        "rerun_node_ids",
        "approval_node_ids",
        "unsafe_node_ids",
        "generated_resume_prompt",
    ):
        assert key in body
    assert body["source_node_id"] == failed
    assert body["recommended_checkpoint_id"] == "cp_pre_edit"
    assert "ship the thing" in body["generated_resume_prompt"]


def test_get_recommendation_404s_for_missing_node(client):
    with Session(engine) as session:
        builder = DagBuilder(session, run_id="run_404")
        builder.run()
        builder.commit()
    response = client.get("/api/runs/run_404/replay/recommendation", params={"nodeId": "ghost"})
    assert response.status_code == 404


def test_get_recommendation_404s_for_missing_run(client):
    response = client.get(
        "/api/runs/run_does_not_exist/replay/recommendation", params={"nodeId": "n1"}
    )
    assert response.status_code == 404


def test_get_recommendation_400s_when_no_checkpoint_exists(client):
    with Session(engine) as session:
        builder = DagBuilder(session, run_id="run_no_cp")
        builder.run()
        builder.node("n1", label="Read", status="failed")
        builder.commit()
    response = client.get("/api/runs/run_no_cp/replay/recommendation", params={"nodeId": "n1"})
    assert response.status_code == 400
    assert "checkpoint" in response.json()["detail"].lower()


def _post_replay(client, run_id: str, body: dict):
    return client.post(f"/api/runs/{run_id}/replay", json=body)


def test_post_replay_creates_attempt_and_signals_runner(client, fake_runner, monkeypatch):
    fake_runner.start(reply={"ok": True, "pid": 9001})
    monkeypatch.setattr(
        "runback_server.replay.launcher._resolve_socket_path", lambda _: fake_runner.path
    )
    with Session(engine) as session:
        failed = _seed_failed_run(session, run_id="run_post1")
    response = _post_replay(client, "run_post1", {"node_id": failed})
    assert response.status_code == 202, response.text
    body = response.json()
    assert body["run_id"] == "run_post1"
    assert body["source_node_id"] == failed
    assert body["new_branch_id"] != body["parent_branch_id"]
    assert body["status"] == "running"
    with Session(engine) as session:
        row = session.get(ReplayAttempt, body["id"])
    assert row is not None
    assert row.resume_prompt and "ship the thing" in row.resume_prompt
    msg = fake_runner.received[-1]
    assert msg["action"] == "replay"
    assert msg["run_id"] == "run_post1"
    assert msg["new_branch_id"] == body["new_branch_id"]
    assert msg["replay_id"] == body["id"]


def test_post_replay_uses_edited_resume_prompt_when_provided(client, fake_runner, monkeypatch):
    fake_runner.start(reply={"ok": True, "pid": 1})
    monkeypatch.setattr(
        "runback_server.replay.launcher._resolve_socket_path", lambda _: fake_runner.path
    )
    with Session(engine) as session:
        failed = _seed_failed_run(session, run_id="run_edit")
    edited = "USER EDITED PROMPT - do thing X"
    response = _post_replay(client, "run_edit", {"node_id": failed, "edited_resume_prompt": edited})
    assert response.status_code == 202
    assert response.json()["resume_prompt"] == edited
    assert fake_runner.received[-1]["resume_prompt"] == edited


def test_post_replay_includes_user_context_in_built_prompt(client, fake_runner, monkeypatch):
    fake_runner.start(reply={"ok": True, "pid": 1})
    monkeypatch.setattr(
        "runback_server.replay.launcher._resolve_socket_path", lambda _: fake_runner.path
    )
    with Session(engine) as session:
        failed = _seed_failed_run(session, run_id="run_ctx")
    response = _post_replay(client, "run_ctx", {"node_id": failed, "user_context": "regex bug"})
    assert response.status_code == 202
    assert "regex bug" in fake_runner.received[-1]["resume_prompt"]


def test_post_replay_marks_attempt_failed_when_runner_errors(client, fake_runner, monkeypatch):
    fake_runner.start(reply={"ok": False, "error": "worktree missing", "code": "worktree_missing"})
    monkeypatch.setattr(
        "runback_server.replay.launcher._resolve_socket_path", lambda _: fake_runner.path
    )
    with Session(engine) as session:
        failed = _seed_failed_run(session, run_id="run_err")
    response = _post_replay(client, "run_err", {"node_id": failed})
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "failed"
    with Session(engine) as session:
        row = session.get(ReplayAttempt, body["id"])
    assert row.status == "failed"
    assert row.generated_context and "worktree missing" in row.generated_context


def test_post_replay_marks_attempt_failed_on_runner_unreachable(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        "runback_server.replay.launcher._resolve_socket_path", lambda _: tmp_path / "no-such.sock"
    )
    with Session(engine) as session:
        failed = _seed_failed_run(session, run_id="run_unreach")
    response = _post_replay(client, "run_unreach", {"node_id": failed})
    assert response.status_code == 202
    assert response.json()["status"] == "failed"


def test_post_replay_404s_for_missing_run(client):
    response = _post_replay(client, "run_does_not_exist", {"node_id": "n1"})
    assert response.status_code == 404


def test_post_replay_422s_for_missing_node_id(client):
    response = _post_replay(client, "run_post1", {})
    assert response.status_code in (400, 422)
