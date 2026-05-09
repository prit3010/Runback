"""Runner endpoints. Stubs; full implementation lands in the backend plan."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("")
def list_runners() -> list[dict]:
    raise HTTPException(status_code=501, detail="Not implemented (stub)")


@router.post("/heartbeat")
def runner_heartbeat(payload: dict) -> dict:
    raise HTTPException(status_code=501, detail="Not implemented (stub)")
