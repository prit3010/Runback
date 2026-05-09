"""`runback init` command."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import click

from runback.config import get_settings, hooks_bin_dir
from runback.runner.hooks_setup import install_forwarder, install_settings_local


@click.command("init")
def init() -> None:
    """Initialize Runback hooks in the current git repo."""
    cwd = Path.cwd()
    if not _is_git_repo(cwd):
        click.secho("error: current directory is not a git repository", fg="red", err=True)
        sys.exit(2)

    settings = get_settings()
    forwarder = install_forwarder(bin_dir=hooks_bin_dir(settings))
    settings_path = install_settings_local(workspace=cwd)
    if shutil.which("claude") is None:
        click.secho("warning: `claude` not found on PATH", fg="yellow", err=True)
    click.secho(f"forwarder installed: {forwarder}", fg="green")
    click.secho(f"hook config written: {settings_path}", fg="green")


def _is_git_repo(path: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--git-dir"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0
