"""Raw event archive and idempotency deduplication."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlmodel import Field, Session, SQLModel

from runback_server.db import engine


class EventDedup(SQLModel, table=True):
    """Idempotency key store for accepted hook events."""

    __tablename__ = "event_dedup"

    event_key: str = Field(primary_key=True)


def _ensure_table() -> None:
    SQLModel.metadata.create_all(engine, tables=[EventDedup.__table__])


def compute_event_key(run_id: str, payload: dict[str, Any]) -> str:
    """Compute a stable idempotency key from run id and event content."""
    event_name = payload.get("hook_event_name", "") or ""
    tool_use_id = payload.get("tool_use_id", "") or ""
    session_id = payload.get("session_id", "") or ""
    content = json.dumps(payload, sort_keys=True, default=str).encode()
    content_hash = hashlib.sha256(content).hexdigest()[:16]
    raw_key = "|".join([run_id, event_name, tool_use_id, session_id, content_hash])
    return hashlib.sha256(raw_key.encode()).hexdigest()


@dataclass
class EventArchive:
    """Per-run JSONL archive. Cheap to instantiate; no open handle is retained."""

    run_id: str
    root: Path

    @property
    def jsonl_path(self) -> Path:
        return self.root / "runs" / self.run_id / "events.jsonl"

    def append(self, payload: dict[str, Any]) -> None:
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        with self.jsonl_path.open("a") as f:
            f.write(json.dumps(payload, default=str))
            f.write("\n")


def is_duplicate_key(_archive: EventArchive, key: str) -> bool:
    """Return true when the idempotency key has already been accepted."""
    _ensure_table()
    with Session(engine) as session:
        return session.get(EventDedup, key) is not None


def record_event_key(_archive: EventArchive, key: str) -> None:
    """Record an accepted idempotency key. Re-recording is a no-op."""
    _ensure_table()
    with Session(engine) as session:
        if session.get(EventDedup, key) is None:
            session.add(EventDedup(event_key=key))
            session.commit()
