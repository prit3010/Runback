"""Builders for synthetic Run / Node / Edge / Checkpoint / RunGroup graphs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from runback_server.models import Checkpoint, Edge, Node, Run, RunGroup, SideEffectLog
from sqlmodel import Session


def _t() -> datetime:
    return datetime(2026, 5, 9, 12, 0, 0, tzinfo=UTC)


@dataclass
class DagBuilder:
    session: Session
    run_id: str
    branch: str = "branch_root"
    _committed: bool = field(default=False, init=False)
    _node_ids: list[str] = field(default_factory=list, init=False)

    def run(
        self,
        *,
        prompt: str = "do thing",
        repo_path: str = "/tmp/x",
        status: str = "running",
    ) -> Run:
        row = Run(
            id=self.run_id,
            run_kind="ad_hoc",
            status=status,
            original_prompt=prompt,
            repo_path=repo_path,
            workspace_path=repo_path,
            root_branch_id=self.branch,
            current_branch_id=self.branch,
            started_at=_t(),
            created_at=_t(),
        )
        self.session.add(row)
        self.session.flush()
        return row

    def group(
        self,
        group_id: str,
        *,
        label: str,
        kind: str = "ticket",
        status: str = "success",
        parent: str | None = None,
    ) -> RunGroup:
        row = RunGroup(
            id=group_id,
            run_id=self.run_id,
            parent_group_id=parent,
            label=label,
            kind=kind,
            status=status,
            started_at=_t(),
            ended_at=_t() if status in {"success", "failed", "skipped"} else None,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def checkpoint(
        self,
        cp_id: str,
        *,
        label: str,
        node_id: str | None = None,
        git_ref: str | None = None,
    ) -> Checkpoint:
        row = Checkpoint(
            id=cp_id,
            run_id=self.run_id,
            branch_id=self.branch,
            node_id=node_id,
            label=label,
            backend="hidden_ref",
            git_ref=git_ref or f"refs/runback/{self.run_id}/{cp_id}",
            workspace_path=f"/tmp/{self.run_id}/ws",
            created_at=_t(),
        )
        self.session.add(row)
        self.session.flush()
        return row

    def node(
        self,
        node_id: str,
        *,
        label: str,
        policy: str = "reuse_cached",
        status: str = "success",
        node_type: str = "tool",
        tool_name: str | None = "Read",
        group_id: str | None = None,
        checkpoint_before_id: str | None = None,
        checkpoint_after_id: str | None = None,
        output_preview: str | None = None,
        error: str | None = None,
        input_json: dict[str, Any] | None = None,
    ) -> Node:
        row = Node(
            id=node_id,
            run_id=self.run_id,
            branch_id=self.branch,
            group_id=group_id,
            claude_tool_use_id=None,
            event_type="PreToolUse" if node_type == "tool" else "Synthesized",
            type=node_type,
            label=label,
            tool_name=tool_name,
            input_json=input_json,
            output_preview=output_preview,
            error=error,
            status=status,
            recovery_policy=policy,
            checkpoint_before_id=checkpoint_before_id,
            checkpoint_after_id=checkpoint_after_id,
            started_at=_t(),
            ended_at=_t(),
        )
        self.session.add(row)
        self.session.flush()
        self._node_ids.append(node_id)
        return row

    def chain(self, *node_ids: str, edge_type: str = "sequence") -> list[Edge]:
        edges: list[Edge] = []
        for src, dst in zip(node_ids, node_ids[1:], strict=False):
            row = Edge(
                id=f"edge_{src}_{dst}",
                run_id=self.run_id,
                branch_id=self.branch,
                source_node_id=src,
                target_node_id=dst,
                edge_type=edge_type,
            )
            self.session.add(row)
            self.session.flush()
            edges.append(row)
        return edges

    def side_effect(
        self,
        *,
        node_id: str,
        kind: str,
        key: str,
        status: str = "executed",
        external_ref: str | None = None,
    ) -> SideEffectLog:
        row = SideEffectLog(
            run_id=self.run_id,
            branch_id=self.branch,
            node_id=node_id,
            kind=kind,
            idempotency_key=key,
            status=status,
            external_ref=external_ref,
            executed_at=_t() if status == "executed" else None,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def commit(self) -> None:
        if self._committed:
            return
        self.session.commit()
        self._committed = True
