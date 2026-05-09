"""Recovery-point selection and DAG ancestor walking."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from sqlmodel import Session, select

from runback_server.models import Checkpoint, Edge, Node, SideEffectLog


@dataclass
class RecoveryRecommendation:
    source_node_id: str
    recommended_checkpoint_id: str
    confidence: float
    reasons: list[str] = field(default_factory=list)
    reuse_node_ids: list[str] = field(default_factory=list)
    rerun_node_ids: list[str] = field(default_factory=list)
    approval_node_ids: list[str] = field(default_factory=list)
    unsafe_node_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "source_node_id": self.source_node_id,
            "recommended_checkpoint_id": self.recommended_checkpoint_id,
            "confidence": self.confidence,
            "reason": self.reasons,
            "reuse_node_ids": self.reuse_node_ids,
            "rerun_node_ids": self.rerun_node_ids,
            "approval_node_ids": self.approval_node_ids,
            "unsafe_node_ids": self.unsafe_node_ids,
        }


def walk_ancestors(
    session: Session,
    *,
    run_id: str,
    node_id: str,
    branch_id: str,
) -> list[str]:
    """Return sequence ancestors of a node, closest first."""
    edges = session.exec(
        select(Edge).where(
            Edge.run_id == run_id,
            Edge.branch_id == branch_id,
            Edge.edge_type == "sequence",
        )
    ).all()
    parents: dict[str, list[str]] = {}
    for edge in edges:
        parents.setdefault(edge.target_node_id, []).append(edge.source_node_id)

    out: list[str] = []
    seen: set[str] = {node_id}
    queue: deque[str] = deque([node_id])
    while queue:
        current = queue.popleft()
        for parent in parents.get(current, []):
            if parent in seen:
                continue
            seen.add(parent)
            out.append(parent)
            queue.append(parent)
    return out


def _ledger_executed(session: Session, run_id: str, node_id: str) -> bool:
    row = session.exec(
        select(SideEffectLog)
        .where(
            SideEffectLog.run_id == run_id,
            SideEffectLog.node_id == node_id,
            SideEffectLog.status == "executed",
        )
        .limit(1)
    ).first()
    return row is not None


def _earliest_checkpoint_id(session: Session, run_id: str, branch_id: str) -> str | None:
    rows = session.exec(
        select(Checkpoint)
        .where(Checkpoint.run_id == run_id, Checkpoint.branch_id == branch_id)
        .order_by(Checkpoint.created_at)
    ).all()
    return rows[0].id if rows else None


def _nearest_inline_checkpoint(session: Session, ancestor_ids: list[str]) -> str | None:
    if not ancestor_ids:
        return None
    rows = session.exec(select(Node).where(Node.id.in_(ancestor_ids))).all()  # type: ignore[attr-defined]
    by_id = {node.id: node for node in rows}
    for node_id in ancestor_ids:
        node = by_id.get(node_id)
        if node and node.checkpoint_before_id:
            return node.checkpoint_before_id
    return None


def select_recovery(
    session: Session,
    *,
    run_id: str,
    failed_node_id: str,
    branch_id: str,
) -> RecoveryRecommendation:
    failed = session.get(Node, failed_node_id)
    if failed is None or failed.run_id != run_id:
        raise ValueError(f"failed node {failed_node_id!r} not found in run {run_id!r}")

    ancestors = walk_ancestors(
        session,
        run_id=run_id,
        node_id=failed_node_id,
        branch_id=branch_id,
    )
    checkpoint_id = _nearest_inline_checkpoint(session, ancestors)
    if checkpoint_id is None:
        checkpoint_id = _earliest_checkpoint_id(session, run_id, branch_id)
    if checkpoint_id is None:
        raise ValueError(f"no checkpoint available on run {run_id!r} branch {branch_id!r}")

    checkpoint = session.get(Checkpoint, checkpoint_id)
    if checkpoint is None:
        raise ValueError(f"checkpoint {checkpoint_id!r} not found")

    ancestor_rows = session.exec(select(Node).where(Node.id.in_(ancestors))).all()  # type: ignore[attr-defined]
    by_id = {node.id: node for node in ancestor_rows}
    reuse: list[str] = []
    rerun: list[str] = []
    approval: list[str] = []
    unsafe: list[str] = []
    reasons = [f"recovered from checkpoint {checkpoint_id} ({checkpoint.label!r})"]

    for node_id in ancestors:
        node = by_id.get(node_id)
        if node is None:
            continue
        policy = (node.recovery_policy or "unknown").lower()
        if policy in {"reuse_cached", "restore_checkpoint"}:
            reuse.append(node_id)
        elif policy == "rerun":
            rerun.append(node_id)
        elif policy == "requires_approval":
            if _ledger_executed(session, run_id, node_id):
                reuse.append(node_id)
                reasons.append(f"node {node_id} ({node.label}) already executed; reusing")
            else:
                approval.append(node_id)
                reasons.append(f"node {node_id} ({node.label}) requires approval")
        elif policy == "unsafe":
            unsafe.append(node_id)
            reasons.append(f"node {node_id} ({node.label}) is unsafe")
        else:
            rerun.append(node_id)
            reasons.append(f"node {node_id} ({node.label}) policy unknown; rerun")

    rerun.append(failed_node_id)
    confidence = max(0.0, min(1.0, 1.0 - (0.3 * len(approval)) - (0.6 * len(unsafe))))
    return RecoveryRecommendation(
        source_node_id=failed_node_id,
        recommended_checkpoint_id=checkpoint_id,
        confidence=confidence,
        reasons=reasons,
        reuse_node_ids=reuse,
        rerun_node_ids=rerun,
        approval_node_ids=approval,
        unsafe_node_ids=unsafe,
    )
