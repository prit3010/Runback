"""Rule-based recovery-policy classifier."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_TOOL_DEFAULTS: dict[str, tuple[str, str]] = {
    "Read": ("reuse_cached", "Read tool default: cache by file content_hash"),
    "Grep": ("reuse_cached", "Grep tool default: cache by repo HEAD"),
    "Glob": ("reuse_cached", "Glob tool default: cache by repo HEAD"),
    "WebFetch": ("reuse_cached", "WebFetch tool default: cache 24h TTL"),
    "WebSearch": ("reuse_cached", "WebSearch tool default: cache 24h TTL"),
    "Edit": ("restore_checkpoint", "Edit tool default: file mutation"),
    "Write": ("restore_checkpoint", "Write tool default: file mutation"),
    "MultiEdit": ("restore_checkpoint", "MultiEdit tool default: file mutation"),
    "TodoWrite": ("rerun", "TodoWrite tool default: cheap boundary marker"),
    "Task": ("unknown", "Task subagent default: conservative"),
}


@dataclass(frozen=True)
class ClassificationResult:
    """Pure result of classifier evaluation."""

    recovery_policy: str
    classification_reason: str
    kind: str | None = None
    idempotency_key: str | None = None


def classify(tool_name: str, tool_input: dict[str, Any] | None) -> ClassificationResult:
    """Classify a tool invocation from a PreToolUse hook payload."""
    if not tool_name:
        return ClassificationResult(
            recovery_policy="unknown",
            classification_reason="empty tool_name; no rule matched",
        )

    if tool_name == "Bash":
        from runback_server.classifier.bash import classify_bash

        command = ""
        if tool_input is not None:
            command = tool_input.get("command") or ""
        return classify_bash(command)

    if tool_name in _TOOL_DEFAULTS:
        policy, reason = _TOOL_DEFAULTS[tool_name]
        return ClassificationResult(
            recovery_policy=policy,
            classification_reason=reason,
        )

    return ClassificationResult(
        recovery_policy="unknown",
        classification_reason=f"no rule for tool {tool_name!r}; manual override required",
    )
