"""SSE event union must round-trip through JSON without losing fields."""
from __future__ import annotations

from runback_server.schemas.sse_events import (
    EdgeCreatedPayload,
    GroupOpenedPayload,
    NodeCreatedPayload,
    NodeUpdatedPayload,
    SideEffectLoggedPayload,
    SseEvent,
)


def test_node_created_roundtrip():
    evt = {
        "type": "node.created",
        "run_id": "run_1",
        "payload": NodeCreatedPayload(
            node_id="n1",
            branch_id="b1",
            type="tool",
            label="Read foo",
            tool_name="Read",
            recovery_policy="reuse_cached",
            status="running",
            group_id=None,
        ).model_dump(),
    }
    parsed = SseEvent.validate_python(evt)
    assert parsed.payload.node_id == "n1"


def test_node_updated_roundtrip():
    parsed = SseEvent.validate_python(
        {
            "type": "node.updated",
            "run_id": "run_1",
            "payload": NodeUpdatedPayload(
                node_id="n1",
                status="success",
                duration_ms=42,
            ).model_dump(),
        }
    )
    assert parsed.payload.status == "success"


def test_group_opened_roundtrip():
    parsed = SseEvent.validate_python(
        {
            "type": "group.opened",
            "run_id": "run_1",
            "payload": GroupOpenedPayload(
                group_id="g1",
                parent_group_id=None,
                label="Ticket #1",
                kind="ticket",
            ).model_dump(),
        }
    )
    assert parsed.payload.label == "Ticket #1"


def test_side_effect_logged_roundtrip():
    parsed = SseEvent.validate_python(
        {
            "type": "side_effect.logged",
            "run_id": "run_1",
            "payload": SideEffectLoggedPayload(
                node_id="n1",
                kind="gh_pr_create",
                idempotency_key="gh:pr:owner/repo:fix/issue-1",
                status="executed",
                external_ref="https://github.com/x/y/pull/1",
            ).model_dump(),
        }
    )
    assert parsed.payload.kind == "gh_pr_create"


def test_edge_created_roundtrip():
    parsed = SseEvent.validate_python(
        {
            "type": "edge.created",
            "run_id": "run_1",
            "payload": EdgeCreatedPayload(
                edge_id="e1",
                source_node_id="n1",
                target_node_id="n2",
                edge_type="sequence",
                branch_id="b1",
            ).model_dump(),
        }
    )
    assert parsed.payload.edge_type == "sequence"
