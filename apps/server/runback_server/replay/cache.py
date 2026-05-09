"""Cache validity checks for replay reuse decisions."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlmodel import Session, select

from runback_server.models import Artifact, NodeArtifactEdge

_DEFAULT_TTL_HOURS = 24
_HASH_CHUNK = 1024 * 1024


@dataclass
class CacheValidity:
    valid: bool
    reason: str = ""


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(_HASH_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def is_artifact_valid(artifact: Artifact) -> CacheValidity:
    if artifact.path:
        path = Path(artifact.path).expanduser()
        if not path.exists():
            return CacheValidity(False, f"file missing at {path}")
        if not artifact.content_hash:
            return CacheValidity(True, "no content_hash recorded; trusting")
        actual = _hash_file(path)
        if actual != artifact.content_hash:
            return CacheValidity(
                False,
                f"content hash mismatch (expected {artifact.content_hash[:8]}, got {actual[:8]})",
            )
        return CacheValidity(True, "hash matches")

    if artifact.source_url:
        ttl_hours = _DEFAULT_TTL_HOURS
        if isinstance(artifact.cache_policy_json, dict):
            ttl_hours = int(artifact.cache_policy_json.get("ttl_hours", _DEFAULT_TTL_HOURS))
        created = artifact.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        age = datetime.now(UTC) - created
        if age > timedelta(hours=ttl_hours):
            return CacheValidity(False, f"ttl expired ({age.total_seconds() / 3600:.1f}h)")
        return CacheValidity(True, "within ttl")

    return CacheValidity(True, "no path or url; trusted")


def validate_reuse_candidates(
    session: Session,
    *,
    run_id: str,
    candidate_node_ids: list[str],
) -> tuple[list[str], list[str]]:
    if not candidate_node_ids:
        return [], []

    edges = session.exec(
        select(NodeArtifactEdge).where(
            NodeArtifactEdge.run_id == run_id,
            NodeArtifactEdge.node_id.in_(candidate_node_ids),  # type: ignore[attr-defined]
            NodeArtifactEdge.direction == "output",
        )
    ).all()
    by_node: dict[str, list[str]] = {}
    for edge in edges:
        by_node.setdefault(edge.node_id, []).append(edge.artifact_id)

    artifact_ids = {artifact_id for ids in by_node.values() for artifact_id in ids}
    artifacts: dict[str, Artifact] = {}
    if artifact_ids:
        rows = session.exec(select(Artifact).where(Artifact.id.in_(artifact_ids))).all()  # type: ignore[attr-defined]
        artifacts = {artifact.id: artifact for artifact in rows}

    valid: list[str] = []
    invalid: list[str] = []
    for node_id in candidate_node_ids:
        outputs = by_node.get(node_id, [])
        if not outputs:
            valid.append(node_id)
            continue
        all_ok = all(
            artifact_id in artifacts and is_artifact_valid(artifacts[artifact_id]).valid
            for artifact_id in outputs
        )
        (valid if all_ok else invalid).append(node_id)
    return valid, invalid
