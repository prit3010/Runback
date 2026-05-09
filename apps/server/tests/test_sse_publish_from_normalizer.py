"""Posting hook events through `POST /api/hooks/claude` causes SSE publishes
on the in-process bus, observable by an active subscriber.
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
    pre_tool_use,
    todos,
    todowrite_pre,
    user_prompt_submit,
)


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


def _parse_sse_chunk(chunk: str) -> list[dict]:
    events = []
    chunk = chunk.replace("\r\n", "\n")
    for block in chunk.split("\n\n"):
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


async def _post(client: httpx.AsyncClient, run_id: str, payload: dict) -> httpx.Response:
    return await client.post(
        "/api/hooks/claude",
        json=payload,
        headers={"x-runback-run-id": run_id},
    )


async def _wait_for_subscription(run_id: str) -> None:
    for _ in range(40):
        if bus.subscriber_count(run_id) >= 1:
            return
        await anyio.sleep(0.05)


@pytest.mark.anyio
async def test_user_prompt_emits_node_created(live_server_url: str):
    async with httpx.AsyncClient(base_url=live_server_url) as client:
        async with client.stream("GET", "/api/runs/run_pub/events", timeout=30.0) as resp:
            assert resp.status_code == 200

            async def producer():
                await _wait_for_subscription("run_pub")
                r = await _post(client, "run_pub", user_prompt_submit(prompt="hi"))
                assert r.status_code == 202

            seen: list = []
            async with anyio.create_task_group() as tg:
                tg.start_soon(producer)
                buf = ""
                with anyio.move_on_after(15.0):
                    async for chunk in resp.aiter_text():
                        buf += chunk
                        seen = _parse_sse_chunk(buf)
                        if any(e["event"] == "node.created" for e in seen):
                            break

            kinds = [e["event"] for e in seen]
            assert "node.created" in kinds


@pytest.mark.anyio
async def test_tool_pre_then_post_emits_node_created_then_node_updated(live_server_url: str):
    async with httpx.AsyncClient(base_url=live_server_url) as client:
        async with client.stream("GET", "/api/runs/run_pp/events", timeout=30.0) as resp:
            assert resp.status_code == 200
            sid = "s1"

            async def producer():
                await _wait_for_subscription("run_pp")
                await _post(client, "run_pp", user_prompt_submit(session_id=sid, prompt="x"))
                await _post(
                    client,
                    "run_pp",
                    pre_tool_use(
                        session_id=sid,
                        tool_name="Read",
                        tool_use_id="t1",
                        tool_input={"file_path": "/tmp/foo"},
                    ),
                )
                await _post(
                    client,
                    "run_pp",
                    post_tool_use(
                        session_id=sid,
                        tool_name="Read",
                        tool_use_id="t1",
                        stdout="contents",
                    ),
                )

            seen: list = []
            async with anyio.create_task_group() as tg:
                tg.start_soon(producer)
                buf = ""
                with anyio.move_on_after(15.0):
                    async for chunk in resp.aiter_text():
                        buf += chunk
                        seen = _parse_sse_chunk(buf)
                        kinds = [e["event"] for e in seen]
                        if kinds.count("node.created") >= 2 and kinds.count("node.updated") >= 1:
                            break

            kinds = [e["event"] for e in seen]
            assert kinds.count("node.created") >= 2
            assert kinds.count("node.updated") >= 1


@pytest.mark.anyio
async def test_todowrite_transitions_emit_group_opened_and_closed(live_server_url: str):
    async with httpx.AsyncClient(base_url=live_server_url) as client:
        async with client.stream("GET", "/api/runs/run_grp/events", timeout=30.0) as resp:
            assert resp.status_code == 200
            sid = "s1"

            async def producer():
                await _wait_for_subscription("run_grp")
                await _post(client, "run_grp", user_prompt_submit(session_id=sid, prompt="x"))
                await _post(
                    client,
                    "run_grp",
                    todowrite_pre(session_id=sid, todos=todos(("Ticket #1: Foo", "pending"))),
                )
                await _post(
                    client,
                    "run_grp",
                    todowrite_pre(session_id=sid, todos=todos(("Ticket #1: Foo", "in_progress"))),
                )
                await _post(
                    client,
                    "run_grp",
                    todowrite_pre(session_id=sid, todos=todos(("Ticket #1: Foo", "completed"))),
                )

            seen: list = []
            async with anyio.create_task_group() as tg:
                tg.start_soon(producer)
                buf = ""
                with anyio.move_on_after(15.0):
                    async for chunk in resp.aiter_text():
                        buf += chunk
                        seen = _parse_sse_chunk(buf)
                        kinds = [e["event"] for e in seen]
                        if "group.opened" in kinds and "group.closed" in kinds:
                            break

            kinds = [e["event"] for e in seen]
            assert "group.opened" in kinds
            assert "group.closed" in kinds


@pytest.mark.anyio
async def test_sequence_edge_published_when_two_consecutive_tool_nodes(live_server_url: str):
    async with httpx.AsyncClient(base_url=live_server_url) as client:
        async with client.stream("GET", "/api/runs/run_edge/events", timeout=30.0) as resp:
            assert resp.status_code == 200
            sid = "s1"

            async def producer():
                await _wait_for_subscription("run_edge")
                await _post(client, "run_edge", user_prompt_submit(session_id=sid, prompt="x"))
                await _post(
                    client,
                    "run_edge",
                    pre_tool_use(session_id=sid, tool_name="Read", tool_use_id="t1"),
                )
                await _post(
                    client,
                    "run_edge",
                    post_tool_use(session_id=sid, tool_name="Read", tool_use_id="t1", stdout="ok"),
                )
                await _post(
                    client,
                    "run_edge",
                    pre_tool_use(session_id=sid, tool_name="Grep", tool_use_id="t2"),
                )

            seen: list = []
            async with anyio.create_task_group() as tg:
                tg.start_soon(producer)
                buf = ""
                with anyio.move_on_after(15.0):
                    async for chunk in resp.aiter_text():
                        buf += chunk
                        seen = _parse_sse_chunk(buf)
                        if any(e["event"] == "edge.created" for e in seen):
                            break

            kinds = [e["event"] for e in seen]
            assert "edge.created" in kinds
