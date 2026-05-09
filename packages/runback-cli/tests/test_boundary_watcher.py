"""Boundary watcher tests."""
from __future__ import annotations

from typing import Any

from runback.runner.boundary_watcher import BoundaryDecision, BoundaryWatcher, classify_node


def _node(**overrides: Any) -> dict[str, Any]:
    base = {"id": "n1", "tool_name": None, "type": "tool", "status": "success", "input_json": {}}
    base.update(overrides)
    return base


def test_classify_edit_node_triggers_pre_and_post() -> None:
    assert (
        classify_node(_node(tool_name="Edit", status="running"), prev_status=None)
        == BoundaryDecision.CHECKPOINT_PRE
    )
    assert (
        classify_node(_node(tool_name="Edit", status="success"), prev_status="running")
        == BoundaryDecision.CHECKPOINT_POST
    )


def test_classify_bash_test_command_triggers_pre() -> None:
    for command in ("npm test", "pnpm run lint", "pytest", "tsc", "eslint .", "make test"):
        assert (
            classify_node(
                _node(tool_name="Bash", status="running", input_json={"command": command}),
                prev_status=None,
            )
            == BoundaryDecision.CHECKPOINT_PRE
        )


def test_classify_arbitrary_bash_no_checkpoint() -> None:
    assert (
        classify_node(
            _node(tool_name="Bash", status="running", input_json={"command": "echo hi"}),
            prev_status=None,
        )
        == BoundaryDecision.NONE
    )


def test_classify_failure_triggers_post() -> None:
    assert (
        classify_node(
            _node(tool_name="Bash", status="failed", input_json={"command": "npm test"}),
            prev_status="running",
        )
        == BoundaryDecision.CHECKPOINT_FAILURE
    )


def test_watcher_creates_checkpoints_for_each_decision() -> None:
    sequence = iter(
        [
            {"nodes": [_node(id="n_edit", tool_name="Edit", status="running")]},
            {"nodes": [_node(id="n_edit", tool_name="Edit", status="success")]},
        ]
    )
    created: list[tuple[str, str]] = []

    class FakeClient:
        def get_run_dag(self, run_id: str) -> dict[str, Any]:
            try:
                return next(sequence)
            except StopIteration:
                return {"nodes": []}

    watcher = BoundaryWatcher(
        run_id="run_x",
        client=FakeClient(),
        create_checkpoint_fn=lambda *, run_id, label, node_id: created.append((label, node_id)),
    )
    watcher.tick()
    watcher.tick()
    assert ("pre_edit", "n_edit") in created
    assert ("post_edit", "n_edit") in created
