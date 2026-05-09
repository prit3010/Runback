"""HTTP-level SSE endpoint tests over real localhost streaming."""
from __future__ import annotations

import json

import anyio
import httpx
import pytest
from runback_server.sse import bus

from tests.fixtures.events import post_tool_use, pre_tool_use, user_prompt_submit


def _parse_sse_chunk(chunk: str) -> list[dict]:
    """Return a list of {event, data} dicts from a raw SSE chunk."""
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


async def _wait_for_subscription(run_id: str) -> None:
    for _ in range(40):
        if bus.subscriber_count(run_id) >= 1:
            return
        await anyio.sleep(0.05)


async def _post(client: httpx.AsyncClient, run_id: str, payload: dict) -> httpx.Response:
    return await client.post(
        "/api/hooks/claude",
        json=payload,
        headers={"x-runback-run-id": run_id},
    )


@pytest.mark.anyio
async def test_sse_endpoint_streams_published_events(live_server_url: str):
    async with httpx.AsyncClient(base_url=live_server_url) as client:
        async with client.stream("GET", "/api/runs/run_sse_1/events", timeout=30.0) as resp:
            assert resp.status_code == 200
            assert resp.headers["content-type"].startswith("text/event-stream")

            async def producer():
                await _wait_for_subscription("run_sse_1")
                sid = "sse_endpoint_1"
                assert (
                    await _post(client, "run_sse_1", user_prompt_submit(session_id=sid, prompt="x"))
                ).status_code == 202
                assert (
                    await _post(
                        client,
                        "run_sse_1",
                        pre_tool_use(session_id=sid, tool_name="Read", tool_use_id="t1"),
                    )
                ).status_code == 202
                assert (
                    await _post(
                        client,
                        "run_sse_1",
                        post_tool_use(
                            session_id=sid,
                            tool_name="Read",
                            tool_use_id="t1",
                            stdout="ok",
                        ),
                    )
                ).status_code == 202

            collected_events: list = []
            async with anyio.create_task_group() as tg:
                tg.start_soon(producer)

                buf = ""
                with anyio.move_on_after(15.0):
                    async for chunk in resp.aiter_text():
                        buf += chunk
                        events = _parse_sse_chunk(buf)
                        kinds = [e["event"] for e in events]
                        if "node.created" in kinds and "node.updated" in kinds:
                            collected_events = events
                            break

            kinds = [e["event"] for e in collected_events]
            assert "node.created" in kinds
            assert "node.updated" in kinds
            payload_node_ids = {
                e["data"]["payload"]["node_id"]
                for e in collected_events
                if e["event"] in {"node.created", "node.updated"}
            }
            assert any(node_id.startswith("node_") for node_id in payload_node_ids)


@pytest.mark.anyio
async def test_sse_endpoint_filters_to_requested_run_id(live_server_url: str):
    async with httpx.AsyncClient(base_url=live_server_url) as client:
        async with client.stream("GET", "/api/runs/run_target/events", timeout=30.0) as resp:
            assert resp.status_code == 200

            async def producer():
                await _wait_for_subscription("run_target")
                await _post(
                    client,
                    "run_other",
                    user_prompt_submit(session_id="other", prompt="should not show"),
                )
                await _post(
                    client,
                    "run_target",
                    user_prompt_submit(session_id="target", prompt="should show"),
                )

            seen: list = []
            async with anyio.create_task_group() as tg:
                tg.start_soon(producer)
                buf = ""
                with anyio.move_on_after(15.0):
                    async for chunk in resp.aiter_text():
                        buf += chunk
                        events = _parse_sse_chunk(buf)
                        if any(e["event"] == "node.created" for e in events):
                            seen = events
                            break

            prompts = {
                e["data"]["payload"]["label"] for e in seen if e["event"] == "node.created"
            }
            assert "Prompt: should show" in prompts
            assert "Prompt: should not show" not in prompts


@pytest.mark.anyio
async def test_sse_endpoint_returns_text_event_stream_content_type(live_server_url: str):
    async with httpx.AsyncClient(base_url=live_server_url) as client:
        async with client.stream("GET", "/api/runs/run_ct/events", timeout=30.0) as resp:
            assert resp.status_code == 200
            assert resp.headers["content-type"].startswith("text/event-stream")
