"""ID generation and label sanitization helpers."""
from __future__ import annotations

import re

import ulid


def new_id(prefix: str) -> str:
    return f"{prefix}_{ulid.new().str}"


def run_id() -> str:
    return new_id("run")


def node_id() -> str:
    return new_id("node")


def group_id() -> str:
    return new_id("grp")


def edge_id() -> str:
    return new_id("edge")


def checkpoint_id() -> str:
    return new_id("cp")


def artifact_id() -> str:
    return new_id("art")


def branch_id() -> str:
    return new_id("branch")


def replay_id() -> str:
    return new_id("replay")


def runner_id() -> str:
    return new_id("runner")


_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]")


def sanitize_label(label: str) -> str:
    """Make a label safe enough for a filesystem path component."""
    sanitized = label.strip()
    if not sanitized:
        return "unlabeled"
    return _UNSAFE_CHARS.sub("_", sanitized)


def label_with_short_id(label: str, full_id: str) -> str:
    """Return ``<sanitized-label>_<last-6-chars-of-id>``."""
    return f"{sanitize_label(label)}_{full_id[-6:].lower()}"
