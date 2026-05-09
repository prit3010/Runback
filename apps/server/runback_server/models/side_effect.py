"""SideEffectLog entity."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class SideEffectLog(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("kind", "idempotency_key", name="uq_kind_key"),)

    id: int | None = Field(default=None, primary_key=True)
    run_id: str = Field(foreign_key="run.id", index=True)
    branch_id: str = Field(index=True)
    node_id: str = Field(index=True)
    kind: str
    idempotency_key: str
    external_ref: str | None = None
    status: str = "pending_approval"
    payload_preview: str | None = None
    executed_at: datetime | None = None
