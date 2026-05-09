"""Flow and FlowVersion entities."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Flow(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    description: str | None = None
    repo_path: str
    agent: str = "claude_code"
    active_version_id: str
    schedule: str | None = None
    enabled: bool = True
    created_at: datetime
    updated_at: datetime


class FlowVersion(SQLModel, table=True):
    id: str = Field(primary_key=True)
    flow_id: str = Field(foreign_key="flow.id", index=True)
    version_number: int
    prompt: str
    replay_mode: str
    side_effect_policy: str
    cache_policy_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime
