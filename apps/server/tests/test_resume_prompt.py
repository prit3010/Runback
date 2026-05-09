"""Resume prompt builder tests."""

from __future__ import annotations

import pytest
from runback_server.db import create_all, engine
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
from runback_server.replay.recovery import RecoveryRecommendation
from runback_server.replay.resume_prompt import (
    MAX_PROMPT_BYTES,
    build_resume_prompt,
    gather_prompt_inputs,
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


def _seed_canonical_run(session: Session) -> tuple[str, str, str, RecoveryRecommendation]:
    builder = DagBuilder(session, run_id="run_p")
    builder.run(prompt="Process every ticket in BACKLOG.md")
    builder.checkpoint("cp_0", label="run start")
    builder.checkpoint("cp_pre_edit_t4", label="checkpoint_pre_edit_4")
    builder.group("g1", label="Ticket #1: foo", status="success")
    builder.group("g4", label="Ticket #4: fix email regex", status="failed")
    builder.node("n1", label="Read BACKLOG.md", policy="reuse_cached", group_id="g1")
    builder.node("n2", label="Edit handler.ts", policy="restore_checkpoint", group_id="g1")
    builder.node(
        "n3", label="gh pr create", policy="requires_approval", group_id="g1", tool_name="Bash"
    )
    builder.side_effect(
        node_id="n3",
        kind="gh_pr_create",
        key="gh:pr:owner/repo:fix/issue-1",
        external_ref="https://github.com/owner/repo/pull/101",
    )
    builder.node(
        "n4",
        label="Edit auth.ts",
        policy="restore_checkpoint",
        group_id="g4",
        checkpoint_before_id="cp_pre_edit_t4",
    )
    builder.node(
        "n5",
        label="Bash npm test",
        policy="rerun",
        group_id="g4",
        tool_name="Bash",
        status="failed",
        output_preview="FAIL src/auth/token.test.ts\n  email regex rejects `+`",
        error="exit 1",
    )
    builder.chain("n1", "n2", "n3", "n4", "n5")
    builder.commit()
    rec = RecoveryRecommendation(
        source_node_id="n5",
        recommended_checkpoint_id="cp_pre_edit_t4",
        confidence=0.9,
        reasons=["recovered from checkpoint cp_pre_edit_t4"],
        reuse_node_ids=["n1", "n2", "n3", "n4"],
        rerun_node_ids=["n5"],
        approval_node_ids=[],
        unsafe_node_ids=[],
    )
    return "run_p", "n5", "branch_root", rec


def test_gather_prompt_inputs_basic_shape():
    with Session(engine) as session:
        run_id, failed, branch, rec = _seed_canonical_run(session)
        inputs = gather_prompt_inputs(
            session,
            run_id=run_id,
            failed_node_id=failed,
            branch_id=branch,
            recommendation=rec,
            user_context=None,
        )
    assert inputs["original_prompt"] == "Process every ticket in BACKLOG.md"
    assert inputs["checkpoint_label"] == "checkpoint_pre_edit_4"
    assert inputs["failed_node_label"] == "Bash npm test"
    assert "FAIL src/auth/token.test.ts" in inputs["failure_output"]
    assert "gh:pr:owner/repo:fix/issue-1" in {
        se["key"] for se in inputs["already_executed_side_effects"]
    }
    group = next(g for g in inputs["completed_groups"] if g["label"] == "Ticket #1: foo")
    assert any("github" in ref for ref in group["external_refs"])


def test_gather_prompt_inputs_includes_user_context():
    with Session(engine) as session:
        run_id, failed, branch, rec = _seed_canonical_run(session)
        inputs = gather_prompt_inputs(
            session,
            run_id=run_id,
            failed_node_id=failed,
            branch_id=branch,
            recommendation=rec,
            user_context="email regex must accept '+'",
        )
    assert inputs["user_context"] == "email regex must accept '+'"


def test_build_resume_prompt_renders_template_with_real_inputs():
    with Session(engine) as session:
        run_id, failed, branch, rec = _seed_canonical_run(session)
        prompt = build_resume_prompt(
            session,
            run_id=run_id,
            failed_node_id=failed,
            branch_id=branch,
            recommendation=rec,
            user_context="hint",
        )
    assert "Process every ticket in BACKLOG.md" in prompt
    assert "checkpoint_pre_edit_4" in prompt
    assert "Bash npm test" in prompt
    assert "https://github.com/owner/repo/pull/101" in prompt
    assert "ALREADY EXECUTED" in prompt
    assert "hint" in prompt
    assert "TodoWrite" in prompt


def test_build_resume_prompt_truncates_failure_output_when_oversized(monkeypatch):
    monkeypatch.setattr("runback_server.replay.resume_prompt.MAX_PROMPT_BYTES", 2048)
    with Session(engine) as session:
        builder = DagBuilder(session, run_id="run_big")
        builder.run(prompt="big prompt")
        builder.checkpoint("cp_0", label="run start")
        builder.node(
            "nbig",
            label="Bash test",
            policy="rerun",
            status="failed",
            tool_name="Bash",
            output_preview="X" * 200_000,
            error="boom",
        )
        builder.commit()
        rec = RecoveryRecommendation(
            source_node_id="nbig",
            recommended_checkpoint_id="cp_0",
            confidence=1.0,
            reasons=["fallback to run start"],
            rerun_node_ids=["nbig"],
        )
        prompt = build_resume_prompt(
            session,
            run_id="run_big",
            failed_node_id="nbig",
            branch_id="branch_root",
            recommendation=rec,
            user_context=None,
        )
    assert len(prompt.encode("utf-8")) <= 2048
    assert "big prompt" in prompt
    assert "truncated" in prompt


def test_build_resume_prompt_includes_scope_instruction_when_groups_present():
    with Session(engine) as session:
        builder = DagBuilder(session, run_id="run_scope")
        builder.run(prompt="multi-ticket")
        builder.checkpoint("cp_0", label="run start")
        builder.group("g1", label="Ticket #1: a", status="success")
        builder.group("g2", label="Ticket #2: b", status="failed")
        builder.group("g3", label="Ticket #3: c", status="pending")
        builder.node("n1", label="Edit a", policy="restore_checkpoint", group_id="g1")
        builder.node(
            "n2",
            label="Edit b",
            policy="restore_checkpoint",
            group_id="g2",
            status="failed",
            error="boom",
        )
        builder.chain("n1", "n2")
        builder.commit()
        rec = RecoveryRecommendation(
            source_node_id="n2",
            recommended_checkpoint_id="cp_0",
            confidence=1.0,
            reasons=["x"],
            reuse_node_ids=["n1"],
            rerun_node_ids=["n2"],
        )
        prompt = build_resume_prompt(
            session,
            run_id="run_scope",
            failed_node_id="n2",
            branch_id="branch_root",
            recommendation=rec,
            user_context=None,
        )
    assert "Ticket #2" in prompt
    assert "Ticket #3" in prompt


def test_max_prompt_bytes_constant_is_documented():
    assert MAX_PROMPT_BYTES == 32 * 1024
