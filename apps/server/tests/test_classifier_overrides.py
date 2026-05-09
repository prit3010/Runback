"""Manual override unit tests."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from runback_server.classifier.overrides import VALID_POLICIES, OverrideError, apply_override
from runback_server.db import engine
from runback_server.ingest.ids import branch_id, node_id, run_id
from runback_server.models import Node, Run
from sqlmodel import Session


def _mk_run_node(session: Session) -> tuple[Run, Node]:
    b = branch_id()
    run = Run(
        id=run_id(),
        run_kind="ad_hoc",
        status="running",
        original_prompt="(test)",
        repo_path="/tmp",
        workspace_path="/tmp",
        root_branch_id=b,
        current_branch_id=b,
        started_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )
    node = Node(
        id=node_id(),
        run_id=run.id,
        branch_id=b,
        event_type="PreToolUse",
        type="tool",
        label="Bash: ls",
        tool_name="Bash",
        status="running",
        recovery_policy="unknown",
        classification_reason="bash command did not match any matrix rule",
        started_at=datetime.now(UTC),
    )
    session.add(run)
    session.flush()
    session.add(node)
    session.flush()
    return run, node


def test_apply_override_updates_policy_and_prefixes_reason():
    with Session(engine) as session:
        _, node = _mk_run_node(session)
        apply_override(session, node, recovery_policy="rerun", reason="user said it's safe")
        node_id_value = node.id
        session.commit()
    with Session(engine) as session:
        saved = session.get(Node, node_id_value)
        assert saved.recovery_policy == "rerun"
        assert saved.classification_reason.startswith("[OVERRIDE]")
        assert "user said it's safe" in saved.classification_reason


def test_apply_override_rejects_invalid_policy():
    with Session(engine) as session:
        _, node = _mk_run_node(session)
        with pytest.raises(OverrideError, match="invalid recovery_policy"):
            apply_override(session, node, recovery_policy="not_a_real_policy", reason="bad")


def test_apply_override_rejects_empty_reason():
    with Session(engine) as session:
        _, node = _mk_run_node(session)
        with pytest.raises(OverrideError, match="reason"):
            apply_override(session, node, recovery_policy="rerun", reason="")


def test_valid_policies_constant_matches_spec():
    assert set(VALID_POLICIES) == {
        "rerun",
        "reuse_cached",
        "restore_checkpoint",
        "requires_approval",
        "unsafe",
        "unknown",
    }


def test_apply_override_twice_keeps_only_one_prefix():
    with Session(engine) as session:
        _, node = _mk_run_node(session)
        apply_override(session, node, recovery_policy="rerun", reason="r1")
        apply_override(session, node, recovery_policy="unsafe", reason="r2")
        node_id_value = node.id
        session.commit()
    with Session(engine) as session:
        saved = session.get(Node, node_id_value)
        assert saved.classification_reason.count("[OVERRIDE]") == 1
        assert "r2" in saved.classification_reason
        assert saved.recovery_policy == "unsafe"
