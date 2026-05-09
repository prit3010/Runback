"""Cache-validity checks for replay reuse decisions."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from runback_server.db import create_all, engine
from runback_server.models import Artifact, Node, NodeArtifactEdge, Run
from runback_server.replay.cache import is_artifact_valid, validate_reuse_candidates
from sqlmodel import Session, select


def _now() -> datetime:
    return datetime.now(UTC)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(autouse=True)
def fresh_db():
    create_all()
    with Session(engine) as session:
        for model in (NodeArtifactEdge, Artifact, Node, Run):
            for row in session.exec(select(model)).all():
                session.delete(row)
        session.commit()


def test_is_artifact_valid_returns_true_when_no_path():
    artifact = Artifact(id="art_x", run_id="r1", type="log", created_at=_now())
    assert is_artifact_valid(artifact).valid is True


def test_is_artifact_valid_returns_true_when_hash_matches(tmp_path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("hello")
    artifact = Artifact(
        id="art_y",
        run_id="r1",
        type="text",
        path=str(file_path),
        content_hash=_sha(file_path),
        created_at=_now(),
    )
    assert is_artifact_valid(artifact).valid is True


def test_is_artifact_valid_returns_false_when_hash_mismatches(tmp_path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("hello")
    artifact = Artifact(
        id="art_z",
        run_id="r1",
        type="text",
        path=str(file_path),
        content_hash="0" * 64,
        created_at=_now(),
    )
    result = is_artifact_valid(artifact)
    assert result.valid is False
    assert "hash mismatch" in result.reason.lower()


def test_is_artifact_valid_returns_false_when_file_missing(tmp_path):
    artifact = Artifact(
        id="art_q",
        run_id="r1",
        type="text",
        path=str(tmp_path / "ghost.txt"),
        content_hash="abc",
        created_at=_now(),
    )
    result = is_artifact_valid(artifact)
    assert result.valid is False
    assert "missing" in result.reason.lower()


def test_is_artifact_valid_webfetch_ttl_expired():
    artifact = Artifact(
        id="art_w",
        run_id="r1",
        type="html",
        source_url="https://x",
        created_at=_now() - timedelta(days=2),
        cache_policy_json={"ttl_hours": 24},
    )
    result = is_artifact_valid(artifact)
    assert result.valid is False
    assert "ttl" in result.reason.lower()


def test_is_artifact_valid_webfetch_within_ttl():
    artifact = Artifact(
        id="art_w2",
        run_id="r1",
        type="html",
        source_url="https://x",
        created_at=_now(),
        cache_policy_json={"ttl_hours": 24},
    )
    assert is_artifact_valid(artifact).valid is True


def test_validate_reuse_candidates_filters_invalid_artifacts(tmp_path):
    good = tmp_path / "good.txt"
    bad = tmp_path / "bad.txt"
    good.write_text("g")
    bad.write_text("b")
    with Session(engine) as session:
        session.add(
            Run(
                id="r1",
                status="running",
                original_prompt="cache test",
                repo_path="/tmp/x",
                workspace_path="/tmp/x",
                root_branch_id="br",
                current_branch_id="br",
                created_at=_now(),
            )
        )
        session.flush()
        session.add(
            Node(
                id="n1",
                run_id="r1",
                branch_id="br",
                event_type="PreToolUse",
                type="tool",
                label="Read good",
                tool_name="Read",
                status="success",
                recovery_policy="reuse_cached",
            )
        )
        session.flush()
        session.add(
            Node(
                id="n2",
                run_id="r1",
                branch_id="br",
                event_type="PreToolUse",
                type="tool",
                label="Read bad",
                tool_name="Read",
                status="success",
                recovery_policy="reuse_cached",
            )
        )
        session.flush()
        session.add(
            Artifact(
                id="a1",
                run_id="r1",
                type="text",
                path=str(good),
                content_hash=_sha(good),
                created_at=_now(),
            )
        )
        session.flush()
        session.add(
            Artifact(
                id="a2",
                run_id="r1",
                type="text",
                path=str(bad),
                content_hash="deadbeef" * 8,
                created_at=_now(),
            )
        )
        session.flush()
        session.add(
            NodeArtifactEdge(
                id="e1",
                run_id="r1",
                node_id="n1",
                artifact_id="a1",
                direction="output",
                created_at=_now(),
            )
        )
        session.add(
            NodeArtifactEdge(
                id="e2",
                run_id="r1",
                node_id="n2",
                artifact_id="a2",
                direction="output",
                created_at=_now(),
            )
        )
        session.commit()
        valid, invalid = validate_reuse_candidates(
            session,
            run_id="r1",
            candidate_node_ids=["n1", "n2"],
        )
    assert "n1" in valid
    assert "n2" in invalid
