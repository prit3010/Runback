"""Side-effect ledger reads/writes."""
from __future__ import annotations

import re
from datetime import UTC, datetime

from sqlmodel import Session, select

from runback_server.classifier import classify
from runback_server.classifier.keys import derive_key, derive_key_for_post
from runback_server.models import Node, Run, SideEffectLog
from runback_server.schemas.hook_events import HookEvent


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


_PR_URL = re.compile(r"https?://[^\s]*github\.com/[^\s]+/pull/\d+")
_SLACK_TS = re.compile(r"\bts=([0-9.]+)\b")
_PUSH_SHA_RANGE = re.compile(r"\b([0-9a-f]{3,40})\.\.([0-9a-f]{3,40})\b")
_HTTP_STATUS = re.compile(r"\bHTTP/[0-9.]+\s+(\d{3})\b")


def extract_external_ref(kind: str, stdout: str | None, stderr: str | None) -> str | None:
    """Best-effort extraction of an external reference from command output."""
    output = f"{stdout or ''}\n{stderr or ''}"
    if not output.strip():
        return None

    if kind == "gh_pr_create":
        match = _PR_URL.search(output)
        if match:
            return match.group(0)

    if kind == "slack_post":
        match = _SLACK_TS.search(output)
        if match:
            return f"slack-msg:{match.group(1)}"

    if kind == "git_push":
        match = _PUSH_SHA_RANGE.search(output)
        if match:
            return f"sha:{match.group(2)}"

    if kind.startswith("http_"):
        match = _HTTP_STATUS.search(output)
        if match:
            return f"status:{match.group(1)}"

    url_match = re.search(r"https?://\S+", output)
    return url_match.group(0) if url_match else None


def lookup_executed(session: Session, kind: str, key: str) -> SideEffectLog | None:
    """Return an executed ledger row for a kind/key pair, if one exists."""
    return session.exec(
        select(SideEffectLog).where(
            SideEffectLog.kind == kind,
            SideEffectLog.idempotency_key == key,
            SideEffectLog.status == "executed",
        )
    ).first()


def record_pre(
    session: Session,
    run: Run,
    node: Node,
    evt: HookEvent,
) -> SideEffectLog | None:
    """Mark a side-effect node as reused when its key was executed before."""
    if node.recovery_policy != "requires_approval":
        return None

    result = classify(evt.tool_name or "", evt.tool_input)
    if result.kind is None:
        return None

    command = (evt.tool_input or {}).get("command") or ""
    key = derive_key(kind=result.kind, command=command)
    prior = lookup_executed(session, result.kind, key)
    if prior is None:
        return None

    node.status = "reused"
    node.ended_at = _now()
    if node.started_at is not None:
        node.duration_ms = max(0, int((node.ended_at - node.started_at).total_seconds() * 1000))
    if prior.external_ref:
        node.classification_reason = (
            f"{node.classification_reason or ''} [reused: {prior.external_ref}]"
        ).strip()
    session.add(node)
    return prior


def record_post(
    session: Session,
    run: Run,
    node: Node,
    evt: HookEvent,
) -> SideEffectLog | None:
    """Insert or update the executed ledger row for a side-effect node."""
    if node.recovery_policy != "requires_approval" or node.status == "reused":
        return None

    result = classify(evt.tool_name or "", evt.tool_input)
    if result.kind is None:
        return None

    command = (evt.tool_input or {}).get("command") or ""
    pre_key = derive_key(kind=result.kind, command=command)
    response = evt.tool_response
    stdout = response.stdout if response is not None else None
    stderr = response.stderr if response is not None else None
    final_key = derive_key_for_post(
        kind=result.kind,
        pre_key=pre_key,
        command=command,
        tool_response_stdout=stdout,
    )
    external_ref = extract_external_ref(result.kind, stdout, stderr)

    existing = session.exec(
        select(SideEffectLog).where(
            SideEffectLog.kind == result.kind,
            SideEffectLog.idempotency_key == final_key,
        )
    ).first()
    if existing is not None:
        existing.status = "executed"
        if existing.external_ref is None and external_ref:
            existing.external_ref = external_ref
        if existing.executed_at is None:
            existing.executed_at = _now()
        session.add(existing)
        return existing

    row = SideEffectLog(
        run_id=run.id,
        branch_id=node.branch_id,
        node_id=node.id,
        kind=result.kind,
        idempotency_key=final_key,
        external_ref=external_ref,
        status="executed",
        payload_preview=(command[:120] if command else None),
        executed_at=_now(),
    )
    session.add(row)
    session.flush()
    return row
