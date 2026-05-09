"""Poll backend DAG snapshots and trigger checkpoints at useful boundaries."""
from __future__ import annotations

import enum
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol


class BoundaryDecision(enum.Enum):
    NONE = "none"
    CHECKPOINT_PRE = "pre"
    CHECKPOINT_POST = "post"
    CHECKPOINT_FAILURE = "failure"


_TEST_BUILD_RE = re.compile(
    r"^\s*("
    r"(npm|pnpm|yarn)\s+(run\s+)?(test|build|lint|typecheck)|"
    r"pytest|"
    r"tsc|"
    r"eslint|"
    r"ruff|"
    r"cargo\s+(test|build|check)|"
    r"go\s+(test|build)|"
    r"make\s+(test|build|lint)"
    r")\b"
)


def classify_node(node: dict[str, Any], prev_status: str | None) -> BoundaryDecision:
    tool = node.get("tool_name") or ""
    status = node.get("status") or ""
    if tool in {"Edit", "Write", "MultiEdit"}:
        if status == "running" and prev_status is None:
            return BoundaryDecision.CHECKPOINT_PRE
        if prev_status == "running" and status == "success":
            return BoundaryDecision.CHECKPOINT_POST
        if prev_status == "running" and status == "failed":
            return BoundaryDecision.CHECKPOINT_FAILURE
    if tool == "Bash":
        command = (node.get("input_json") or {}).get("command", "") or ""
        if _TEST_BUILD_RE.match(command):
            if status == "running" and prev_status is None:
                return BoundaryDecision.CHECKPOINT_PRE
            if prev_status == "running" and status == "failed":
                return BoundaryDecision.CHECKPOINT_FAILURE
    return BoundaryDecision.NONE


class DagClient(Protocol):
    def get_run_dag(self, run_id: str) -> dict[str, Any]: ...


CheckpointCreateFn = Callable[..., None]


@dataclass
class BoundaryWatcher:
    run_id: str
    client: DagClient
    create_checkpoint_fn: CheckpointCreateFn
    _prev_status: dict[str, str] = field(init=False, default_factory=dict)

    def tick(self) -> None:
        dag = self.client.get_run_dag(self.run_id)
        for node in dag.get("nodes", []):
            node_id = node.get("id")
            if not node_id:
                continue
            prev = self._prev_status.get(node_id)
            decision = classify_node(node, prev)
            if decision != BoundaryDecision.NONE:
                self.create_checkpoint_fn(
                    run_id=self.run_id,
                    label=self._label_for(node, decision),
                    node_id=node_id,
                )
            self._prev_status[node_id] = node.get("status") or ""

    @staticmethod
    def _label_for(node: dict[str, Any], decision: BoundaryDecision) -> str:
        kind = {
            BoundaryDecision.CHECKPOINT_PRE: "pre",
            BoundaryDecision.CHECKPOINT_POST: "post",
            BoundaryDecision.CHECKPOINT_FAILURE: "failure",
        }[decision]
        tool = node.get("tool_name") or "tool"
        if tool in {"Edit", "Write", "MultiEdit"}:
            return f"{kind}_edit"
        if tool == "Bash":
            return f"{kind}_bash_verify"
        return f"{kind}_{tool.lower()}"
