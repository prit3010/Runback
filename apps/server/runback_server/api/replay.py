"""Replay endpoints. Stubs; full implementation lands in the backend plan."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/runs/{run_id}/replay", status_code=202)
def replay_run(run_id: str, payload: dict) -> dict:
    raise HTTPException(status_code=501, detail="Not implemented (stub)")


@router.get("/runs/{run_id}/replay/recommendation")
def get_replay_recommendation(run_id: str, node_id: str) -> dict:
    raise HTTPException(status_code=501, detail="Not implemented (stub)")
