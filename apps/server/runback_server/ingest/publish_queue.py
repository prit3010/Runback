"""Per-request queue for SSE publishes that the synchronous normalizer/reconciler
generates while inside a SQL transaction.

Usage:
    queue = PublishQueue()
    queue.enqueue_node_created(run_id, payload)
    ...
    # After session.commit() succeeds:
    await queue.drain(bus)

The reconciler/groups read a thread-local current queue via
`get_current_publish_queue()`; the hook endpoint sets it via `with publish_scope():`.
This avoids threading the queue through every function signature.
"""
from __future__ import annotations

import contextvars
from collections.abc import Awaitable, Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from runback_server.schemas.sse_events import (
    CheckpointCreatedPayload,
    EdgeCreatedPayload,
    GroupClosedPayload,
    GroupOpenedPayload,
    NodeCreatedPayload,
    NodeUpdatedPayload,
    ReplayCreatedPayload,
    SideEffectLoggedPayload,
)


@dataclass
class _Item:
    method: str
    run_id: str
    payload: Any


@dataclass
class PublishQueue:
    items: list[_Item] = field(default_factory=list)

    def enqueue_node_created(self, run_id: str, payload: NodeCreatedPayload) -> None:
        self.items.append(_Item("publish_node_created", run_id, payload))

    def enqueue_node_updated(self, run_id: str, payload: NodeUpdatedPayload) -> None:
        self.items.append(_Item("publish_node_updated", run_id, payload))

    def enqueue_edge_created(self, run_id: str, payload: EdgeCreatedPayload) -> None:
        self.items.append(_Item("publish_edge_created", run_id, payload))

    def enqueue_checkpoint_created(self, run_id: str, payload: CheckpointCreatedPayload) -> None:
        self.items.append(_Item("publish_checkpoint_created", run_id, payload))

    def enqueue_side_effect_logged(self, run_id: str, payload: SideEffectLoggedPayload) -> None:
        self.items.append(_Item("publish_side_effect_logged", run_id, payload))

    def enqueue_replay_created(self, run_id: str, payload: ReplayCreatedPayload) -> None:
        self.items.append(_Item("publish_replay_created", run_id, payload))

    def enqueue_group_opened(self, run_id: str, payload: GroupOpenedPayload) -> None:
        self.items.append(_Item("publish_group_opened", run_id, payload))

    def enqueue_group_closed(self, run_id: str, payload: GroupClosedPayload) -> None:
        self.items.append(_Item("publish_group_closed", run_id, payload))

    async def drain(self, bus_obj: Any) -> None:
        while self.items:
            item = self.items.pop(0)
            method: Callable[..., Awaitable[None]] = getattr(bus_obj, item.method)
            await method(run_id=item.run_id, payload=item.payload)


_current: contextvars.ContextVar[PublishQueue | None] = contextvars.ContextVar(
    "current_publish_queue",
    default=None,
)


def get_current_publish_queue() -> PublishQueue | None:
    return _current.get()


@contextmanager
def publish_scope():
    queue = PublishQueue()
    token = _current.set(queue)
    try:
        yield queue
    finally:
        _current.reset(token)
