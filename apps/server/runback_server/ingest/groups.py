"""TodoWrite to RunGroup boundary detection."""
from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from sqlmodel import Field, Session, SQLModel, select

from runback_server.ingest.ids import group_id
from runback_server.models import RunGroup
from runback_server.schemas.hook_events import HookEvent

_TICKET_RE = re.compile(r"^Ticket #\d+:", re.IGNORECASE)


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class TodoState(SQLModel, table=True):
    """Last known TodoWrite status per run and todo content."""

    __tablename__ = "todo_state"

    run_id: str = Field(primary_key=True)
    content: str = Field(primary_key=True)
    last_status: str
    open_group_id: str | None = None


def _detect_kind(content: str) -> str:
    if _TICKET_RE.match(content):
        return "ticket"
    return "phase"


def apply_todowrite(session: Session, run_id: str, evt: HookEvent) -> None:
    """Process a TodoWrite PreToolUse payload and emit RunGroup transitions."""
    todos: list[dict[str, Any]] = (evt.tool_input or {}).get("todos", []) or []
    for todo in todos:
        content = (todo.get("content") or "").strip()
        new_status = (todo.get("status") or "").strip()
        if not content or not new_status:
            continue

        prev = session.get(TodoState, (run_id, content))
        prev_status = prev.last_status if prev else "pending"

        if prev_status != "in_progress" and new_status == "in_progress":
            gid = group_id()
            session.add(
                RunGroup(
                    id=gid,
                    run_id=run_id,
                    parent_group_id=None,
                    label=content,
                    kind=_detect_kind(content),
                    status="running",
                    started_at=_now(),
                )
            )
            if prev is None:
                session.add(
                    TodoState(
                        run_id=run_id,
                        content=content,
                        last_status=new_status,
                        open_group_id=gid,
                    )
                )
            else:
                prev.last_status = new_status
                prev.open_group_id = gid
            continue

        if prev_status == "in_progress" and new_status in {"completed", "cancelled"}:
            gid = prev.open_group_id if prev else None
            if gid:
                group = session.get(RunGroup, gid)
                if group is not None and group.ended_at is None:
                    group.status = "success" if new_status == "completed" else "failed"
                    group.ended_at = _now()
            if prev:
                prev.last_status = new_status
                prev.open_group_id = None
            continue

        if prev is None:
            session.add(TodoState(run_id=run_id, content=content, last_status=new_status))
        else:
            prev.last_status = new_status


def current_open_group_id(session: Session, run_id: str) -> str | None:
    """Return the most recently opened group that has not been closed."""
    rows = session.exec(
        select(RunGroup)
        .where(RunGroup.run_id == run_id, RunGroup.ended_at.is_(None))  # type: ignore[union-attr]
        .order_by(RunGroup.started_at.desc())  # type: ignore[arg-type]
    ).all()
    return rows[0].id if rows else None
