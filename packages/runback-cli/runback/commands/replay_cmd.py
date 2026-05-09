"""`runback replay` command."""
from __future__ import annotations

import sys

import click
import httpx

from runback.config import get_settings


@click.command("replay")
@click.argument("run_id", required=True)
@click.argument("node_id", required=True)
@click.option("--context", "user_context", default=None, help="Free-form replay steering text.")
def replay(run_id: str, node_id: str, user_context: str | None) -> None:
    """Replay a failed run from the nearest safe checkpoint of NODE_ID."""
    settings = get_settings()
    body = {"node_id": node_id}
    if user_context:
        body["user_context"] = user_context
    try:
        with httpx.Client(base_url=settings.backend_url, timeout=15.0) as client:
            response = client.post(f"/api/runs/{run_id}/replay", json=body)
    except httpx.HTTPError as exc:
        click.secho(f"error: cannot reach backend: {exc}", fg="red", err=True)
        sys.exit(2)
    if response.status_code not in (200, 202):
        click.secho(
            f"error: backend returned {response.status_code}: {response.text}",
            fg="red",
            err=True,
        )
        sys.exit(1)
    payload = response.json()
    click.secho(f"replay attempt created on branch {payload.get('new_branch_id')}", fg="green")
