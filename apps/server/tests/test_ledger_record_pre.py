"""Side-effect ledger PreToolUse reuse detection."""
from __future__ import annotations

from datetime import UTC, datetime

from runback_server.db import engine
from runback_server.ingest import reconciler
from runback_server.ingest.ids import branch_id, run_id
from runback_server.models import Node, Run, SideEffectLog
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


def _event(kind: str, tool_use_id: str, command: str, stdout: str = "ok"):
    payload = {
        "session_id": "s1",
        "hook_event_name": kind,
        "cwd": "/tmp",
        "tool_name": "Bash",
        "tool_use_id": tool_use_id,
        "tool_input": {"command": command},
    }
    if kind == "PostToolUse":
        payload["tool_response"] = {"stdout": stdout, "stderr": "", "is_image": False}
    return parse_hook_event(payload)


def _full_cycle(
    session: Session,
    run: Run,
    tool_use_id: str,
    command: str,
    stdout: str = "ok",
) -> Node:
    node = reconciler.apply_pre(session, run, _event("PreToolUse", tool_use_id, command))
    reconciler.apply_post(session, run, _event("PostToolUse", tool_use_id, command, stdout))
    return node


def test_second_pre_with_same_key_marks_node_reused():
    with Session(engine) as session:
        run = _mk_run(session)
        _full_cycle(
            session,
            run,
            "tu_p_1",
            "git push origin fix/x",
            stdout="To github.com:acme/widget.git\n  abc..def fix/x -> fix/x",
        )
        session.commit()

    with Session(engine) as session:
        run = session.exec(select(Run)).first()
        node2 = reconciler.apply_pre(
            session,
            run,
            _event("PreToolUse", "tu_p_2", "git push origin fix/x"),
        )
        node2_id = node2.id
        session.commit()

    with Session(engine) as session:
        saved = session.get(Node, node2_id)
        assert saved.status == "reused"
        assert "[reused:" in (saved.classification_reason or "")


def test_second_post_does_not_insert_duplicate_ledger_row():
    with Session(engine) as session:
        run = _mk_run(session)
        _full_cycle(
            session,
            run,
            "tu_g_1",
            "gh pr create --title 'a'",
            stdout="https://github.com/acme/widget/pull/100",
        )
        session.commit()

    with Session(engine) as session:
        run = session.exec(select(Run)).first()
        _full_cycle(
            session,
            run,
            "tu_g_2",
            "gh pr create --title 'a'",
            stdout="https://github.com/acme/widget/pull/200",
        )
        session.commit()

    with Session(engine) as session:
        rows = session.exec(select(SideEffectLog).where(SideEffectLog.kind == "gh_pr_create")).all()
        assert len(rows) == 1
        assert rows[0].external_ref == "https://github.com/acme/widget/pull/100"


def test_different_command_creates_new_ledger_row():
    with Session(engine) as session:
        run = _mk_run(session)
        _full_cycle(
            session,
            run,
            "tu_s_1",
            "slack-cli post --channel growth -m 'first'",
            stdout="ok ts=1.1",
        )
        _full_cycle(
            session,
            run,
            "tu_s_2",
            "slack-cli post --channel growth -m 'second'",
            stdout="ok ts=2.2",
        )
        session.commit()
    with Session(engine) as session:
        rows = session.exec(select(SideEffectLog).where(SideEffectLog.kind == "slack_post")).all()
        assert len(rows) == 2


def test_non_approval_tool_never_writes_ledger():
    with Session(engine) as session:
        run = _mk_run(session)
        _full_cycle(session, run, "tu_r_1", "npm test", stdout="passed")
        _full_cycle(session, run, "tu_r_2", "pytest", stdout="passed")
        session.commit()
    with Session(engine) as session:
        assert session.exec(select(SideEffectLog)).all() == []
