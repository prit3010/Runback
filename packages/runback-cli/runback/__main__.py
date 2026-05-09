"""Runback CLI entrypoint."""
from __future__ import annotations

import sys

import click


@click.group()
@click.version_option(package_name="runback-cli")
def cli() -> None:
    """Runback - checkpointing and replay for Claude Code workflows."""


@cli.command()
def init() -> None:
    """Initialize Runback hooks in the current git repo."""
    click.echo("Not implemented (stub)", err=True)
    sys.exit(2)


@cli.command()
def dev() -> None:
    """Start backend, frontend, and runner daemon together."""
    click.echo("Not implemented (stub)", err=True)
    sys.exit(2)


@cli.command()
@click.argument("prompt", required=True)
def claude(prompt: str) -> None:
    """Launch a one-shot Claude Code run captured by Runback."""
    click.echo(f"Not implemented (stub) - would run: {prompt}", err=True)
    sys.exit(2)


@cli.command()
@click.argument("run_id", required=True)
@click.argument("node_id", required=True)
def replay(run_id: str, node_id: str) -> None:
    """Replay a failed run from the nearest safe checkpoint of NODE_ID."""
    click.echo(f"Not implemented (stub) - would replay {run_id} from {node_id}", err=True)
    sys.exit(2)


@cli.command()
def runner() -> None:
    """Start the runner daemon."""
    click.echo("Not implemented (stub)", err=True)
    sys.exit(2)


if __name__ == "__main__":
    cli()
