"""Hook ingest endpoint. Stub; full implementation lands in the backend plan."""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

router = APIRouter()


@router.post("/claude")
def ingest_claude_hook(payload: dict, x_runback_run_id: str = Header(...)) -> dict:
    raise HTTPException(status_code=501, detail="Not implemented (stub)")
