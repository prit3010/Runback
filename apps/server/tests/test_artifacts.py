from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from runback_server.db import create_all, engine
from runback_server.ingest.normalizer import Normalizer
from runback_server.models import Artifact, Node, NodeArtifactEdge, Run
from sqlmodel import Session, select

from tests.fixtures.events import post_tool_use, pre_tool_use, user_prompt_submit


@pytest.fixture(autouse=True)
def fresh_db():
    create_all()
    with Session(engine) as session:
        for row in session.exec(select(NodeArtifactEdge)).all():
            session.delete(row)
        for row in session.exec(select(Artifact)).all():
            session.delete(row)
        for row in session.exec(select(Node)).all():
            session.delete(row)
        for row in session.exec(select(Run)).all():
            session.delete(row)
        session.commit()


@pytest.fixture
def runtime(tmp_path):
    return tmp_path


@pytest.fixture
def norm(runtime, monkeypatch):
    monkeypatch.setenv("RUNBACK_RUNTIME_ROOT", str(runtime))
    return Normalizer(runtime_root=runtime)


def _make_persisted_file(tmp_path: Path, contents: str) -> Path:
    path = tmp_path / "claude-side" / "persisted-output.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents)
    return path


def test_small_output_no_artifact_copied(norm):
    sid = "s1"
    norm.handle("run_1", user_prompt_submit(session_id=sid, prompt="x"))
    norm.handle("run_1", pre_tool_use(session_id=sid, tool_name="Bash", tool_use_id="t1"))
    norm.handle(
        "run_1",
        post_tool_use(session_id=sid, tool_name="Bash", tool_use_id="t1", stdout="hi"),
    )
    with Session(engine) as session:
        artifacts = session.exec(select(Artifact)).all()
    assert artifacts == []


def test_large_output_copied_to_run_scope_with_hash(norm, tmp_path):
    big = "x" * 600_000
    persisted = _make_persisted_file(tmp_path, big)
    sid = "s1"
    norm.handle("run_1", user_prompt_submit(session_id=sid, prompt="x"))
    norm.handle(
        "run_1",
        pre_tool_use(
            session_id=sid,
            tool_name="Bash",
            tool_use_id="t1",
            tool_input={"command": "cat big.txt"},
        ),
    )
    norm.handle(
        "run_1",
        post_tool_use(
            session_id=sid,
            tool_name="Bash",
            tool_use_id="t1",
            stdout=big[:30000],
            persisted_output_path=str(persisted),
            persisted_output_size=len(big),
            tool_input={"command": "cat big.txt"},
        ),
    )
    with Session(engine) as session:
        node = session.exec(select(Node).where(Node.claude_tool_use_id == "t1")).one()
        artifacts = session.exec(select(Artifact).where(Artifact.run_id == "run_1")).all()
        edges = session.exec(
            select(NodeArtifactEdge).where(NodeArtifactEdge.node_id == node.id)
        ).all()
    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact.size_bytes == len(big)
    assert artifact.content_hash == hashlib.sha256(big.encode()).hexdigest()
    assert artifact.path is not None
    artifact_path = Path(artifact.path)
    assert "runs/run_1/artifacts" in str(artifact_path)
    assert artifact_path.exists()
    assert len(artifact_path.read_text()) == len(big)
    assert len(edges) == 1
    assert edges[0].direction == "output"
    assert edges[0].artifact_id == artifact.id


def test_persisted_path_missing_does_not_crash(norm):
    sid = "s1"
    norm.handle("run_1", user_prompt_submit(session_id=sid, prompt="x"))
    norm.handle("run_1", pre_tool_use(session_id=sid, tool_name="Bash", tool_use_id="t1"))
    norm.handle(
        "run_1",
        post_tool_use(
            session_id=sid,
            tool_name="Bash",
            tool_use_id="t1",
            stdout="x" * 5,
            persisted_output_path="/nonexistent/path",
            persisted_output_size=999_999,
        ),
    )
    with Session(engine) as session:
        artifacts = session.exec(select(Artifact)).all()
    assert artifacts == []
