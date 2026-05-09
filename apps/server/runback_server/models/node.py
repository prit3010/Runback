"""Node and Edge entities."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Node(SQLModel, table=True):
    id: str = Field(primary_key=True)
    run_id: str = Field(foreign_key="run.id", index=True)
    branch_id: str = Field(index=True)
    group_id: str | None = Field(default=None, foreign_key="rungroup.id", index=True)
    claude_tool_use_id: str | None = Field(default=None, index=True)
    event_type: str
    type: str
    label: str
    tool_name: str | None = None
    input_json: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    output_json: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    output_preview: str | None = None
    error: str | None = None
    status: str
    recovery_policy: str
    classification_reason: str | None = None
    classification_confidence: float | None = None
    checkpoint_before_id: str | None = None
    checkpoint_after_id: str | None = None
    cache_policy_json: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_ms: int | None = None
    raw_event_path: str | None = None


class Edge(SQLModel, table=True):
    id: str = Field(primary_key=True)
    run_id: str = Field(foreign_key="run.id", index=True)
    branch_id: str = Field(index=True)
    source_node_id: str
    target_node_id: str
    edge_type: str
