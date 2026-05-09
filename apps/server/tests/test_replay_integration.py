"""End-to-end replay integration tests."""

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


def _seed_backlog_run(session: Session) -> tuple[str, str]:
    builder = DagBuilder(session, run_id="run_backlog")
    builder.run(prompt="Process every ticket in BACKLOG.md")
    builder.checkpoint("cp_0", label="run start")
    builder.checkpoint("cp_pre_edit_4", label="checkpoint_pre_edit_4")
    builder.group("g1", label="Ticket #1: handler", status="success")
    builder.node("n_read_backlog", label="Read BACKLOG.md", policy="reuse_cached", group_id="g1")
    builder.node(
        "n_edit_handler",
        label="Edit handler.ts",
        policy="restore_checkpoint",
        group_id="g1",
        checkpoint_before_id="cp_0",
    )
    builder.node(
        "n_test_t1", label="Bash npm test", policy="rerun", group_id="g1", tool_name="Bash"
    )
    builder.node(
        "n_pr_t1", label="gh pr create", policy="requires_approval", group_id="g1", tool_name="Bash"
    )
    builder.side_effect(
        node_id="n_pr_t1",
        kind="gh_pr_create",
        key="gh:pr:owner/repo:fix/issue-1",
        external_ref="https://github.com/owner/repo/pull/101",
    )
    builder.group("g4", label="Ticket #4: email regex", status="failed")
    builder.node(
        "n_edit_auth",
        label="Edit auth.ts",
        policy="restore_checkpoint",
        group_id="g4",
        checkpoint_before_id="cp_pre_edit_4",
    )
    builder.node(
        "n_test_t4",
        label="Bash npm test",
        policy="rerun",
        group_id="g4",
        tool_name="Bash",
        status="failed",
        error="exit 1",
        output_preview="FAIL src/auth/email.test.ts\n  email regex rejects '+'",
    )
    builder.chain(
        "n_read_backlog",
        "n_edit_handler",
        "n_test_t1",
        "n_pr_t1",
        "n_edit_auth",
        "n_test_t4",
    )
    builder.commit()
    return "run_backlog", "n_test_t4"


def test_full_replay_pipeline(client, fake_runner, monkeypatch):
    fake_runner.start(reply={"ok": True, "pid": 31337})
    monkeypatch.setattr(
        "runback_server.replay.launcher._resolve_socket_path", lambda _: fake_runner.path
    )
    with Session(engine) as session:
        run_id, failed = _seed_backlog_run(session)

    response = client.get(f"/api/runs/{run_id}/replay/recommendation", params={"nodeId": failed})
    assert response.status_code == 200, response.text
    recommendation = response.json()
    assert recommendation["recommended_checkpoint_id"] == "cp_pre_edit_4"
    assert "n_pr_t1" in recommendation["reuse_node_ids"]
    assert "n_pr_t1" not in recommendation["approval_node_ids"]
    assert "https://github.com/owner/repo/pull/101" in recommendation["generated_resume_prompt"]
    assert "ALREADY EXECUTED" in recommendation["generated_resume_prompt"]

    response = client.post(
        f"/api/runs/{run_id}/replay",
        json={"node_id": failed, "user_context": "regex must accept '+' characters"},
    )
    assert response.status_code == 202, response.text
    body = response.json()
    assert body["status"] == "running"
    assert body["new_branch_id"] != body["parent_branch_id"]
    assert body["source_checkpoint_id"] == "cp_pre_edit_4"

    with Session(engine) as session:
        row = session.get(ReplayAttempt, body["id"])
    assert row is not None
    assert row.status == "running"
    assert row.user_context == "regex must accept '+' characters"
    assert row.recommendation_json["recommended_checkpoint_id"] == "cp_pre_edit_4"
    assert row.recommendation_json.get("runner_pid") == 31337
    assert "regex must accept '+' characters" in row.resume_prompt
    assert "https://github.com/owner/repo/pull/101" in row.resume_prompt

    assert len(fake_runner.received) == 1
    msg = fake_runner.received[0]
    assert msg["action"] == "replay"
    assert msg["run_id"] == run_id
    assert msg["checkpoint_id"] == "cp_pre_edit_4"
    assert msg["new_branch_id"] == row.new_branch_id
    assert msg["replay_id"] == row.id
    assert msg["resume_prompt"] == row.resume_prompt


def test_full_pipeline_with_runner_unreachable(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        "runback_server.replay.launcher._resolve_socket_path", lambda _: tmp_path / "absent.sock"
    )
    with Session(engine) as session:
        run_id, failed = _seed_backlog_run(session)
    response = client.post(f"/api/runs/{run_id}/replay", json={"node_id": failed})
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "failed"
    with Session(engine) as session:
        row = session.get(ReplayAttempt, body["id"])
    assert row.status == "failed"
    assert row.generated_context is not None


def test_full_pipeline_edited_prompt_overrides_built_one(client, fake_runner, monkeypatch):
    fake_runner.start(reply={"ok": True, "pid": 1})
    monkeypatch.setattr(
        "runback_server.replay.launcher._resolve_socket_path", lambda _: fake_runner.path
    )
    with Session(engine) as session:
        run_id, failed = _seed_backlog_run(session)
    edited = "USER OVERRIDE: just rerun the last test"
    response = client.post(
        f"/api/runs/{run_id}/replay",
        json={"node_id": failed, "edited_resume_prompt": edited},
    )
    assert response.status_code == 202
    assert response.json()["resume_prompt"] == edited
    assert fake_runner.received[-1]["resume_prompt"] == edited
    assert fake_runner.received[-1]["checkpoint_id"] == "cp_pre_edit_4"
