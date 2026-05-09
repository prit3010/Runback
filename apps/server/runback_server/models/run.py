"""Run and RunGroup entities."""
from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


class Run(SQLModel, table=True):
    id: str = Field(primary_key=True)
    flow_id: str | None = Field(default=None, foreign_key="flow.id", index=True)
    flow_version_id: str | None = None
    runner_id: str | None = None
    run_kind: str = "ad_hoc"
    status: str
    original_prompt: str
    repo_path: str
    workspace_path: str | None = None
    root_branch_id: str
    current_branch_id: str
    failure_node_id: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime


class RunGroup(SQLModel, table=True):
    id: str = Field(primary_key=True)
    run_id: str = Field(foreign_key="run.id", index=True)
    parent_group_id: str | None = Field(default=None, foreign_key="rungroup.id")
    label: str
    kind: str
    status: str
    started_at: datetime | None = None
    ended_at: datetime | None = None
