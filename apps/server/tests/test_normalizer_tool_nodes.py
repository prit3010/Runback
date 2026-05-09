from __future__ import annotations

from pathlib import Path

import pytest
from runback_server.db import create_all, engine
from runback_server.ingest.normalizer import Normalizer
from runback_server.models import Edge, Node, Run
from sqlmodel import Session, select

from tests.fixtures.events import (
    post_tool_use,
    post_tool_use_failure,
    pre_tool_use,
    user_prompt_submit,
)


@pytest.fixture(autouse=True)
def fresh_db():
    create_all()
    with Session(engine) as session:
        for row in session.exec(select(Edge)).all():
            session.delete(row)
        for row in session.exec(select(Node)).all():
            session.delete(row)
        for row in session.exec(select(Run)).all():
            session.delete(row)
        session.commit()


@pytest.fixture
def norm(tmp_path):
    return Normalizer(runtime_root=Path(tmp_path))


def test_pretooluse_creates_pending_node(norm):
    sid = "s1"
    norm.handle("run_1", user_prompt_submit(session_id=sid, prompt="x"))
    norm.handle(
        "run_1",
        pre_tool_use(
            session_id=sid,
            tool_name="Read",
            tool_use_id="t1",
            tool_input={"file_path": "/tmp/foo.py"},
        ),
    )
    with Session(engine) as session:
        nodes = session.exec(select(Node).where(Node.run_id == "run_1")).all()
    tool_node = [node for node in nodes if node.type == "tool"][0]
    assert tool_node.status == "running"
    assert tool_node.tool_name == "Read"
    assert tool_node.claude_tool_use_id == "t1"
    assert tool_node.input_json == {"file_path": "/tmp/foo.py"}
    assert tool_node.recovery_policy == "reuse_cached"
    assert tool_node.classification_reason
    assert tool_node.started_at is not None


def test_posttooluse_reconciles_to_success(norm):
    sid = "s1"
    norm.handle("run_1", user_prompt_submit(session_id=sid, prompt="x"))
    norm.handle("run_1", pre_tool_use(session_id=sid, tool_name="Read", tool_use_id="t1"))
    norm.handle(
        "run_1",
        post_tool_use(session_id=sid, tool_name="Read", tool_use_id="t1", stdout="hello world"),
    )
    with Session(engine) as session:
        node = session.exec(select(Node).where(Node.claude_tool_use_id == "t1")).one()
    assert node.status == "success"
    assert node.ended_at is not None
    assert node.duration_ms is not None and node.duration_ms >= 0
    assert node.output_preview == "hello world"


def test_posttooluse_failure_marks_failed(norm):
    sid = "s1"
    norm.handle("run_1", user_prompt_submit(session_id=sid, prompt="x"))
    norm.handle(
        "run_1",
        pre_tool_use(
            session_id=sid,
            tool_name="Bash",
            tool_use_id="t1",
            tool_input={"command": "false"},
        ),
    )
    norm.handle(
        "run_1",
        post_tool_use_failure(session_id=sid, tool_name="Bash", tool_use_id="t1", error="exit 1"),
    )
    with Session(engine) as session:
        node = session.exec(select(Node).where(Node.claude_tool_use_id == "t1")).one()
    assert node.status == "failed"
    assert node.error and "exit 1" in node.error
    assert node.ended_at is not None


def test_orphan_post_creates_node_anyway(norm):
    sid = "s1"
    norm.handle("run_1", user_prompt_submit(session_id=sid, prompt="x"))
    norm.handle(
        "run_1",
        post_tool_use(session_id=sid, tool_name="Read", tool_use_id="orphan", stdout="data"),
    )
    with Session(engine) as session:
        node = session.exec(select(Node).where(Node.claude_tool_use_id == "orphan")).one()
    assert node.status == "success"
    assert node.tool_name == "Read"


def test_sequence_edge_added_between_consecutive_nodes(norm):
    sid = "s1"
    norm.handle("run_1", user_prompt_submit(session_id=sid, prompt="x"))
    norm.handle("run_1", pre_tool_use(session_id=sid, tool_name="Read", tool_use_id="t1"))
    norm.handle("run_1", post_tool_use(session_id=sid, tool_name="Read", tool_use_id="t1"))
    norm.handle("run_1", pre_tool_use(session_id=sid, tool_name="Grep", tool_use_id="t2"))
    norm.handle("run_1", post_tool_use(session_id=sid, tool_name="Grep", tool_use_id="t2"))
    with Session(engine) as session:
        edges = session.exec(select(Edge).where(Edge.run_id == "run_1")).all()
    assert [edge for edge in edges if edge.edge_type == "sequence"]


def test_user_prompt_creates_prompt_node(norm):
    sid = "s1"
    norm.handle("run_1", user_prompt_submit(session_id=sid, prompt="hello world"))
    with Session(engine) as session:
        nodes = session.exec(select(Node).where(Node.run_id == "run_1")).all()
    prompts = [node for node in nodes if node.type == "prompt"]
    assert len(prompts) == 1
    assert prompts[0].label.startswith("Prompt") or "hello" in prompts[0].label
