"""Replay endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session

from runback_server.db import engine
from runback_server.ingest.ids import branch_id, replay_id
from runback_server.models import ReplayAttempt, Run
from runback_server.replay.launcher import LauncherError, ReplayLaunchPayload, send_replay
from runback_server.replay.recovery import select_recovery
from runback_server.replay.resume_prompt import build_resume_prompt

router = APIRouter()


class ReplayRequestBody(BaseModel):
    node_id: str = Field(..., description="The failed node to replay from")
    user_context: str | None = Field(default=None)
    edited_resume_prompt: str | None = Field(default=None)


def _now() -> datetime:
    return datetime.now(UTC)


def _load_run(session: Session, run_id: str) -> Run:
    run = session.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"run {run_id!r} not found")
    return run


def _attempt_to_dict(row: ReplayAttempt) -> dict[str, Any]:
    return {
        "id": row.id,
        "run_id": row.run_id,
        "source_node_id": row.source_node_id,
        "source_checkpoint_id": row.source_checkpoint_id,
        "parent_branch_id": row.parent_branch_id,
        "new_branch_id": row.new_branch_id,
        "resume_prompt": row.resume_prompt,
        "status": row.status,
        "created_at": row.created_at.isoformat(),
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "ended_at": row.ended_at.isoformat() if row.ended_at else None,
    }


@router.post("/runs/{run_id}/replay", status_code=202)
def replay_run(run_id: str, body: ReplayRequestBody) -> dict[str, Any]:
    with Session(engine) as session:
        run = _load_run(session, run_id)
        try:
            recommendation = select_recovery(
                session,
                run_id=run_id,
                failed_node_id=body.node_id,
                branch_id=run.current_branch_id,
            )
        except ValueError as exc:
            message = str(exc)
            if "not found" in message:
                raise HTTPException(status_code=404, detail=message) from exc
            raise HTTPException(status_code=400, detail=message) from exc

        resume_prompt = body.edited_resume_prompt
        if resume_prompt is None:
            resume_prompt = build_resume_prompt(
                session,
                run_id=run_id,
                failed_node_id=body.node_id,
                branch_id=run.current_branch_id,
                recommendation=recommendation,
                user_context=body.user_context,
            )

        new_branch = branch_id()
        replay_attempt_id = replay_id()
        attempt = ReplayAttempt(
            id=replay_attempt_id,
            run_id=run_id,
            source_node_id=body.node_id,
            source_checkpoint_id=recommendation.recommended_checkpoint_id,
            parent_branch_id=run.current_branch_id,
            new_branch_id=new_branch,
            resume_prompt=resume_prompt,
            user_context=body.user_context,
            status="created",
            recommendation_json=recommendation.to_dict(),
            created_at=_now(),
        )
        session.add(attempt)
        session.commit()
        session.refresh(attempt)

        payload = ReplayLaunchPayload(
            run_id=run_id,
            checkpoint_id=recommendation.recommended_checkpoint_id,
            new_branch_id=new_branch,
            resume_prompt=resume_prompt,
            replay_id=replay_attempt_id,
        )
        try:
            ack = send_replay(payload)
            attempt.status = "running"
            attempt.started_at = _now()
            recommendation_json = dict(attempt.recommendation_json or {})
            recommendation_json["runner_pid"] = ack.get("pid")
            attempt.recommendation_json = recommendation_json
        except LauncherError as exc:
            attempt.status = "failed"
            attempt.ended_at = _now()
            attempt.generated_context = f"runner launch failed: {exc} (code={exc.code})"

        session.add(attempt)
        session.commit()
        session.refresh(attempt)
        # TODO(plan-2c): publish replay.created over the SSE bus here.
        return _attempt_to_dict(attempt)


@router.get("/runs/{run_id}/replay/recommendation")
def get_replay_recommendation(
    run_id: str,
    node_id: str = Query(..., alias="nodeId", description="The failed node id to replay from"),
) -> dict[str, Any]:
    with Session(engine) as session:
        run = _load_run(session, run_id)
        try:
            recommendation = select_recovery(
                session,
                run_id=run_id,
                failed_node_id=node_id,
                branch_id=run.current_branch_id,
            )
        except ValueError as exc:
            message = str(exc)
            if "not found" in message:
                raise HTTPException(status_code=404, detail=message) from exc
            raise HTTPException(status_code=400, detail=message) from exc

        prompt = build_resume_prompt(
            session,
            run_id=run_id,
            failed_node_id=node_id,
            branch_id=run.current_branch_id,
            recommendation=recommendation,
            user_context=None,
        )

    body = recommendation.to_dict()
    body["generated_resume_prompt"] = prompt
    return body
