"""GET /api/runs/{runId}/nodes/{nodeId} returns NodeDetail with artifacts."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from runback_server.db import create_all, engine
from runback_server.main import app
from runback_server.models import (
    Artifact,
    Checkpoint,
    Edge,
    Node,
    NodeArtifactEdge,
    Run,
    RunGroup,
    SideEffectLog,
)


@pytest.fixture(autouse=True)
def fresh_db():
    create_all()
    with Session(engine) as s:
        for row in s.exec(select(NodeArtifactEdge)).all():
            s.delete(row)
        for row in s.exec(select(Artifact)).all():
            s.delete(row)
        for row in s.exec(select(Edge)).all():
            s.delete(row)
        for row in s.exec(select(Checkpoint)).all():
            s.delete(row)
        for row in s.exec(select(SideEffectLog)).all():
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


def _seed_node_with_artifact() -> tuple[str, str, str]:
    rid, nid, aid = "run_nd", "node_nd", "art_nd"
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
                id=nid,
                run_id=rid,
                branch_id="b1",
                event_type="PreToolUse",
                type="tool",
                tool_name="Bash",
                label="Bash: echo hi",
                input_json={"command": "echo hi"},
                output_json={"stdout": "hi"},
                output_preview="hi",
                status="success",
                recovery_policy="rerun",
                classification_reason="Bash test/build/lint",
                classification_confidence=0.9,
                checkpoint_before_id="cp_before",
                checkpoint_after_id="cp_after",
                started_at=_now(),
            )
        )
        s.flush()
        s.add(
            Artifact(
                id=aid,
                run_id=rid,
                node_id=nid,
                produced_by_node_id=nid,
                type="log",
                path="/tmp/x/out.txt",
                description="stdout",
                content_preview="hi",
                content_hash="abc123",
                size_bytes=2,
                created_at=_now(),
            )
        )
        s.add(
            NodeArtifactEdge(
                id="nae_1",
                run_id=rid,
                node_id=nid,
                artifact_id=aid,
                direction="output",
                required=True,
                created_at=_now(),
            )
        )
        s.commit()
    return rid, nid, aid


def test_get_node_detail_returns_full_payload(client):
    rid, nid, aid = _seed_node_with_artifact()
    r = client.get(f"/api/runs/{rid}/nodes/{nid}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == nid
    assert body["tool_name"] == "Bash"
    assert body["status"] == "success"
    assert body["input_json"] == {"command": "echo hi"}
    assert body["output_json"] == {"stdout": "hi"}
    assert body["classification_reason"] == "Bash test/build/lint"
    assert body["classification_confidence"] == 0.9
    assert body["checkpoint_before_id"] == "cp_before"
    assert body["checkpoint_after_id"] == "cp_after"
    assert isinstance(body["artifacts"], list)
    assert len(body["artifacts"]) == 1
    art = body["artifacts"][0]
    assert art["id"] == aid
    assert art["path"] == "/tmp/x/out.txt"
    assert art["content_hash"] == "abc123"


def test_get_node_detail_404_when_run_missing(client):
    r = client.get("/api/runs/missing/nodes/whatever")
    assert r.status_code == 404


def test_get_node_detail_404_when_node_not_in_run(client):
    rid, nid, _ = _seed_node_with_artifact()
    r = client.get(f"/api/runs/{rid}/nodes/wrong_node")
    assert r.status_code == 404


def test_get_node_detail_node_in_other_run_returns_404(client):
    rid, nid, _ = _seed_node_with_artifact()
    with Session(engine) as s:
        s.add(
            Run(
                id="other_run",
                run_kind="ad_hoc",
                status="running",
                original_prompt="x",
                repo_path="/tmp",
                root_branch_id="b2",
                current_branch_id="b2",
                started_at=_now(),
                created_at=_now(),
            )
        )
        s.commit()
    r = client.get(f"/api/runs/other_run/nodes/{nid}")
    assert r.status_code == 404


def test_get_node_detail_no_artifacts_returns_empty_list(client):
    rid = "run_noart"
    nid = "node_noart"
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
                id=nid,
                run_id=rid,
                branch_id="b1",
                event_type="PreToolUse",
                type="tool",
                tool_name="Read",
                label="Read foo",
                status="success",
                recovery_policy="reuse_cached",
                started_at=_now(),
            )
        )
        s.commit()
    r = client.get(f"/api/runs/{rid}/nodes/{nid}")
    assert r.status_code == 200
    body = r.json()
    assert body["artifacts"] == []
