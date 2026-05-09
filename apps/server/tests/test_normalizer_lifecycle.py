from __future__ import annotations

from pathlib import Path

import pytest
from runback_server.db import create_all, engine
from runback_server.ingest.normalizer import Normalizer
from runback_server.models import Run
from sqlmodel import Session, select

from tests.fixtures.events import pre_tool_use, stop, stop_failure, user_prompt_submit


@pytest.fixture(autouse=True)
def fresh_db():
    create_all()
    with Session(engine) as session:
        for row in session.exec(select(Run)).all():
            session.delete(row)
        session.commit()


@pytest.fixture
def norm(tmp_path):
    return Normalizer(runtime_root=Path(tmp_path))


def test_first_event_creates_run(norm):
    payload = user_prompt_submit(prompt="hello", cwd="/tmp/sandbox")
    norm.handle(run_id="run_1", payload=payload)
    with Session(engine) as session:
        run = session.get(Run, "run_1")
    assert run is not None
    assert run.status == "running"
    assert run.original_prompt == "hello"
    assert run.repo_path == "/tmp/sandbox"
    assert run.run_kind == "ad_hoc"
    assert run.root_branch_id == run.current_branch_id
    assert run.started_at is not None


def test_subsequent_events_do_not_recreate(norm):
    sid = "s1"
    norm.handle("run_1", user_prompt_submit(session_id=sid, prompt="hi"))
    norm.handle("run_1", pre_tool_use(session_id=sid, tool_name="Read"))
    with Session(engine) as session:
        rows = session.exec(select(Run).where(Run.id == "run_1")).all()
    assert len(rows) == 1


def test_stop_finalizes_run_success(norm):
    sid = "s1"
    norm.handle("run_1", user_prompt_submit(session_id=sid, prompt="x"))
    norm.handle("run_1", stop(session_id=sid))
    with Session(engine) as session:
        run = session.get(Run, "run_1")
    assert run.status == "success"
    assert run.ended_at is not None


def test_stop_failure_finalizes_run_failed(norm):
    sid = "s1"
    norm.handle("run_1", user_prompt_submit(session_id=sid, prompt="x"))
    norm.handle("run_1", stop_failure(session_id=sid))
    with Session(engine) as session:
        run = session.get(Run, "run_1")
    assert run.status == "failed"
    assert run.ended_at is not None


def test_post_tool_use_failure_does_not_finalize_run(norm):
    sid = "s1"
    norm.handle("run_1", user_prompt_submit(session_id=sid, prompt="x"))
    norm.handle("run_1", pre_tool_use(session_id=sid, tool_name="Bash", tool_use_id="t1"))
    norm.handle(
        "run_1",
        {
            "session_id": sid,
            "hook_event_name": "PostToolUseFailure",
            "cwd": "/tmp/sandbox",
            "tool_name": "Bash",
            "tool_use_id": "t1",
            "tool_input": {},
            "tool_response": {
                "stdout": "",
                "stderr": "boom",
                "interrupted": True,
                "isImage": False,
                "noOutputExpected": False,
            },
        },
    )
    with Session(engine) as session:
        run = session.get(Run, "run_1")
    assert run.status == "running"
