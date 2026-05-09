from __future__ import annotations

from pathlib import Path

import pytest
from runback_server.db import create_all, engine
from runback_server.ingest.normalizer import Normalizer
from runback_server.models import Node, Run, RunGroup
from sqlmodel import Session, select

from tests.fixtures.events import pre_tool_use, todos, todowrite_pre, user_prompt_submit


@pytest.fixture(autouse=True)
def fresh_db():
    create_all()
    with Session(engine) as session:
        for row in session.exec(select(Node)).all():
            session.delete(row)
        for row in session.exec(select(RunGroup)).all():
            session.delete(row)
        for row in session.exec(select(Run)).all():
            session.delete(row)
        session.commit()


@pytest.fixture
def norm(tmp_path):
    return Normalizer(runtime_root=Path(tmp_path))


def _by_label(session: Session, label_substr: str) -> RunGroup | None:
    for group in session.exec(select(RunGroup)).all():
        if label_substr in group.label:
            return group
    return None


def test_initial_todowrite_creates_no_groups(norm):
    sid = "s1"
    norm.handle("run_1", user_prompt_submit(session_id=sid, prompt="x"))
    norm.handle(
        "run_1",
        todowrite_pre(
            session_id=sid,
            todos=todos(
                ("Ticket #1: Foo", "pending"),
                ("Ticket #2: Bar", "pending"),
                ("Ticket #3: Baz", "pending"),
            ),
        ),
    )
    with Session(engine) as session:
        groups = session.exec(select(RunGroup)).all()
    assert groups == []


def test_pending_to_in_progress_opens_group(norm):
    sid = "s1"
    norm.handle("run_1", user_prompt_submit(session_id=sid, prompt="x"))
    norm.handle(
        "run_1",
        todowrite_pre(
            session_id=sid,
            todos=todos(("Ticket #1: Foo", "pending"), ("Ticket #2: Bar", "pending")),
        ),
    )
    norm.handle(
        "run_1",
        todowrite_pre(
            session_id=sid,
            todos=todos(("Ticket #1: Foo", "in_progress"), ("Ticket #2: Bar", "pending")),
        ),
    )
    with Session(engine) as session:
        group = _by_label(session, "Ticket #1: Foo")
    assert group is not None
    assert group.status == "running"
    assert group.kind == "ticket"
    assert group.started_at is not None
    assert group.ended_at is None


def test_in_progress_to_completed_closes_group(norm):
    sid = "s1"
    norm.handle("run_1", user_prompt_submit(session_id=sid, prompt="x"))
    norm.handle("run_1", todowrite_pre(session_id=sid, todos=todos(("Ticket #1: Foo", "pending"))))
    norm.handle(
        "run_1", todowrite_pre(session_id=sid, todos=todos(("Ticket #1: Foo", "in_progress")))
    )
    norm.handle(
        "run_1", todowrite_pre(session_id=sid, todos=todos(("Ticket #1: Foo", "completed")))
    )
    with Session(engine) as session:
        group = _by_label(session, "Ticket #1: Foo")
    assert group is not None
    assert group.status == "success"
    assert group.ended_at is not None


def test_non_ticket_titles_default_to_phase_kind(norm):
    sid = "s1"
    norm.handle("run_1", user_prompt_submit(session_id=sid, prompt="x"))
    norm.handle(
        "run_1",
        todowrite_pre(session_id=sid, todos=todos(("Plan: explore repo", "pending"))),
    )
    norm.handle(
        "run_1", todowrite_pre(session_id=sid, todos=todos(("Plan: explore repo", "in_progress")))
    )
    with Session(engine) as session:
        group = _by_label(session, "Plan: explore repo")
    assert group is not None
    assert group.kind == "phase"


def test_tool_nodes_after_open_get_group_id(norm):
    sid = "s1"
    norm.handle("run_1", user_prompt_submit(session_id=sid, prompt="x"))
    norm.handle("run_1", todowrite_pre(session_id=sid, todos=todos(("Ticket #1: Foo", "pending"))))
    norm.handle(
        "run_1", todowrite_pre(session_id=sid, todos=todos(("Ticket #1: Foo", "in_progress")))
    )
    norm.handle("run_1", pre_tool_use(session_id=sid, tool_name="Read", tool_use_id="t1"))
    with Session(engine) as session:
        node = session.exec(select(Node).where(Node.claude_tool_use_id == "t1")).one()
        ticket = _by_label(session, "Ticket #1: Foo")
    assert ticket is not None
    assert node.group_id == ticket.id


def test_close_then_reopen_creates_no_new_group(norm):
    sid = "s1"
    norm.handle("run_1", user_prompt_submit(session_id=sid, prompt="x"))
    for status in ["pending", "in_progress", "completed", "completed"]:
        norm.handle("run_1", todowrite_pre(session_id=sid, todos=todos(("Ticket #1: Foo", status))))
    with Session(engine) as session:
        groups = session.exec(select(RunGroup)).all()
    assert len(groups) == 1
    assert groups[0].status == "success"
