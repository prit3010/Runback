"""Manual recovery-policy overrides for individual Nodes."""
from __future__ import annotations

from sqlmodel import Session

from runback_server.models import Node

VALID_POLICIES: frozenset[str] = frozenset(
    {
        "rerun",
        "reuse_cached",
        "restore_checkpoint",
        "requires_approval",
        "unsafe",
        "unknown",
    }
)

_OVERRIDE_PREFIX = "[OVERRIDE]"


class OverrideError(ValueError):
    """Raised when an override request is invalid."""


def apply_override(
    session: Session,
    node: Node,
    *,
    recovery_policy: str,
    reason: str,
) -> Node:
    """Mutate a Node with a user-supplied recovery-policy override."""
    if recovery_policy not in VALID_POLICIES:
        raise OverrideError(
            f"invalid recovery_policy {recovery_policy!r}; must be one of {sorted(VALID_POLICIES)}"
        )
    cleaned_reason = (reason or "").strip()
    if not cleaned_reason:
        raise OverrideError("reason is required and cannot be empty")

    prior = node.classification_reason or ""
    if prior.startswith(_OVERRIDE_PREFIX):
        prior = prior.split(" | ", 1)[1] if " | " in prior else ""

    node.recovery_policy = recovery_policy
    suffix = f" | {prior}" if prior else ""
    node.classification_reason = f"{_OVERRIDE_PREFIX} {cleaned_reason}{suffix}"
    session.add(node)
    return node
