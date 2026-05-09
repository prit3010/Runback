"""Checkpoint entity."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Checkpoint(SQLModel, table=True):
    id: str = Field(primary_key=True)
    run_id: str = Field(foreign_key="run.id", index=True)
    branch_id: str = Field(index=True)
    node_id: str | None = None
    label: str
    backend: str
    git_ref: str | None = None
    git_commit_hash: str | None = None
    patch_path: str | None = None
    workspace_path: str
    diff_summary: str | None = None
    file_hashes_json: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime
