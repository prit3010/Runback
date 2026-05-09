"""Flow CRUD endpoints + flow-run trigger."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from runback_server.db import engine
from runback_server.ingest.ids import branch_id, new_id, run_id as new_run_id
from runback_server.models import Flow, FlowVersion, Run

router = APIRouter()


def _now() -> datetime:
    return datetime.now(timezone.utc)


class FlowCreate(BaseModel):
    """POST /api/flows body."""

    name: str = Field(..., min_length=1)
    description: str | None = None
    repo_path: str = Field(..., min_length=1)
    prompt: str = Field(..., min_length=1)
    schedule: str | None = None
    replay_mode: str = "manual"
    side_effect_policy: str = "label_only"


def _serialize_flow(f: Flow) -> dict[str, Any]:
    return {
        "id": f.id,
        "name": f.name,
        "description": f.description,
        "repo_path": f.repo_path,
        "agent": f.agent,
        "active_version_id": f.active_version_id,
        "schedule": f.schedule,
        "enabled": f.enabled,
        "created_at": f.created_at.isoformat() if f.created_at else None,
        "updated_at": f.updated_at.isoformat() if f.updated_at else None,
    }


def _serialize_run(r: Run) -> dict[str, Any]:
    return {
        "id": r.id,
        "flow_id": r.flow_id,
        "flow_version_id": r.flow_version_id,
        "runner_id": r.runner_id,
        "run_kind": r.run_kind,
        "status": r.status,
        "original_prompt": r.original_prompt,
        "repo_path": r.repo_path,
        "workspace_path": r.workspace_path,
        "root_branch_id": r.root_branch_id,
        "current_branch_id": r.current_branch_id,
        "failure_node_id": r.failure_node_id,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "ended_at": r.ended_at.isoformat() if r.ended_at else None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@router.get("")
def list_flows() -> list[dict[str, Any]]:
    with Session(engine) as session:
        rows = session.exec(
            select(Flow).order_by(Flow.created_at.desc())  # type: ignore[arg-type]
        ).all()
        return [_serialize_flow(r) for r in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_flow(body: FlowCreate) -> dict[str, Any]:
    fid = new_id("flow")
    fvid = new_id("fv")
    now = _now()
    with Session(engine) as session:
        flow = Flow(
            id=fid,
            name=body.name,
            description=body.description,
            repo_path=body.repo_path,
            agent="claude_code",
            active_version_id=fvid,
            schedule=body.schedule,
            enabled=True,
            created_at=now,
            updated_at=now,
        )
        version = FlowVersion(
            id=fvid,
            flow_id=fid,
            version_number=1,
            prompt=body.prompt,
            replay_mode=body.replay_mode,
            side_effect_policy=body.side_effect_policy,
            cache_policy_json={},
            created_at=now,
        )
        session.add(flow)
        session.add(version)
        session.commit()
        session.refresh(flow)
        return _serialize_flow(flow)


@router.get("/{flow_id}")
def get_flow(flow_id: str) -> dict[str, Any]:
    with Session(engine) as session:
        f = session.get(Flow, flow_id)
        if f is None:
            raise HTTPException(status_code=404, detail=f"flow not found: {flow_id}")
        return _serialize_flow(f)


@router.post("/{flow_id}/run", status_code=status.HTTP_202_ACCEPTED)
def run_flow(flow_id: str) -> dict[str, Any]:
    now = _now()
    with Session(engine) as session:
        flow = session.get(Flow, flow_id)
        if flow is None:
            raise HTTPException(status_code=404, detail=f"flow not found: {flow_id}")
        version = session.get(FlowVersion, flow.active_version_id)
        if version is None:
            raise HTTPException(
                status_code=500,
                detail=f"flow {flow_id} references missing active version {flow.active_version_id}",
            )
        b = branch_id()
        run = Run(
            id=new_run_id(),
            flow_id=flow.id,
            flow_version_id=version.id,
            run_kind="registered_flow",
            status="queued",
            original_prompt=version.prompt,
            repo_path=flow.repo_path,
            root_branch_id=b,
            current_branch_id=b,
            created_at=now,
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        return _serialize_run(run)
