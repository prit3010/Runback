"""Artifact and NodeArtifactEdge entities."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Artifact(SQLModel, table=True):
    id: str = Field(primary_key=True)
    run_id: str = Field(foreign_key="run.id", index=True)
    node_id: str | None = None
    produced_by_node_id: str | None = None
    type: str
    path: str | None = None
    source_url: str | None = None
    description: str | None = None
    content_preview: str | None = None
    content_hash: str | None = None
    size_bytes: int | None = None
    cache_policy_json: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime


class NodeArtifactEdge(SQLModel, table=True):
    id: str = Field(primary_key=True)
    run_id: str = Field(foreign_key="run.id", index=True)
    node_id: str = Field(foreign_key="node.id", index=True)
    artifact_id: str = Field(foreign_key="artifact.id", index=True)
    direction: str
    required: bool = True
    created_at: datetime
