"""Runner heartbeat + listing endpoints."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlmodel import Session, select

from runback_server.db import engine
from runback_server.models import Runner

router = APIRouter()


def _now() -> datetime:
    return datetime.now(timezone.utc)


class RunnerHeartbeat(BaseModel):
    runner_id: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    current_run_id: str | None = None
    version: str = Field(..., min_length=1)
    claude_code_available: bool


def _serialize_runner(r: Runner) -> dict[str, Any]:
    return {
        "id": r.id,
        "name": r.name,
        "machine_id": r.machine_id,
        "status": r.status,
        "last_heartbeat_at": r.last_heartbeat_at.isoformat() if r.last_heartbeat_at else None,
        "current_run_id": r.current_run_id,
        "claude_code_available": r.claude_code_available,
        "version": r.version,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@router.get("")
def list_runners() -> list[dict[str, Any]]:
    with Session(engine) as session:
        rows = session.exec(
            select(Runner).order_by(
                desc(Runner.last_heartbeat_at),
                desc(Runner.created_at),
            )
        ).all()
        return [_serialize_runner(r) for r in rows]


@router.post("/heartbeat", status_code=status.HTTP_200_OK)
def runner_heartbeat(body: RunnerHeartbeat) -> dict[str, Any]:
    now = _now()
    with Session(engine) as session:
        existing = session.get(Runner, body.runner_id)
        if existing is None:
            runner = Runner(
                id=body.runner_id,
                name=body.runner_id,
                status=body.status,
                last_heartbeat_at=now,
                current_run_id=body.current_run_id,
                claude_code_available=body.claude_code_available,
                version=body.version,
                created_at=now,
            )
            session.add(runner)
            session.commit()
            session.refresh(runner)
            return _serialize_runner(runner)
        existing.status = body.status
        existing.last_heartbeat_at = now
        existing.current_run_id = body.current_run_id
        existing.version = body.version
        existing.claude_code_available = body.claude_code_available
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return _serialize_runner(existing)
