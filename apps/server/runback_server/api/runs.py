"""Run, DAG, node, and SSE endpoints. Stubs; full implementation lands later."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("")
def list_runs() -> list[dict]:
    raise HTTPException(status_code=501, detail="Not implemented (stub)")


@router.get("/{run_id}")
def get_run(run_id: str) -> dict:
    raise HTTPException(status_code=501, detail="Not implemented (stub)")


@router.get("/{run_id}/dag")
def get_run_dag(run_id: str) -> dict:
    raise HTTPException(status_code=501, detail="Not implemented (stub)")


@router.get("/{run_id}/events")
def stream_run_events(run_id: str) -> dict:
    raise HTTPException(status_code=501, detail="Not implemented (stub)")


@router.get("/{run_id}/nodes/{node_id}")
def get_node(run_id: str, node_id: str) -> dict:
    raise HTTPException(status_code=501, detail="Not implemented (stub)")


@router.post("/{run_id}/nodes/{node_id}/policy")
def override_node_policy(run_id: str, node_id: str, payload: dict) -> dict:
    raise HTTPException(status_code=501, detail="Not implemented (stub)")
