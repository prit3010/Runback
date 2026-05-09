"""Runner entity."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Runner(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    machine_id: str | None = None
    status: str
    last_heartbeat_at: datetime | None = None
    current_run_id: str | None = None
    available_repos_json: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    claude_code_available: bool = True
    version: str
    created_at: datetime
