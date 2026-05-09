"""Persist Claude persisted tool output into run-scoped Artifact rows."""
from __future__ import annotations

import hashlib
import shutil
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session

from runback_server.config import get_settings
from runback_server.ingest.ids import artifact_id, label_with_short_id
from runback_server.models import Artifact, Node, NodeArtifactEdge


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def maybe_copy_persisted_output(
    session: Session,
    run_id: str,
    node: Node,
    persisted_path: str | None,
    _persisted_size: int | None,
) -> Artifact | None:
    """Copy a Claude-persisted output file into the Runback runtime root."""
    if not persisted_path:
        return None

    src = Path(persisted_path)
    if not src.exists() or not src.is_file():
        return None

    settings = get_settings()
    dir_label = label_with_short_id(node.label or node.tool_name or "tool", node.id)
    dest_dir = settings.runtime_root / "runs" / run_id / "artifacts" / dir_label
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "output.txt"
    shutil.copy2(src, dest)

    artifact = Artifact(
        id=artifact_id(),
        run_id=run_id,
        node_id=node.id,
        produced_by_node_id=node.id,
        type="log",
        path=str(dest),
        description=f"Persisted output of {node.label}",
        content_preview=(node.output_preview or "")[:1024],
        content_hash=_sha256_file(dest),
        size_bytes=dest.stat().st_size,
        created_at=_now(),
    )
    session.add(artifact)
    session.flush()
    session.add(
        NodeArtifactEdge(
            id=f"nae_{artifact.id[-12:]}",
            run_id=run_id,
            node_id=node.id,
            artifact_id=artifact.id,
            direction="output",
            required=True,
            created_at=_now(),
        )
    )
    return artifact
