"""Resume-prompt input gathering and Jinja rendering."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import jinja2
from sqlmodel import Session, select

from runback_server.models import (
    Artifact,
    Checkpoint,
    Node,
    NodeArtifactEdge,
    Run,
    RunGroup,
    SideEffectLog,
)
from runback_server.replay.recovery import RecoveryRecommendation

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_TEMPLATE_NAME = "resume.md.j2"

MAX_PROMPT_BYTES = 32 * 1024
_FAILURE_OUTPUT_TAIL_BYTES = 4 * 1024
_MAX_CACHED_ARTIFACTS = 10


def _env() -> jinja2.Environment:
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=jinja2.StrictUndefined,
    )


def _completed_groups(
    session: Session,
    run_id: str,
    side_effects: list[SideEffectLog],
) -> list[dict]:
    groups = session.exec(
        select(RunGroup).where(RunGroup.run_id == run_id).order_by(RunGroup.started_at)
    ).all()
    nodes = session.exec(select(Node).where(Node.run_id == run_id)).all()
    group_by_node = {node.id: node.group_id for node in nodes if node.group_id}
    refs_by_group: dict[str, list[str]] = {}
    for side_effect in side_effects:
        group_id = group_by_node.get(side_effect.node_id)
        if group_id and side_effect.external_ref:
            refs_by_group.setdefault(group_id, []).append(side_effect.external_ref)

    return [
        {
            "label": group.label,
            "status": group.status,
            "external_refs": refs_by_group.get(group.id, []),
        }
        for group in groups
        if group.status in {"success", "failed", "skipped"}
    ]


def _cached_artifacts(
    session: Session,
    run_id: str,
    reuse_node_ids: list[str],
) -> list[dict]:
    if not reuse_node_ids:
        return []
    edges = session.exec(
        select(NodeArtifactEdge).where(
            NodeArtifactEdge.run_id == run_id,
            NodeArtifactEdge.node_id.in_(reuse_node_ids),  # type: ignore[attr-defined]
            NodeArtifactEdge.direction == "output",
        )
    ).all()
    if not edges:
        return []
    artifact_ids = {edge.artifact_id for edge in edges}
    artifacts = session.exec(select(Artifact).where(Artifact.id.in_(artifact_ids))).all()  # type: ignore[attr-defined]
    return [
        {
            "description": artifact.description or f"{artifact.type} artifact ({artifact.id})",
            "path": artifact.path,
        }
        for artifact in artifacts
        if artifact.path
    ]


def _already_executed_side_effects(
    session: Session,
    run_id: str,
    node_ids: list[str],
) -> list[SideEffectLog]:
    if not node_ids:
        return []
    return list(
        session.exec(
            select(SideEffectLog).where(
                SideEffectLog.run_id == run_id,
                SideEffectLog.node_id.in_(node_ids),  # type: ignore[attr-defined]
                SideEffectLog.status == "executed",
            )
        ).all()
    )


def _scope_instruction(session: Session, run_id: str, failed_node_id: str) -> str | None:
    failed = session.get(Node, failed_node_id)
    if not failed or not failed.group_id:
        return None
    failed_group = session.get(RunGroup, failed.group_id)
    if not failed_group:
        return None
    groups = session.exec(
        select(RunGroup).where(RunGroup.run_id == run_id).order_by(RunGroup.started_at)
    ).all()
    pending_after = [
        group for group in groups if group.status == "pending" and group.id != failed_group.id
    ]
    if not pending_after:
        return f"Continue ONLY with **{failed_group.label}**."
    pending_labels = ", ".join(group.label for group in pending_after)
    return (
        f"Continue ONLY with **{failed_group.label}** first. "
        f"After it succeeds, proceed with: {pending_labels}."
    )


def gather_prompt_inputs(
    session: Session,
    *,
    run_id: str,
    failed_node_id: str,
    branch_id: str,
    recommendation: RecoveryRecommendation,
    user_context: str | None,
) -> dict[str, Any]:
    _ = branch_id
    run = session.get(Run, run_id)
    if run is None:
        raise ValueError(f"run {run_id!r} not found")
    failed = session.get(Node, failed_node_id)
    if failed is None:
        raise ValueError(f"failed node {failed_node_id!r} not found")
    checkpoint = session.get(Checkpoint, recommendation.recommended_checkpoint_id)
    if checkpoint is None:
        raise ValueError(f"checkpoint {recommendation.recommended_checkpoint_id!r} not found")

    scoped_nodes = list(
        set(
            recommendation.reuse_node_ids
            + recommendation.rerun_node_ids
            + recommendation.approval_node_ids
            + recommendation.unsafe_node_ids
        )
    )
    side_effects = _already_executed_side_effects(session, run_id, scoped_nodes)
    return {
        "original_prompt": run.original_prompt,
        "completed_groups": _completed_groups(session, run_id, side_effects),
        "cached_artifacts": _cached_artifacts(session, run_id, recommendation.reuse_node_ids),
        "checkpoint_label": checkpoint.label,
        "failed_node_label": failed.label,
        "failure_output": (failed.output_preview or failed.error or "").strip(),
        "already_executed_side_effects": [
            {"kind": se.kind, "external_ref": se.external_ref, "key": se.idempotency_key}
            for se in side_effects
        ],
        "user_context": user_context,
        "scope_instruction": _scope_instruction(session, run_id, failed_node_id),
    }


def _render(inputs: dict[str, Any]) -> str:
    return _env().get_template(_TEMPLATE_NAME).render(**inputs)


def _fits(text: str) -> bool:
    return len(text.encode("utf-8")) <= MAX_PROMPT_BYTES


def _apply_truncation(inputs: dict[str, Any]) -> dict[str, Any]:
    out = dict(inputs)
    if _fits(_render(out)):
        return out

    failure_output = out.get("failure_output") or ""
    if isinstance(failure_output, str) and failure_output:
        out["failure_output"] = "[truncated]\n" + failure_output[-_FAILURE_OUTPUT_TAIL_BYTES:]
    if _fits(_render(out)):
        return out

    out["cached_artifacts"] = (out.get("cached_artifacts") or [])[-_MAX_CACHED_ARTIFACTS:]
    if _fits(_render(out)):
        return out

    groups = out.get("completed_groups") or []
    if len(groups) > 5:
        out["completed_groups"] = [
            {
                "label": f"({len(groups) - 5} earlier groups completed)",
                "status": "summary",
                "external_refs": [],
            },
            *groups[-5:],
        ]
    if _fits(_render(out)):
        return out

    out["failure_output"] = "[truncated - full output is stored in the Runback archive]"
    return out


def build_resume_prompt(
    session: Session,
    *,
    run_id: str,
    failed_node_id: str,
    branch_id: str,
    recommendation: RecoveryRecommendation,
    user_context: str | None,
) -> str:
    inputs = gather_prompt_inputs(
        session,
        run_id=run_id,
        failed_node_id=failed_node_id,
        branch_id=branch_id,
        recommendation=recommendation,
        user_context=user_context,
    )
    prompt = _render(_apply_truncation(inputs))
    if _fits(prompt):
        return prompt

    # Final guard for very small test caps: shrink the failure section further.
    compact = dict(inputs)
    compact["failure_output"] = "[truncated]"
    prompt = _render(compact)
    while not _fits(prompt) and len(compact["failure_output"]) > 0:
        compact["failure_output"] = compact["failure_output"][:-1]
        prompt = _render(compact)
    return prompt
