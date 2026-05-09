"""Run, DAG, node, and SSE endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session

from runback_server.classifier import OverrideError, apply_override
from runback_server.db import engine
from runback_server.models import Node, Run

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


class PolicyOverrideRequest(BaseModel):
    recovery_policy: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class PolicyOverrideResponse(BaseModel):
    node_id: str
    recovery_policy: str
    classification_reason: str


@router.post("/{run_id}/nodes/{node_id}/policy", response_model=PolicyOverrideResponse)
def override_node_policy(
    run_id: str,
    node_id: str,
    payload: PolicyOverrideRequest,
) -> PolicyOverrideResponse:
    with Session(engine) as session:
        run = session.get(Run, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"run {run_id!r} not found")

        node = session.get(Node, node_id)
        if node is None or node.run_id != run_id:
            raise HTTPException(
                status_code=404,
                detail=f"node {node_id!r} not found in run {run_id!r}",
            )

        try:
            apply_override(
                session,
                node,
                recovery_policy=payload.recovery_policy,
                reason=payload.reason,
            )
        except OverrideError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        session.commit()
        session.refresh(node)
        return PolicyOverrideResponse(
            node_id=node.id,
            recovery_policy=node.recovery_policy,
            classification_reason=node.classification_reason or "",
        )
