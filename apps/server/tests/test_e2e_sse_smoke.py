"""End-to-end smoke: post hook events, subscribe to SSE, assert events stream.

Marked ``slow``: endpoint + bus + ``test_sse_publish_from_normalizer`` cover the
same surfaces for PRs. Run this occasionally or in release checks::

    uv run pytest tests/test_e2e_sse_smoke.py -v
    uv run pytest -m slow -v
"""
from __future__ import annotations

import json

import anyio
import httpx
import pytest
from runback_server.db import create_all, engine
from runback_server.models import Node, Run, RunGroup
from runback_server.sse import bus
from sqlmodel import Session, select

from tests.fixtures.events import (
    post_tool_use,
    post_tool_use_failure,
    pre_tool_use,
    todos,
    todowrite_pre,
    user_prompt_submit,
)

pytestmark = pytest.mark.slow


@pytest.fixture(autouse=True)
def fresh_db():
    create_all()
    with Session(engine) as s:
        for row in s.exec(select(Node)).all():
            s.delete(row)
        for row in s.exec(select(RunGroup)).all():
            s.delete(row)
        for row in s.exec(select(Run)).all():
            s.delete(row)
        s.commit()


def _parse_sse(buf: str) -> list[dict]:
    events = []
    buf = buf.replace("\r\n", "\n")
    for block in buf.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        event_name = None
        data_lines: list[str] = []
        for line in block.splitlines():
            if line.startswith(":"):
                continue
            if line.startswith("event:"):
                event_name = line.removeprefix("event:").strip()
            elif line.startswith("data:"):
                data_lines.append(line.removeprefix("data:").strip())
        if event_name and data_lines:
            events.append({"event": event_name, "data": json.loads("\n".join(data_lines))})
    return events


async def _wait_for_subscription(run_id: str) -> None:
    for _ in range(40):
        if bus.subscriber_count(run_id) >= 1:
            return
        await anyio.sleep(0.05)


@pytest.mark.anyio
async def test_full_session_stream(live_server_url: str):
    async with httpx.AsyncClient(base_url=live_server_url) as client:
        async with client.stream("GET", "/api/runs/run_e2e/events", timeout=60.0) as resp:
            assert resp.status_code == 200
            assert resp.headers["content-type"].startswith("text/event-stream")
            sid = "session_e2e"

            async def producer():
                await _wait_for_subscription("run_e2e")
                r = await client.post(
                    "/api/hooks/claude",
                    json=user_prompt_submit(session_id=sid, prompt="task"),
                    headers={"x-runback-run-id": "run_e2e"},
                )
                assert r.status_code == 202
                await client.post(
                    "/api/hooks/claude",
                    json=todowrite_pre(session_id=sid, todos=todos(("Ticket #1: Foo", "pending"))),
                    headers={"x-runback-run-id": "run_e2e"},
                )
                await client.post(
                    "/api/hooks/claude",
                    json=todowrite_pre(
                        session_id=sid, todos=todos(("Ticket #1: Foo", "in_progress"))
                    ),
                    headers={"x-runback-run-id": "run_e2e"},
                )
                await client.post(
                    "/api/hooks/claude",
                    json=pre_tool_use(
                        session_id=sid,
                        tool_name="Read",
                        tool_use_id="t1",
                        tool_input={"file_path": "/tmp/foo"},
                    ),
                    headers={"x-runback-run-id": "run_e2e"},
                )
                await client.post(
                    "/api/hooks/claude",
                    json=post_tool_use(
                        session_id=sid,
                        tool_name="Read",
                        tool_use_id="t1",
                        stdout="hi",
                    ),
                    headers={"x-runback-run-id": "run_e2e"},
                )
                await client.post(
                    "/api/hooks/claude",
                    json=pre_tool_use(
                        session_id=sid,
                        tool_name="Bash",
                        tool_use_id="t2",
                        tool_input={"command": "npm test"},
                    ),
                    headers={"x-runback-run-id": "run_e2e"},
                )
                await client.post(
                    "/api/hooks/claude",
                    json=post_tool_use_failure(
                        session_id=sid,
                        tool_name="Bash",
                        tool_use_id="t2",
                        error="FAIL",
                    ),
                    headers={"x-runback-run-id": "run_e2e"},
                )
                await client.post(
                    "/api/hooks/claude",
                    json=todowrite_pre(
                        session_id=sid, todos=todos(("Ticket #1: Foo", "completed"))
                    ),
                    headers={"x-runback-run-id": "run_e2e"},
                )

            seen: list = []
            async with anyio.create_task_group() as tg:
                tg.start_soon(producer)
                buf = ""
                with anyio.move_on_after(45.0):
                    async for chunk in resp.aiter_text():
                        buf += chunk
                        seen = _parse_sse(buf)
                        kinds = [e["event"] for e in seen]
                        if (
                            kinds.count("node.created") >= 3
                            and kinds.count("node.updated") >= 2
                            and "group.opened" in kinds
                            and "group.closed" in kinds
                            and "edge.created" in kinds
                        ):
                            break

            kinds = [e["event"] for e in seen]
            assert kinds.count("node.created") >= 3, kinds
            assert kinds.count("node.updated") >= 2, kinds
            assert "group.opened" in kinds, kinds
            assert "group.closed" in kinds, kinds
            assert "edge.created" in kinds, kinds

            updates = [e for e in seen if e["event"] == "node.updated"]
            statuses = [u["data"]["payload"]["status"] for u in updates]
            assert "success" in statuses
            assert "failed" in statuses

            with Session(engine) as s:
                run = s.get(Run, "run_e2e")
                groups = s.exec(select(RunGroup)).all()
                nodes = s.exec(select(Node)).all()
            assert run is not None
            assert sum(1 for n in nodes if n.type == "tool") == 2
            assert sum(1 for n in nodes if n.type == "prompt") == 1
            assert any(g.label == "Ticket #1: Foo" and g.status == "success" for g in groups)
