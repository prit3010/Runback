"""Smoke tests for SQLModel tables."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from runback_server.db import create_all, engine
from runback_server.models import (
    Artifact,
    Checkpoint,
    Edge,
    Flow,
    FlowVersion,
    Node,
    NodeArtifactEdge,
    ReplayAttempt,
    Run,
    RunGroup,
    Runner,
    SideEffectLog,
)
from sqlmodel import Session, SQLModel


@pytest.fixture
def session():
    SQLModel.metadata.drop_all(engine)
    create_all()
    with Session(engine) as s:
        yield s
    SQLModel.metadata.drop_all(engine)


def now() -> datetime:
    return datetime.now(UTC)


def test_flow_roundtrip(session):
    flow = Flow(
        id="flow_1",
        name="test flow",
        repo_path="/tmp/x",
        agent="claude_code",
        active_version_id="fv_1",
        enabled=True,
        created_at=now(),
        updated_at=now(),
    )
    session.add(flow)
    session.commit()
    fetched = session.get(Flow, "flow_1")
    assert fetched is not None
    assert fetched.name == "test flow"


def test_run_with_run_group_and_node(session):
    run = Run(
        id="run_1",
        run_kind="ad_hoc",
        status="running",
        original_prompt="fix tests",
        repo_path="/tmp/x",
        root_branch_id="branch_root",
        current_branch_id="branch_root",
        created_at=now(),
    )
    session.add(run)
    group = RunGroup(
        id="grp_1",
        run_id="run_1",
        parent_group_id=None,
        label="Ticket #1: foo",
        kind="ticket",
        status="running",
        started_at=now(),
    )
    session.add(group)
    session.commit()
    node = Node(
        id="node_1",
        run_id="run_1",
        branch_id="branch_root",
        group_id="grp_1",
        event_type="PreToolUse",
        type="tool",
        label="Read foo.py",
        tool_name="Read",
        status="success",
        recovery_policy="reuse_cached",
    )
    session.add(node)
    session.commit()
    assert session.get(Node, "node_1").group_id == "grp_1"


def test_checkpoint_artifact_replay_runner_sideeffect(session):
    run = Run(
        id="run_x",
        run_kind="ad_hoc",
        status="running",
        original_prompt="x",
        repo_path="/tmp/x",
        root_branch_id="branch_root",
        current_branch_id="branch_root",
        created_at=now(),
    )
    node = Node(
        id="node_1",
        run_id="run_x",
        branch_id="branch_root",
        event_type="PreToolUse",
        type="tool",
        label="Bash npm test",
        tool_name="Bash",
        status="failed",
        recovery_policy="rerun",
    )
    session.add(run)
    session.commit()
    session.add(node)
    session.commit()
    session.add(
        Checkpoint(
            id="cp_0",
            run_id="run_x",
            branch_id="branch_root",
            label="run start",
            backend="hidden_ref",
            git_ref="refs/runback/run_x/0",
            workspace_path="/tmp/ws",
            created_at=now(),
        )
    )
    session.add(
        Artifact(
            id="art_1",
            run_id="run_x",
            produced_by_node_id="node_1",
            type="log",
            path=".runback/runs/run_x/artifacts/node_1/output.txt",
            created_at=now(),
        )
    )
    session.commit()
    session.add(
        NodeArtifactEdge(
            id="nae_1",
            run_id="run_x",
            node_id="node_1",
            artifact_id="art_1",
            direction="output",
            required=True,
            created_at=now(),
        )
    )
    session.add(
        ReplayAttempt(
            id="ra_1",
            run_id="run_x",
            source_node_id="node_1",
            source_checkpoint_id="cp_0",
            parent_branch_id="branch_root",
            new_branch_id="branch_replay_1",
            resume_prompt="resume...",
            status="created",
            created_at=now(),
        )
    )
    session.add(
        Runner(
            id="runner_1",
            name="local",
            status="online",
            claude_code_available=True,
            version="0.0.0",
            created_at=now(),
        )
    )
    session.add(
        SideEffectLog(
            run_id="run_x",
            branch_id="branch_root",
            node_id="node_1",
            kind="gh_pr_create",
            idempotency_key="gh:pr:owner/repo:fix/issue-1",
            status="executed",
        )
    )
    session.commit()
    assert session.get(Checkpoint, "cp_0").git_ref == "refs/runback/run_x/0"


def test_flow_version(session):
    session.add(
        Flow(
            id="flow_1",
            name="test flow",
            repo_path="/tmp/x",
            active_version_id="fv_1",
            created_at=now(),
            updated_at=now(),
        )
    )
    session.add(
        FlowVersion(
            id="fv_1",
            flow_id="flow_1",
            version_number=1,
            prompt="do thing",
            replay_mode="semi_automatic",
            side_effect_policy="label_only",
            cache_policy_json={},
            created_at=now(),
        )
    )
    session.commit()
    assert session.get(FlowVersion, "fv_1").prompt == "do thing"


def test_edge(session):
    session.add(
        Run(
            id="run_1",
            run_kind="ad_hoc",
            status="running",
            original_prompt="x",
            repo_path="/tmp/x",
            root_branch_id="branch_root",
            current_branch_id="branch_root",
            created_at=now(),
        )
    )
    session.commit()
    session.add(
        Edge(
            id="edge_1",
            run_id="run_1",
            branch_id="branch_root",
            source_node_id="node_1",
            target_node_id="node_2",
            edge_type="sequence",
        )
    )
    session.commit()
    assert session.get(Edge, "edge_1").edge_type == "sequence"
