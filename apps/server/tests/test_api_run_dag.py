"""GET /api/runs/{runId}/dag returns Run + Nodes + Edges + Checkpoints + Groups + SideEffects."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from runback_server.db import create_all, engine
from runback_server.main import app
from runback_server.models import (
    Checkpoint,
    Edge,
    Node,
    Run,
    RunGroup,
    SideEffectLog,
)


@pytest.fixture(autouse=True)
def fresh_db():
    create_all()
    with Session(engine) as s:
        for row in s.exec(select(SideEffectLog)).all():
            s.delete(row)
        for row in s.exec(select(Checkpoint)).all():
            s.delete(row)
        for row in s.exec(select(Edge)).all():
            s.delete(row)
        for row in s.exec(select(Node)).all():
            s.delete(row)
        for row in s.exec(select(RunGroup)).all():
            s.delete(row)
        for row in s.exec(select(Run)).all():
            s.delete(row)
        s.commit()


@pytest.fixture
def client():
    return TestClient(app)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _seed_full_run() -> str:
    rid = "run_dag_1"
    with Session(engine) as s:
        s.add(
            Run(
                id=rid,
                run_kind="ad_hoc",
                status="running",
                original_prompt="task",
                repo_path="/tmp",
                root_branch_id="b1",
                current_branch_id="b1",
                started_at=_now(),
                created_at=_now(),
            )
        )
        s.flush()
        s.add(
            RunGroup(
                id="g1",
                run_id=rid,
                parent_group_id=None,
                label="Ticket #1: Foo",
                kind="ticket",
                status="running",
                started_at=_now(),
            )
        )
        s.flush()
        s.add(
            Node(
                id="n1",
                run_id=rid,
                branch_id="b1",
                group_id="g1",
                event_type="UserPromptSubmit",
                type="prompt",
                label="Prompt: task",
                status="success",
                recovery_policy="reuse_cached",
                started_at=_now(),
                ended_at=_now(),
            )
        )
        s.add(
            Node(
                id="n2",
                run_id=rid,
                branch_id="b1",
                group_id="g1",
                event_type="PreToolUse",
                type="tool",
                tool_name="Read",
                label="Read foo.py",
                status="success",
                recovery_policy="reuse_cached",
                started_at=_now(),
            )
        )
        s.flush()
        s.add(
            Edge(
                id="e1",
                run_id=rid,
                branch_id="b1",
                source_node_id="n1",
                target_node_id="n2",
                edge_type="sequence",
            )
        )
        s.add(
            Checkpoint(
                id="cp1",
                run_id=rid,
                branch_id="b1",
                node_id="n2",
                label="run start",
                backend="hidden_ref",
                git_ref=f"refs/runback/{rid}/0",
                workspace_path="/tmp/ws",
                created_at=_now(),
            )
        )
        s.add(
            SideEffectLog(
                run_id=rid,
                branch_id="b1",
                node_id="n2",
                kind="gh_pr_create",
                idempotency_key="gh:pr:o/r:fix/x",
                external_ref="https://github.com/o/r/pull/1",
                status="executed",
            )
        )
        s.commit()
    return rid


def test_get_run_dag_returns_all_pieces(client):
    rid = _seed_full_run()
    r = client.get(f"/api/runs/{rid}/dag")
    assert r.status_code == 200
    body = r.json()

    assert body["run"]["id"] == rid
    assert body["run"]["status"] == "running"

    assert len(body["nodes"]) == 2
    by_id = {n["id"]: n for n in body["nodes"]}
    assert by_id["n1"]["type"] == "prompt"
    assert by_id["n2"]["tool_name"] == "Read"
    for n in body["nodes"]:
        for k in ("id", "run_id", "branch_id", "type", "label", "status", "recovery_policy"):
            assert k in n

    assert len(body["edges"]) == 1
    assert body["edges"][0]["source_node_id"] == "n1"
    assert body["edges"][0]["target_node_id"] == "n2"

    assert len(body["checkpoints"]) == 1
    assert body["checkpoints"][0]["git_ref"] == f"refs/runback/{rid}/0"

    assert len(body["groups"]) == 1
    assert body["groups"][0]["label"] == "Ticket #1: Foo"

    assert len(body["side_effects"]) == 1
    assert body["side_effects"][0]["kind"] == "gh_pr_create"


def test_get_run_dag_returns_404_when_run_missing(client):
    r = client.get("/api/runs/no_such_run/dag")
    assert r.status_code == 404


def test_get_run_dag_empty_collections_for_new_run(client):
    rid = "run_empty"
    with Session(engine) as s:
        s.add(
            Run(
                id=rid,
                run_kind="ad_hoc",
                status="running",
                original_prompt="x",
                repo_path="/tmp",
                root_branch_id="b1",
                current_branch_id="b1",
                started_at=_now(),
                created_at=_now(),
            )
        )
        s.commit()
    r = client.get(f"/api/runs/{rid}/dag")
    assert r.status_code == 200
    body = r.json()
    assert body["nodes"] == []
    assert body["edges"] == []
    assert body["checkpoints"] == []
    assert body["groups"] == []
    assert body["side_effects"] == []


def test_nodes_ordered_by_started_at(client):
    rid = "run_ord"
    with Session(engine) as s:
        s.add(
            Run(
                id=rid,
                run_kind="ad_hoc",
                status="running",
                original_prompt="x",
                repo_path="/tmp",
                root_branch_id="b1",
                current_branch_id="b1",
                started_at=_now(),
                created_at=_now(),
            )
        )
        s.flush()
        s.add(
            Node(
                id="late",
                run_id=rid,
                branch_id="b1",
                event_type="PreToolUse",
                type="tool",
                label="late",
                status="success",
                recovery_policy="rerun",
                started_at=datetime(2026, 5, 9, 12, 5, 0),
            )
        )
        s.add(
            Node(
                id="early",
                run_id=rid,
                branch_id="b1",
                event_type="PreToolUse",
                type="tool",
                label="early",
                status="success",
                recovery_policy="rerun",
                started_at=datetime(2026, 5, 9, 12, 0, 0),
            )
        )
        s.commit()
    r = client.get(f"/api/runs/{rid}/dag")
    body = r.json()
    assert [n["id"] for n in body["nodes"]] == ["early", "late"]
