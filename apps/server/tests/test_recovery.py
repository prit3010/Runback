"""Recovery-point selector and ancestor walker tests."""

from __future__ import annotations

import pytest
from runback_server.db import create_all, engine
from runback_server.models import Checkpoint, Edge, Node, Run, RunGroup, SideEffectLog
from runback_server.replay.recovery import RecoveryRecommendation, select_recovery, walk_ancestors
from sqlmodel import Session, select

from tests.fixtures.replay_dags import DagBuilder


@pytest.fixture(autouse=True)
def fresh_db():
    create_all()
    with Session(engine) as session:
        for model in (SideEffectLog, Edge, Node, Checkpoint, RunGroup, Run):
            for row in session.exec(select(model)).all():
                session.delete(row)
        session.commit()


def test_walk_ancestors_empty_for_node_with_no_predecessors():
    with Session(engine) as session:
        builder = DagBuilder(session, run_id="run_a")
        builder.run()
        builder.node("n1", label="Read")
        builder.commit()
        ancestors = walk_ancestors(session, run_id="run_a", node_id="n1", branch_id="branch_root")
    assert ancestors == []


def test_walk_ancestors_linear_chain():
    with Session(engine) as session:
        builder = DagBuilder(session, run_id="run_b")
        builder.run()
        builder.node("n1", label="A")
        builder.node("n2", label="B")
        builder.node("n3", label="C")
        builder.chain("n1", "n2", "n3")
        builder.commit()
        ancestors = walk_ancestors(session, run_id="run_b", node_id="n3", branch_id="branch_root")
    assert ancestors == ["n2", "n1"]


def test_walk_ancestors_diamond():
    with Session(engine) as session:
        builder = DagBuilder(session, run_id="run_c")
        builder.run()
        for node_id in ("n1", "n2", "n3", "n4"):
            builder.node(node_id, label=node_id)
        builder.chain("n1", "n2")
        builder.chain("n1", "n3")
        builder.chain("n2", "n4")
        builder.chain("n3", "n4")
        builder.commit()
        ancestors = walk_ancestors(session, run_id="run_c", node_id="n4", branch_id="branch_root")
    assert set(ancestors) == {"n1", "n2", "n3"}
    assert ancestors[-1] == "n1"


def test_walk_ancestors_ignores_other_branches():
    with Session(engine) as session:
        root = DagBuilder(session, run_id="run_d", branch="branch_root")
        root.run()
        root.node("n1", label="A")
        root.node("n2", label="B")
        root.chain("n1", "n2")
        root.commit()
        replay = DagBuilder(session, run_id="run_d", branch="branch_replay_1")
        replay.node("n3", label="C")
        replay.node("n4", label="D")
        replay.chain("n3", "n4")
        replay.commit()
        ancestors = walk_ancestors(session, run_id="run_d", node_id="n2", branch_id="branch_root")
    assert ancestors == ["n1"]


def test_walk_ancestors_returns_unique_ids_in_diamond():
    with Session(engine) as session:
        builder = DagBuilder(session, run_id="run_e")
        builder.run()
        for node_id in ("n1", "n2", "n3", "n4"):
            builder.node(node_id, label=node_id)
        builder.chain("n1", "n2")
        builder.chain("n1", "n3")
        builder.chain("n2", "n4")
        builder.chain("n3", "n4")
        builder.commit()
        ancestors = walk_ancestors(session, run_id="run_e", node_id="n4", branch_id="branch_root")
    assert sorted(ancestors) == ["n1", "n2", "n3"]
    assert len(ancestors) == len(set(ancestors))


def _build_simple_run(
    session: Session,
    *,
    with_unsafe: bool = False,
    with_approval: bool = False,
    ledgered_pr: bool = False,
) -> str:
    builder = DagBuilder(session, run_id="run_sel")
    builder.run()
    builder.checkpoint("cp_0", label="run start")
    builder.node("n1", label="Read foo", policy="reuse_cached")
    builder.node(
        "n2",
        label="Edit foo",
        policy="restore_checkpoint",
        checkpoint_before_id="cp_0",
    )
    builder.node("n3", label="Bash test", policy="rerun", tool_name="Bash")
    chain_ids = ["n1", "n2", "n3"]
    if with_approval:
        builder.node("n4", label="gh pr create", policy="requires_approval", tool_name="Bash")
        chain_ids.append("n4")
        if ledgered_pr:
            builder.side_effect(
                node_id="n4",
                kind="gh_pr_create",
                key="gh:pr:owner/repo:fix/issue-1",
                external_ref="https://github.com/owner/repo/pull/1",
            )
    if with_unsafe:
        builder.node("n5", label="rm -rf", policy="unsafe", tool_name="Bash")
        chain_ids.append("n5")
    builder.node("n6", label="Bash test", policy="rerun", status="failed", tool_name="Bash")
    chain_ids.append("n6")
    builder.chain(*chain_ids)
    builder.commit()
    return "n6"


def test_select_recovery_simple_chain_no_approval_or_unsafe():
    with Session(engine) as session:
        failed = _build_simple_run(session)
        rec = select_recovery(
            session, run_id="run_sel", failed_node_id=failed, branch_id="branch_root"
        )
    assert isinstance(rec, RecoveryRecommendation)
    assert rec.recommended_checkpoint_id == "cp_0"
    assert set(rec.reuse_node_ids) == {"n1", "n2"}
    assert set(rec.rerun_node_ids) == {"n3", "n6"}
    assert rec.approval_node_ids == []
    assert rec.unsafe_node_ids == []
    assert 0.0 < rec.confidence <= 1.0


def test_select_recovery_skips_ledgered_approval_node():
    with Session(engine) as session:
        failed = _build_simple_run(session, with_approval=True, ledgered_pr=True)
        rec = select_recovery(
            session, run_id="run_sel", failed_node_id=failed, branch_id="branch_root"
        )
    assert "n4" in rec.reuse_node_ids
    assert "n4" not in rec.approval_node_ids


def test_select_recovery_flags_unledgered_approval_node():
    with Session(engine) as session:
        failed = _build_simple_run(session, with_approval=True)
        rec = select_recovery(
            session, run_id="run_sel", failed_node_id=failed, branch_id="branch_root"
        )
    assert "n4" in rec.approval_node_ids
    assert rec.confidence < 1.0


def test_select_recovery_flags_unsafe_node():
    with Session(engine) as session:
        failed = _build_simple_run(session, with_unsafe=True)
        rec = select_recovery(
            session, run_id="run_sel", failed_node_id=failed, branch_id="branch_root"
        )
    assert "n5" in rec.unsafe_node_ids
    assert rec.confidence < 0.5


def test_select_recovery_uses_run_start_when_no_inline_checkpoint():
    with Session(engine) as session:
        builder = DagBuilder(session, run_id="run_fb")
        builder.run()
        builder.checkpoint("cp_0", label="run start")
        builder.node("n1", label="Read")
        builder.node("n2", label="Bash test", policy="rerun", status="failed", tool_name="Bash")
        builder.chain("n1", "n2")
        builder.commit()
        rec = select_recovery(
            session, run_id="run_fb", failed_node_id="n2", branch_id="branch_root"
        )
    assert rec.recommended_checkpoint_id == "cp_0"


def test_select_recovery_raises_when_failed_node_missing():
    with Session(engine) as session:
        builder = DagBuilder(session, run_id="run_x")
        builder.run()
        builder.commit()
        with pytest.raises(ValueError, match="not found"):
            select_recovery(
                session, run_id="run_x", failed_node_id="ghost", branch_id="branch_root"
            )


def test_select_recovery_raises_when_no_checkpoint_exists():
    with Session(engine) as session:
        builder = DagBuilder(session, run_id="run_no_cp")
        builder.run()
        builder.node("n1", label="Read", status="failed")
        builder.commit()
        with pytest.raises(ValueError, match="no checkpoint"):
            select_recovery(
                session, run_id="run_no_cp", failed_node_id="n1", branch_id="branch_root"
            )
