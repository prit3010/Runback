"""Reconciler integration with the classifier."""
from __future__ import annotations

from datetime import UTC, datetime

from runback_server.db import engine
from runback_server.ingest import reconciler
from runback_server.ingest.ids import branch_id, run_id
from runback_server.models import Node, Run
from runback_server.schemas.hook_events import parse_hook_event
from sqlmodel import Session


def _mk_run(session: Session) -> Run:
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
    session.add(run)
    session.flush()
    return run


def _pre(tool_name: str, tool_use_id: str, tool_input: dict):
    return parse_hook_event(
        {
            "session_id": "s1",
            "hook_event_name": "PreToolUse",
            "cwd": "/tmp",
            "tool_name": tool_name,
            "tool_use_id": tool_use_id,
            "tool_input": tool_input,
        }
    )


def test_apply_pre_read_gets_reuse_cached():
    with Session(engine) as session:
        run = _mk_run(session)
        node = reconciler.apply_pre(session, run, _pre("Read", "tu1", {"file_path": "/tmp/x"}))
        node_id = node.id
        session.commit()
    with Session(engine) as session:
        saved = session.get(Node, node_id)
        assert saved.recovery_policy == "reuse_cached"
        assert saved.classification_reason


def test_apply_pre_edit_gets_restore_checkpoint():
    with Session(engine) as session:
        run = _mk_run(session)
        node = reconciler.apply_pre(
            session,
            run,
            _pre("Edit", "tu2", {"file_path": "/tmp/x", "old_string": "a", "new_string": "b"}),
        )
        node_id = node.id
        session.commit()
    with Session(engine) as session:
        assert session.get(Node, node_id).recovery_policy == "restore_checkpoint"


def test_apply_pre_bash_test_gets_rerun():
    with Session(engine) as session:
        run = _mk_run(session)
        node = reconciler.apply_pre(session, run, _pre("Bash", "tu3", {"command": "npm test"}))
        node_id = node.id
        session.commit()
    with Session(engine) as session:
        assert session.get(Node, node_id).recovery_policy == "rerun"


def test_apply_pre_bash_git_push_gets_requires_approval():
    with Session(engine) as session:
        run = _mk_run(session)
        node = reconciler.apply_pre(
            session,
            run,
            _pre("Bash", "tu4", {"command": "git push origin main"}),
        )
        node_id = node.id
        session.commit()
    with Session(engine) as session:
        saved = session.get(Node, node_id)
        assert saved.recovery_policy == "requires_approval"
        assert "git push" in saved.classification_reason.lower()


def test_apply_pre_bash_rm_rf_gets_unsafe():
    with Session(engine) as session:
        run = _mk_run(session)
        node = reconciler.apply_pre(
            session,
            run,
            _pre("Bash", "tu5", {"command": "rm -rf node_modules"}),
        )
        node_id = node.id
        session.commit()
    with Session(engine) as session:
        assert session.get(Node, node_id).recovery_policy == "unsafe"


def test_apply_pre_unknown_tool_keeps_unknown_policy():
    with Session(engine) as session:
        run = _mk_run(session)
        node = reconciler.apply_pre(session, run, _pre("FooBarTool", "tu6", {}))
        node_id = node.id
        session.commit()
    with Session(engine) as session:
        saved = session.get(Node, node_id)
        assert saved.recovery_policy == "unknown"
        assert saved.classification_reason
