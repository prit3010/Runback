"""SSE event payload schemas. Mirror these in apps/web/lib/sse-types.ts."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, TypeAdapter


class NodeCreatedPayload(BaseModel):
    node_id: str
    branch_id: str
    group_id: str | None
    type: str
    label: str
    tool_name: str | None
    recovery_policy: str
    status: str


class NodeUpdatedPayload(BaseModel):
    node_id: str
    status: str | None = None
    output_preview: str | None = None
    error: str | None = None
    duration_ms: int | None = None
    recovery_policy: str | None = None
    classification_reason: str | None = None


class EdgeCreatedPayload(BaseModel):
    edge_id: str
    branch_id: str
    source_node_id: str
    target_node_id: str
    edge_type: str


class CheckpointCreatedPayload(BaseModel):
    checkpoint_id: str
    branch_id: str
    label: str
    git_ref: str | None = None
    node_id: str | None = None


class SideEffectLoggedPayload(BaseModel):
    node_id: str
    kind: str
    idempotency_key: str
    status: str
    external_ref: str | None = None


class ReplayCreatedPayload(BaseModel):
    replay_id: str
    parent_branch_id: str
    new_branch_id: str
    source_node_id: str
    source_checkpoint_id: str


class GroupOpenedPayload(BaseModel):
    group_id: str
    parent_group_id: str | None
    label: str
    kind: str


class GroupClosedPayload(BaseModel):
    group_id: str
    status: str


class _Base(BaseModel):
    run_id: str
    ts: datetime = Field(default_factory=lambda: datetime.now(UTC))


class _NodeCreated(_Base):
    type: Literal["node.created"]
    payload: NodeCreatedPayload


class _NodeUpdated(_Base):
    type: Literal["node.updated"]
    payload: NodeUpdatedPayload


class _EdgeCreated(_Base):
    type: Literal["edge.created"]
    payload: EdgeCreatedPayload


class _CheckpointCreated(_Base):
    type: Literal["checkpoint.created"]
    payload: CheckpointCreatedPayload


class _SideEffectLogged(_Base):
    type: Literal["side_effect.logged"]
    payload: SideEffectLoggedPayload


class _ReplayCreated(_Base):
    type: Literal["replay.created"]
    payload: ReplayCreatedPayload


class _GroupOpened(_Base):
    type: Literal["group.opened"]
    payload: GroupOpenedPayload


class _GroupClosed(_Base):
    type: Literal["group.closed"]
    payload: GroupClosedPayload


SseEvent = TypeAdapter(
    Annotated[
        _NodeCreated
        | _NodeUpdated
        | _EdgeCreated
        | _CheckpointCreated
        | _SideEffectLogged
        | _ReplayCreated
        | _GroupOpened
        | _GroupClosed,
        Field(discriminator="type"),
    ]
)
