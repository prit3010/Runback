"""Hook-event normalizer."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from runback_server.db import engine
from runback_server.ingest import groups, reconciler
from runback_server.ingest.ids import branch_id
from runback_server.models import Run
from runback_server.schemas.hook_events import HookEvent, parse_hook_event


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


@dataclass
class Normalizer:
    runtime_root: Path

    def handle(
        self, run_id: str, payload: dict[str, Any], branch_id_override: str | None = None
    ) -> None:
        event = parse_hook_event(payload)
        with Session(engine) as session:
            run = self._ensure_run(session, run_id, event, branch_id_override=branch_id_override)
            self._dispatch(session, run, event)
            session.commit()

    def _ensure_run(
        self,
        session: Session,
        run_id: str,
        event: HookEvent,
        branch_id_override: str | None = None,
    ) -> Run:
        existing = session.get(Run, run_id)
        if existing is not None:
            if branch_id_override:
                existing.current_branch_id = branch_id_override
            return existing

        branch = branch_id_override or branch_id()
        run = Run(
            id=run_id,
            run_kind="ad_hoc",
            status="running",
            original_prompt=event.prompt or "(no prompt captured)",
            repo_path=event.cwd,
            workspace_path=event.cwd,
            root_branch_id=branch,
            current_branch_id=branch,
            started_at=_now(),
            created_at=_now(),
        )
        session.add(run)
        try:
            session.flush()
        except IntegrityError:
            session.rollback()
            existing = session.get(Run, run_id)
            if existing is not None:
                return existing
            raise
        return run

    def _dispatch(self, session: Session, run: Run, event: HookEvent) -> None:
        event_name = event.hook_event_name

        if event_name == "UserPromptSubmit":
            reconciler.apply_user_prompt(session, run, event)
            return

        if event_name == "PreToolUse":
            if event.tool_name == "TodoWrite":
                groups.apply_todowrite(session, run.id, event)
                return
            node = reconciler.apply_pre(session, run, event)
            node.group_id = groups.current_open_group_id(session, run.id)
            return

        if event_name == "PostToolUse":
            if event.tool_name == "TodoWrite":
                return
            reconciler.apply_post(session, run, event)
            return

        if event_name == "PostToolUseFailure":
            if event.tool_name == "TodoWrite":
                return
            reconciler.apply_post_failure(session, run, event)
            return

        if event_name == "Stop":
            run.status = "success"
            run.ended_at = _now()
            return

        if event_name == "StopFailure":
            run.status = "failed"
            run.ended_at = _now()
