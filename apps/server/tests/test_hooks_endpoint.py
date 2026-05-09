from __future__ import annotations

from fastapi.testclient import TestClient
from runback_server.db import create_all, engine
from runback_server.main import app
from runback_server.models import Node, Run, RunGroup
from sqlmodel import Session, select

from tests.fixtures.events import post_tool_use, pre_tool_use, stop, user_prompt_submit


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


def _post(client: TestClient, run_id: str, payload: dict):
    return client.post("/api/hooks/claude", json=payload, headers={"x-runback-run-id": run_id})


def test_endpoint_accepts_event_and_returns_202():
    fresh_db()
    client = TestClient(app)
    response = _post(client, "run_1", user_prompt_submit(prompt="hi"))
    assert response.status_code == 202
    body = response.json()
    assert body["accepted"] is True
    assert body["run_id"] == "run_1"


def test_endpoint_rejects_missing_run_id_header():
    fresh_db()
    client = TestClient(app)
    response = client.post("/api/hooks/claude", json=user_prompt_submit(prompt="hi"))
    assert response.status_code in (400, 422)


def test_endpoint_rejects_malformed_payload():
    fresh_db()
    client = TestClient(app)
    response = _post(client, "run_1", {"not_a_real_event": True})
    assert response.status_code in (400, 422)


def test_endpoint_idempotent_on_duplicate_post():
    fresh_db()
    client = TestClient(app)
    sid = "s1"
    pre = pre_tool_use(session_id=sid, tool_name="Read", tool_use_id="t1")
    _post(client, "run_1", user_prompt_submit(session_id=sid, prompt="x"))
    _post(client, "run_1", pre)
    _post(client, "run_1", pre)
    with Session(engine) as session:
        rows = session.exec(select(Node).where(Node.claude_tool_use_id == "t1")).all()
    assert len(rows) == 1


def test_endpoint_archives_to_jsonl(tmp_path, monkeypatch):
    fresh_db()
    monkeypatch.setenv("RUNBACK_RUNTIME_ROOT", str(tmp_path))
    client = TestClient(app)
    response = _post(client, "run_1", user_prompt_submit(prompt="hi"))
    assert response.status_code == 202
    assert (tmp_path / "runs" / "run_1" / "events.jsonl").exists()


def test_full_session_creates_full_dag():
    fresh_db()
    client = TestClient(app)
    sid = "s1"
    _post(client, "run_2", user_prompt_submit(session_id=sid, prompt="task"))
    _post(client, "run_2", pre_tool_use(session_id=sid, tool_name="Read", tool_use_id="ta"))
    _post(
        client,
        "run_2",
        post_tool_use(session_id=sid, tool_name="Read", tool_use_id="ta", stdout="contents"),
    )
    _post(
        client,
        "run_2",
        pre_tool_use(
            session_id=sid,
            tool_name="Bash",
            tool_use_id="tb",
            tool_input={"command": "echo hi"},
        ),
    )
    _post(
        client,
        "run_2",
        post_tool_use(session_id=sid, tool_name="Bash", tool_use_id="tb", stdout="hi"),
    )
    _post(client, "run_2", stop(session_id=sid))
    with Session(engine) as session:
        run = session.get(Run, "run_2")
        nodes = session.exec(select(Node).where(Node.run_id == "run_2")).all()
    assert run is not None
    assert run.status == "success"
    assert len(nodes) == 3
    assert {node.type for node in nodes} >= {"prompt", "tool"}
