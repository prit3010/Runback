"""Tool-default classifier rules per docs/contracts/policies.md."""
from __future__ import annotations

import pytest
from runback_server.classifier.rules import ClassificationResult, classify


def test_classify_returns_classification_result():
    result = classify("Read", {"file_path": "/tmp/x"})
    assert isinstance(result, ClassificationResult)
    assert result.recovery_policy
    assert result.classification_reason


@pytest.mark.parametrize(
    "tool_name,expected_policy",
    [
        ("Read", "reuse_cached"),
        ("Grep", "reuse_cached"),
        ("Glob", "reuse_cached"),
        ("WebFetch", "reuse_cached"),
        ("WebSearch", "reuse_cached"),
        ("Edit", "restore_checkpoint"),
        ("Write", "restore_checkpoint"),
        ("MultiEdit", "restore_checkpoint"),
        ("TodoWrite", "rerun"),
        ("Task", "unknown"),
    ],
)
def test_tool_defaults(tool_name: str, expected_policy: str):
    result = classify(tool_name, {})
    assert result.recovery_policy == expected_policy
    assert result.classification_reason
    assert result.kind is None
    assert result.idempotency_key is None


def test_unknown_tool_falls_back_to_unknown_policy():
    result = classify("FooBarTool", {})
    assert result.recovery_policy == "unknown"
    assert "no rule" in result.classification_reason.lower()


def test_mcp_tool_falls_back_to_unknown():
    result = classify("mcp__github__create_issue", {})
    assert result.recovery_policy == "unknown"


def test_classify_handles_none_tool_input():
    result = classify("Read", None)
    assert result.recovery_policy == "reuse_cached"


def test_classify_handles_empty_tool_name():
    result = classify("", {})
    assert result.recovery_policy == "unknown"
