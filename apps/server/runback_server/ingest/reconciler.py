"""PreToolUse/PostToolUse pairing and sequence-edge maintenance."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlmodel import Session, select

from runback_server.ingest.ids import edge_id, node_id
from runback_server.models import Edge, Node, Run
from runback_server.schemas.hook_events import HookEvent


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _last_node_id(session: Session, run: Run) -> str | None:
    rows = session.exec(
        select(Node)
        .where(Node.run_id == run.id, Node.branch_id == run.current_branch_id)
        .order_by(Node.started_at.desc())  # type: ignore[arg-type]
    ).all()
    return rows[0].id if rows else None


def _add_sequence_edge(session: Session, run: Run, target_node_id: str) -> None:
    source_node_id = _last_node_id(session, run)
    if source_node_id is None or source_node_id == target_node_id:
        return
    session.add(
        Edge(
            id=edge_id(),
            run_id=run.id,
            branch_id=run.current_branch_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            edge_type="sequence",
        )
    )


def _label_for_tool(tool_name: str, tool_input: dict[str, Any] | None) -> str:
    tool_input = tool_input or {}
    if tool_name == "Bash":
        lines = (tool_input.get("command") or "").splitlines()
        command = lines[0][:80] if lines else ""
        return f"Bash: {command}" if command else "Bash"
    if tool_name in {"Read", "Write", "Edit"}:
        path = tool_input.get("file_path") or tool_input.get("path") or ""
        return f"{tool_name} {path}".strip()
    if tool_name == "Grep":
        return f"Grep {tool_input.get('pattern', '')}".strip()
    if tool_name == "Glob":
        return f"Glob {tool_input.get('pattern', '')}".strip()
    if tool_name == "WebFetch":
        return f"WebFetch {tool_input.get('url', '')}".strip()
    return tool_name


def apply_user_prompt(session: Session, run: Run, evt: HookEvent) -> Node:
    node = Node(
        id=node_id(),
        run_id=run.id,
        branch_id=run.current_branch_id,
        event_type="UserPromptSubmit",
        type="prompt",
        label=f"Prompt: {(evt.prompt or '')[:60]}",
        status="success",
        recovery_policy="reuse_cached",
        started_at=_now(),
        ended_at=_now(),
        duration_ms=0,
    )
    _add_sequence_edge(session, run, node.id)
    session.add(node)
    return node


def apply_pre(session: Session, run: Run, evt: HookEvent) -> Node:
    tool_use_id = evt.tool_use_id or f"anon_{node_id()}"
    node = Node(
        id=node_id(),
        run_id=run.id,
        branch_id=run.current_branch_id,
        claude_tool_use_id=tool_use_id,
        event_type="PreToolUse",
        type="tool",
        label=_label_for_tool(evt.tool_name or "", evt.tool_input),
        tool_name=evt.tool_name,
        input_json=evt.tool_input,
        status="running",
        recovery_policy="unknown",
        started_at=_now(),
    )
    _add_sequence_edge(session, run, node.id)
    session.add(node)
    return node


def _find_pending_node(session: Session, run: Run, tool_use_id: str) -> Node | None:
    rows = session.exec(
        select(Node).where(
            Node.run_id == run.id,
            Node.claude_tool_use_id == tool_use_id,
            Node.status == "running",
        )
    ).all()
    return rows[0] if rows else None


def _ensure_node_for_orphan_post(session: Session, run: Run, evt: HookEvent) -> Node:
    node = Node(
        id=node_id(),
        run_id=run.id,
        branch_id=run.current_branch_id,
        claude_tool_use_id=evt.tool_use_id,
        event_type="PostToolUse",
        type="tool",
        label=_label_for_tool(evt.tool_name or "", evt.tool_input),
        tool_name=evt.tool_name,
        input_json=evt.tool_input,
        status="running",
        recovery_policy="unknown",
        started_at=_now(),
    )
    _add_sequence_edge(session, run, node.id)
    session.add(node)
    session.flush()
    return node


def _finish_duration(node: Node) -> None:
    node.ended_at = _now()
    if node.started_at is not None:
        node.duration_ms = max(0, int((node.ended_at - node.started_at).total_seconds() * 1000))


def apply_post(session: Session, run: Run, evt: HookEvent) -> Node:
    node = _find_pending_node(session, run, evt.tool_use_id or "")
    if node is None:
        node = _ensure_node_for_orphan_post(session, run, evt)

    response = evt.tool_response
    if response is not None:
        node.output_json = response.model_dump(by_alias=True)
        node.output_preview = (
            (response.stdout or "")[:30000] if not response.is_image else "[image]"
        )
        from runback_server.ingest.artifacts import maybe_copy_persisted_output

        maybe_copy_persisted_output(
            session,
            run.id,
            node,
            response.persisted_output_path,
            response.persisted_output_size,
        )

    node.status = "success"
    _finish_duration(node)
    return node


def apply_post_failure(session: Session, run: Run, evt: HookEvent) -> Node:
    node = _find_pending_node(session, run, evt.tool_use_id or "")
    if node is None:
        node = _ensure_node_for_orphan_post(session, run, evt)

    error_text = ""
    response = evt.tool_response
    if response is not None:
        node.output_json = response.model_dump(by_alias=True)
        error_text = (response.stderr or "") or (response.stdout or "")
        from runback_server.ingest.artifacts import maybe_copy_persisted_output

        maybe_copy_persisted_output(
            session,
            run.id,
            node,
            response.persisted_output_path,
            response.persisted_output_size,
        )

    node.error = error_text[:8000] or "(no error text)"
    node.status = "failed"
    _finish_duration(node)
    if run.failure_node_id is None:
        run.failure_node_id = node.id
    return node
