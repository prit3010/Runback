"""ReplayAttempt entity."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class ReplayAttempt(SQLModel, table=True):
    id: str = Field(primary_key=True)
    run_id: str = Field(foreign_key="run.id", index=True)
    source_node_id: str
    source_checkpoint_id: str
    parent_branch_id: str
    new_branch_id: str = Field(index=True)
    resume_prompt: str
    user_context: str | None = None
    generated_context: str | None = None
    status: str
    recommendation_json: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime
    started_at: datetime | None = None
    ended_at: datetime | None = None
