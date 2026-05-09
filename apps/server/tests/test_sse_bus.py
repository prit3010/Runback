"""SSE bus pub/sub: subscribers receive published events for their run only."""
from __future__ import annotations

import anyio
import pytest

from runback_server.schemas.sse_events import (
    EdgeCreatedPayload,
    GroupClosedPayload,
    GroupOpenedPayload,
    NodeCreatedPayload,
    NodeUpdatedPayload,
    SideEffectLoggedPayload,
)
from runback_server.sse import SseBus


@pytest.mark.anyio
async def test_subscribe_receives_published_node_created():
    bus = SseBus()
    received: list = []

    async def consumer():
        async with bus.subscribe("run_1") as stream:
            async for evt in stream:
                received.append(evt)
                if len(received) == 1:
                    return

    async with anyio.create_task_group() as tg:
        tg.start_soon(consumer)
        await anyio.sleep(0.02)
        await bus.publish_node_created(
            run_id="run_1",
            payload=NodeCreatedPayload(
                node_id="n1",
                branch_id="b1",
                group_id=None,
                type="tool",
                label="Read foo",
                tool_name="Read",
                recovery_policy="reuse_cached",
                status="running",
            ),
        )

    assert len(received) == 1
    evt = received[0]
    assert evt.type == "node.created"
    assert evt.run_id == "run_1"
    assert evt.payload.node_id == "n1"


@pytest.mark.anyio
async def test_subscribers_isolated_by_run_id():
    bus = SseBus()
    got_run1: list = []
    got_run2: list = []

    async def consume(run_id, sink):
        async with bus.subscribe(run_id) as stream:
            async for evt in stream:
                sink.append(evt)
                return

    async with anyio.create_task_group() as tg:
        tg.start_soon(consume, "run_1", got_run1)
        tg.start_soon(consume, "run_2", got_run2)
        await anyio.sleep(0.02)
        await bus.publish_node_updated(
            run_id="run_1",
            payload=NodeUpdatedPayload(node_id="n1", status="success"),
        )
        await anyio.sleep(0.02)
        await bus.publish_node_updated(
            run_id="run_2",
            payload=NodeUpdatedPayload(node_id="n9", status="failed"),
        )

    assert len(got_run1) == 1 and got_run1[0].payload.node_id == "n1"
    assert len(got_run2) == 1 and got_run2[0].payload.node_id == "n9"


@pytest.mark.anyio
async def test_multiple_subscribers_same_run_each_receive_event():
    bus = SseBus()
    a: list = []
    b: list = []

    async def consume(sink):
        async with bus.subscribe("run_x") as stream:
            async for evt in stream:
                sink.append(evt)
                return

    async with anyio.create_task_group() as tg:
        tg.start_soon(consume, a)
        tg.start_soon(consume, b)
        await anyio.sleep(0.02)
        await bus.publish_edge_created(
            run_id="run_x",
            payload=EdgeCreatedPayload(
                edge_id="e1",
                branch_id="b1",
                source_node_id="n1",
                target_node_id="n2",
                edge_type="sequence",
            ),
        )

    assert len(a) == 1 and len(b) == 1
    assert a[0].payload.edge_id == "e1"
    assert b[0].payload.edge_id == "e1"


@pytest.mark.anyio
async def test_publish_with_no_subscribers_is_noop():
    bus = SseBus()
    await bus.publish_group_opened(
        run_id="run_empty",
        payload=GroupOpenedPayload(
            group_id="g1",
            parent_group_id=None,
            label="Ticket #1",
            kind="ticket",
        ),
    )


@pytest.mark.anyio
async def test_unsubscribe_on_context_exit_removes_subscriber():
    bus = SseBus()
    async with bus.subscribe("run_1") as _stream:
        assert bus.subscriber_count("run_1") == 1
    assert bus.subscriber_count("run_1") == 0


@pytest.mark.anyio
async def test_publish_group_closed_and_side_effect_logged():
    bus = SseBus()
    received: list = []

    async def consumer():
        async with bus.subscribe("run_1") as stream:
            async for evt in stream:
                received.append(evt)
                if len(received) == 2:
                    return

    async with anyio.create_task_group() as tg:
        tg.start_soon(consumer)
        await anyio.sleep(0.02)
        await bus.publish_group_closed(
            run_id="run_1",
            payload=GroupClosedPayload(group_id="g1", status="success"),
        )
        await bus.publish_side_effect_logged(
            run_id="run_1",
            payload=SideEffectLoggedPayload(
                node_id="n1",
                kind="gh_pr_create",
                idempotency_key="gh:pr:o/r:fix/x",
                status="executed",
                external_ref="https://github.com/o/r/pull/1",
            ),
        )

    assert {e.type for e in received} == {"group.closed", "side_effect.logged"}
