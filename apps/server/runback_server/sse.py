"""In-process SSE pub/sub bus.

Single instance per FastAPI process. Keyed by `run_id` to a set of
`MemoryObjectSendStream` handles. Each `subscribe(run_id)` is an async context
manager that yields a `MemoryObjectReceiveStream` and cleans up on exit.

`publish_*` helpers shape typed `SseEvent` instances (see
`runback_server/schemas/sse_events.py`) and broadcast to all subscribers for the
run. Publishes to a run with no subscribers are no-ops.

Concurrency model: a single asyncio event loop is assumed (FastAPI default).
Sends use `send_nowait` so a slow subscriber does not block the producer; if the
subscriber buffer is full the event is dropped for that subscriber and an
`anyio.WouldBlock` is swallowed (the SSE connection is best-effort, not a queue).
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import anyio
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream

from runback_server.schemas.sse_events import (
    CheckpointCreatedPayload,
    EdgeCreatedPayload,
    GroupClosedPayload,
    GroupOpenedPayload,
    NodeCreatedPayload,
    NodeUpdatedPayload,
    ReplayCreatedPayload,
    SideEffectLoggedPayload,
    _CheckpointCreated,
    _EdgeCreated,
    _GroupClosed,
    _GroupOpened,
    _NodeCreated,
    _NodeUpdated,
    _ReplayCreated,
    _SideEffectLogged,
)

# Buffer size per subscriber. Generous enough that brief UI lag does not lose
# events; small enough that a dead subscriber does not bloat memory.
_SUBSCRIBER_BUFFER = 256


class SseBus:
    """Per-process pub/sub bus.

    Use the module-level `bus` singleton in production code. Constructed
    explicitly only by tests.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[MemoryObjectSendStream[Any]]] = {}

    @asynccontextmanager
    async def subscribe(self, run_id: str) -> AsyncIterator[MemoryObjectReceiveStream[Any]]:
        """Async context manager. Yields a receive-stream; cleans up on exit."""
        send, receive = anyio.create_memory_object_stream(_SUBSCRIBER_BUFFER)
        self._subscribers.setdefault(run_id, []).append(send)
        try:
            yield receive
        finally:
            try:
                self._subscribers.get(run_id, []).remove(send)
            except ValueError:
                pass
            await send.aclose()
            await receive.aclose()
            if run_id in self._subscribers and not self._subscribers[run_id]:
                self._subscribers.pop(run_id, None)

    def subscriber_count(self, run_id: str) -> int:
        return len(self._subscribers.get(run_id, []))

    async def _broadcast(self, run_id: str, event: Any) -> None:
        sinks = list(self._subscribers.get(run_id, []))
        for sink in sinks:
            try:
                sink.send_nowait(event)
            except anyio.WouldBlock:
                continue
            except anyio.BrokenResourceError:
                try:
                    self._subscribers.get(run_id, []).remove(sink)
                except ValueError:
                    pass

    async def publish_node_created(self, run_id: str, payload: NodeCreatedPayload) -> None:
        evt = _NodeCreated(run_id=run_id, type="node.created", payload=payload)
        await self._broadcast(run_id, evt)

    async def publish_node_updated(self, run_id: str, payload: NodeUpdatedPayload) -> None:
        evt = _NodeUpdated(run_id=run_id, type="node.updated", payload=payload)
        await self._broadcast(run_id, evt)

    async def publish_edge_created(self, run_id: str, payload: EdgeCreatedPayload) -> None:
        evt = _EdgeCreated(run_id=run_id, type="edge.created", payload=payload)
        await self._broadcast(run_id, evt)

    async def publish_checkpoint_created(self, run_id: str, payload: CheckpointCreatedPayload) -> None:
        evt = _CheckpointCreated(run_id=run_id, type="checkpoint.created", payload=payload)
        await self._broadcast(run_id, evt)

    async def publish_side_effect_logged(self, run_id: str, payload: SideEffectLoggedPayload) -> None:
        evt = _SideEffectLogged(run_id=run_id, type="side_effect.logged", payload=payload)
        await self._broadcast(run_id, evt)

    async def publish_replay_created(self, run_id: str, payload: ReplayCreatedPayload) -> None:
        evt = _ReplayCreated(run_id=run_id, type="replay.created", payload=payload)
        await self._broadcast(run_id, evt)

    async def publish_group_opened(self, run_id: str, payload: GroupOpenedPayload) -> None:
        evt = _GroupOpened(run_id=run_id, type="group.opened", payload=payload)
        await self._broadcast(run_id, evt)

    async def publish_group_closed(self, run_id: str, payload: GroupClosedPayload) -> None:
        evt = _GroupClosed(run_id=run_id, type="group.closed", payload=payload)
        await self._broadcast(run_id, evt)


bus = SseBus()

__all__ = ["SseBus", "bus"]
