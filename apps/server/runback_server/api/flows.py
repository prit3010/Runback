"""Flow CRUD endpoints. Stubs; full implementation lands in the backend plan."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("")
def list_flows() -> list[dict]:
    raise HTTPException(status_code=501, detail="Not implemented (stub)")


@router.post("", status_code=201)
def create_flow(payload: dict) -> dict:
    raise HTTPException(status_code=501, detail="Not implemented (stub)")


@router.get("/{flow_id}")
def get_flow(flow_id: str) -> dict:
    raise HTTPException(status_code=501, detail="Not implemented (stub)")


@router.post("/{flow_id}/run", status_code=202)
def run_flow(flow_id: str) -> dict:
    raise HTTPException(status_code=501, detail="Not implemented (stub)")
