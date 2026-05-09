"""Hook ingest endpoint: dedupe, archive, normalize, broadcast SSE."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import ValidationError

from runback_server.config import get_settings
from runback_server.ingest.archive import (
    EventArchive,
    compute_event_key,
    is_duplicate_key,
    record_event_key,
)
from runback_server.ingest.normalizer import Normalizer
from runback_server.ingest.publish_queue import publish_scope
from runback_server.schemas.hook_events import parse_hook_event
from runback_server.sse import bus

router = APIRouter()


@router.post("/claude", status_code=status.HTTP_202_ACCEPTED)
async def ingest_claude_hook(
    payload: dict[str, Any],
    x_runback_run_id: str = Header(..., alias="x-runback-run-id"),
    x_runback_branch_id: str | None = Header(default=None, alias="x-runback-branch-id"),
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="payload must be a JSON object")

    try:
        parse_hook_event(payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"invalid hook event: {exc.errors()[:3]}",
        ) from exc

    settings = get_settings()
    archive = EventArchive(run_id=x_runback_run_id, root=settings.runtime_root)
    event_key = compute_event_key(x_runback_run_id, payload)

    if is_duplicate_key(archive, event_key):
        return {"accepted": True, "run_id": x_runback_run_id, "duplicate": True}

    archive.append(payload)

    with publish_scope() as queue:
        Normalizer(runtime_root=settings.runtime_root).handle(
            run_id=x_runback_run_id,
            payload=payload,
            branch_id_override=x_runback_branch_id or None,
        )
        await queue.drain(bus)

    record_event_key(archive, event_key)
    return {"accepted": True, "run_id": x_runback_run_id, "duplicate": False}
