"""Run + DAG + SSE + node detail endpoints."""
from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from sse_starlette.sse import EventSourceResponse

from runback_server.classifier import OverrideError, apply_override
from runback_server.db import engine
from runback_server.models import (
    Artifact,
    Checkpoint,
    Edge,
    Node,
    NodeArtifactEdge,
    Run,
    RunGroup,
    SideEffectLog,
)
from runback_server.sse import bus

router = APIRouter()


@router.get("/{run_id}/events")
async def stream_run_events(run_id: str, request: Request) -> EventSourceResponse:
    """Stream live DAG events for a run as text/event-stream."""

    async def event_generator() -> AsyncIterator[dict]:
        async with bus.subscribe(run_id) as stream:
            try:
                async for evt in stream:
                    if await request.is_disconnected():
                        return
                    yield {
                        "event": evt.type,
                        "data": evt.model_dump_json(),
                    }
            except Exception:  # noqa: BLE001
                return

    return EventSourceResponse(event_generator(), ping=15)


def _serialize_run(run: Run) -> dict:
    return {
        "id": run.id,
        "flow_id": run.flow_id,
        "flow_version_id": run.flow_version_id,
        "runner_id": run.runner_id,
        "run_kind": run.run_kind,
        "status": run.status,
        "original_prompt": run.original_prompt,
        "repo_path": run.repo_path,
        "workspace_path": run.workspace_path,
        "root_branch_id": run.root_branch_id,
        "current_branch_id": run.current_branch_id,
        "failure_node_id": run.failure_node_id,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "ended_at": run.ended_at.isoformat() if run.ended_at else None,
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }


def _serialize_node_summary(node: Node) -> dict:
    return {
        "id": node.id,
        "run_id": node.run_id,
        "branch_id": node.branch_id,
        "group_id": node.group_id,
        "type": node.type,
        "label": node.label,
        "tool_name": node.tool_name,
        "status": node.status,
        "recovery_policy": node.recovery_policy,
        "started_at": node.started_at.isoformat() if node.started_at else None,
        "ended_at": node.ended_at.isoformat() if node.ended_at else None,
        "duration_ms": node.duration_ms,
        "output_preview": node.output_preview,
        "error": node.error,
    }


def _serialize_edge(edge: Edge) -> dict:
    return {
        "id": edge.id,
        "run_id": edge.run_id,
        "branch_id": edge.branch_id,
        "source_node_id": edge.source_node_id,
        "target_node_id": edge.target_node_id,
        "edge_type": edge.edge_type,
    }


def _serialize_checkpoint(cp: Checkpoint) -> dict:
    return {
        "id": cp.id,
        "run_id": cp.run_id,
        "branch_id": cp.branch_id,
        "node_id": cp.node_id,
        "label": cp.label,
        "backend": cp.backend,
        "git_ref": cp.git_ref,
        "git_commit_hash": cp.git_commit_hash,
        "workspace_path": cp.workspace_path,
        "diff_summary": cp.diff_summary,
        "created_at": cp.created_at.isoformat() if cp.created_at else None,
    }


def _serialize_group(g: RunGroup) -> dict:
    return {
        "id": g.id,
        "run_id": g.run_id,
        "parent_group_id": g.parent_group_id,
        "label": g.label,
        "kind": g.kind,
        "status": g.status,
        "started_at": g.started_at.isoformat() if g.started_at else None,
        "ended_at": g.ended_at.isoformat() if g.ended_at else None,
    }


def _serialize_side_effect(se: SideEffectLog) -> dict:
    return {
        "id": se.id,
        "run_id": se.run_id,
        "branch_id": se.branch_id,
        "node_id": se.node_id,
        "kind": se.kind,
        "idempotency_key": se.idempotency_key,
        "external_ref": se.external_ref,
        "status": se.status,
        "payload_preview": se.payload_preview,
        "executed_at": se.executed_at.isoformat() if se.executed_at else None,
    }


def _serialize_artifact(a: Artifact) -> dict:
    return {
        "id": a.id,
        "run_id": a.run_id,
        "node_id": a.node_id,
        "produced_by_node_id": a.produced_by_node_id,
        "type": a.type,
        "path": a.path,
        "source_url": a.source_url,
        "description": a.description,
        "content_preview": a.content_preview,
        "content_hash": a.content_hash,
        "size_bytes": a.size_bytes,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


@router.post("", status_code=201)
def create_run(payload: dict[str, Any]) -> dict[str, Any]:
    required = {
        "id",
        "run_kind",
        "status",
        "original_prompt",
        "repo_path",
        "root_branch_id",
        "current_branch_id",
    }
    missing = required - set(payload)
    if missing:
        raise HTTPException(status_code=400, detail=f"missing fields: {sorted(missing)}")
    with Session(engine) as session:
        if session.get(Run, payload["id"]) is not None:
            raise HTTPException(status_code=409, detail="run already exists")
        run = Run(
            id=payload["id"],
            flow_id=payload.get("flow_id"),
            flow_version_id=payload.get("flow_version_id"),
            runner_id=payload.get("runner_id"),
            run_kind=payload["run_kind"],
            status=payload["status"],
            original_prompt=payload["original_prompt"],
            repo_path=payload["repo_path"],
            workspace_path=payload.get("workspace_path"),
            root_branch_id=payload["root_branch_id"],
            current_branch_id=payload["current_branch_id"],
            started_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        return _serialize_run(run)


@router.get("")
def list_runs(status: str | None = Query(default=None)) -> list[dict]:
    with Session(engine) as session:
        stmt = select(Run).order_by(Run.created_at.desc())  # type: ignore[arg-type]
        if status is not None:
            stmt = stmt.where(Run.status == status)
        rows = session.exec(stmt).all()
        return [_serialize_run(r) for r in rows]


@router.get("/{run_id}")
def get_run(run_id: str) -> dict:
    with Session(engine) as session:
        row = session.get(Run, run_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f"run not found: {run_id}")
        return _serialize_run(row)


@router.post("/{run_id}/checkpoints", status_code=201)
def create_checkpoint(run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    required = {"label", "backend", "git_ref", "git_commit_hash", "workspace_path", "branch_id"}
    missing = required - set(payload)
    if missing:
        raise HTTPException(status_code=400, detail=f"missing fields: {sorted(missing)}")
    with Session(engine) as session:
        run = session.get(Run, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"unknown run {run_id}")
        existing_count = len(
            list(session.exec(select(Checkpoint).where(Checkpoint.run_id == run_id)))
        )
        checkpoint = Checkpoint(
            id=f"cp_{run_id[-8:]}_{existing_count}",
            run_id=run_id,
            branch_id=payload["branch_id"],
            node_id=payload.get("node_id"),
            label=payload["label"],
            backend=payload["backend"],
            git_ref=payload["git_ref"],
            git_commit_hash=payload["git_commit_hash"],
            workspace_path=payload["workspace_path"],
            diff_summary=payload.get("diff_summary"),
            file_hashes_json=payload.get("file_hashes_json"),
            created_at=datetime.now(UTC),
        )
        session.add(checkpoint)
        session.commit()
        session.refresh(checkpoint)
        return _serialize_checkpoint(checkpoint)


@router.get("/{run_id}/dag")
def get_run_dag(run_id: str) -> dict:
    with Session(engine) as session:
        run = session.get(Run, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"run not found: {run_id}")
        nodes = session.exec(
            select(Node)
            .where(Node.run_id == run_id)
            .order_by(Node.started_at.asc())  # type: ignore[arg-type]
        ).all()
        edges = session.exec(select(Edge).where(Edge.run_id == run_id)).all()
        checkpoints = session.exec(
            select(Checkpoint)
            .where(Checkpoint.run_id == run_id)
            .order_by(Checkpoint.created_at.asc())  # type: ignore[arg-type]
        ).all()
        groups = session.exec(
            select(RunGroup)
            .where(RunGroup.run_id == run_id)
            .order_by(RunGroup.started_at.asc())  # type: ignore[arg-type]
        ).all()
        side_effects = session.exec(
            select(SideEffectLog)
            .where(SideEffectLog.run_id == run_id)
            .order_by(SideEffectLog.id.asc())  # type: ignore[arg-type]
        ).all()
        return {
            "run": _serialize_run(run),
            "nodes": [_serialize_node_summary(n) for n in nodes],
            "edges": [_serialize_edge(e) for e in edges],
            "checkpoints": [_serialize_checkpoint(c) for c in checkpoints],
            "groups": [_serialize_group(g) for g in groups],
            "side_effects": [_serialize_side_effect(se) for se in side_effects],
        }


@router.get("/{run_id}/nodes/{node_id}")
def get_node(run_id: str, node_id: str) -> dict:
    with Session(engine) as session:
        run = session.get(Run, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"run not found: {run_id}")
        node = session.get(Node, node_id)
        if node is None or node.run_id != run_id:
            raise HTTPException(status_code=404, detail=f"node not found in run {run_id}: {node_id}")

        edges = session.exec(
            select(NodeArtifactEdge).where(NodeArtifactEdge.node_id == node_id)
        ).all()
        artifact_ids = [e.artifact_id for e in edges]
        artifacts: list[Artifact] = []
        if artifact_ids:
            artifacts = list(
                session.exec(select(Artifact).where(Artifact.id.in_(artifact_ids))).all()  # type: ignore[attr-defined]
            )

        summary = _serialize_node_summary(node)
        summary.update(
            {
                "input_json": node.input_json,
                "output_json": node.output_json,
                "classification_reason": node.classification_reason,
                "classification_confidence": node.classification_confidence,
                "checkpoint_before_id": node.checkpoint_before_id,
                "checkpoint_after_id": node.checkpoint_after_id,
                "artifacts": [_serialize_artifact(a) for a in artifacts],
            }
        )
        return summary


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
