"""Side-effect ledger PostToolUse writes."""
from __future__ import annotations

from datetime import UTC, datetime

from runback_server.db import engine
from runback_server.ingest import reconciler
from runback_server.ingest.ids import branch_id, run_id
from runback_server.models import Run, SideEffectLog
from runback_server.schemas.hook_events import parse_hook_event
from sqlmodel import Session, select


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


def _pre(command: str, tool_use_id: str):
    return parse_hook_event(
        {
            "session_id": "s1",
            "hook_event_name": "PreToolUse",
            "cwd": "/tmp",
            "tool_name": "Bash",
            "tool_use_id": tool_use_id,
            "tool_input": {"command": command},
        }
    )


def _post(command: str, tool_use_id: str, stdout: str):
    return parse_hook_event(
        {
            "session_id": "s1",
            "hook_event_name": "PostToolUse",
            "cwd": "/tmp",
            "tool_name": "Bash",
            "tool_use_id": tool_use_id,
            "tool_input": {"command": command},
            "tool_response": {"stdout": stdout, "stderr": "", "is_image": False},
        }
    )


def test_post_for_git_push_inserts_ledger_row():
    with Session(engine) as session:
        run = _mk_run(session)
        node = reconciler.apply_pre(session, run, _pre("git push origin fix/x", "tu_push_1"))
        reconciler.apply_post(
            session,
            run,
            _post(
                "git push origin fix/x",
                "tu_push_1",
                "To github.com:acme/widget.git\n  abc..def fix/x -> fix/x",
            ),
        )
        node_id = node.id
        session.commit()
    with Session(engine) as session:
        rows = session.exec(select(SideEffectLog).where(SideEffectLog.node_id == node_id)).all()
        assert len(rows) == 1
        assert rows[0].kind == "git_push"
        assert rows[0].status == "executed"
        assert rows[0].idempotency_key.startswith("git:push:")
        assert rows[0].executed_at is not None


def test_post_for_gh_pr_create_inserts_ledger_row_with_external_ref():
    with Session(engine) as session:
        run = _mk_run(session)
        command = "gh pr create --title 'fix' --body 'b'"
        node = reconciler.apply_pre(session, run, _pre(command, "tu_pr_1"))
        reconciler.apply_post(session, run, _post(command, "tu_pr_1", "https://github.com/acme/widget/pull/101"))
        node_id = node.id
        session.commit()
    with Session(engine) as session:
        rows = session.exec(select(SideEffectLog).where(SideEffectLog.node_id == node_id)).all()
        assert len(rows) == 1
        assert rows[0].kind == "gh_pr_create"
        assert rows[0].status == "executed"
        assert rows[0].external_ref == "https://github.com/acme/widget/pull/101"


def test_post_for_slack_post_inserts_ledger_row():
    with Session(engine) as session:
        run = _mk_run(session)
        command = "slack-cli post --channel growth -m 'hello'"
        reconciler.apply_pre(session, run, _pre(command, "tu_slack_1"))
        reconciler.apply_post(session, run, _post(command, "tu_slack_1", "ok ts=1234.5678"))
        session.commit()
    with Session(engine) as session:
        rows = session.exec(select(SideEffectLog).where(SideEffectLog.kind == "slack_post")).all()
        assert len(rows) == 1
        assert rows[0].idempotency_key.startswith("slack:#growth:")


def test_post_for_non_approval_node_does_not_insert_ledger_row():
    with Session(engine) as session:
        run = _mk_run(session)
        reconciler.apply_pre(session, run, _pre("npm test", "tu_test_1"))
        reconciler.apply_post(session, run, _post("npm test", "tu_test_1", "ok"))
        session.commit()
    with Session(engine) as session:
        assert session.exec(select(SideEffectLog)).all() == []
