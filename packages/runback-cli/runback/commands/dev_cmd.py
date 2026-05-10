"""`runback dev` command."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time

import click

from runback.config import get_settings


@click.command("dev")
@click.option("--no-web", is_flag=True, help="Skip starting the web dev server.")
@click.option("--no-server", is_flag=True, help="Skip starting the FastAPI backend.")
@click.option("--no-runner", is_flag=True, help="Skip starting the runner daemon.")
def dev(no_web: bool, no_server: bool, no_runner: bool) -> None:
    """Start backend, frontend, and runner daemon together."""
    settings = get_settings()
    procs: list[tuple[str, subprocess.Popen]] = []
    if not no_server:
        click.secho("preparing backend database", fg="cyan")
        migration = subprocess.run(
            ["uv", "run", "--extra", "dev", "alembic", "upgrade", "head"],
            cwd="apps/server",
            env=os.environ.copy(),
        )
        if migration.returncode != 0:
            raise click.ClickException("backend database migration failed")
        click.secho(f"starting backend on port {settings.server_port}", fg="cyan")
        procs.append(
            (
                "server",
                subprocess.Popen(
                    [
                        "uv",
                        "run",
                        "uvicorn",
                        "runback_server.main:app",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(settings.server_port),
                        "--reload",
                    ],
                    cwd="apps/server",
                    env=os.environ.copy(),
                ),
            )
        )
    if not no_web:
        click.secho(f"starting web on port {settings.web_port}", fg="cyan")
        procs.append(
            (
                "web",
                subprocess.Popen(
                    ["corepack", "pnpm", "exec", "next", "dev", "-p", str(settings.web_port)],
                    cwd="apps/web",
                    env={**os.environ, "PORT": str(settings.web_port)},
                ),
            )
        )
    if not no_runner:
        click.secho("starting runner daemon", fg="cyan")
        procs.append(("runner", subprocess.Popen([sys.executable, "-m", "runback"] + ["runner"])))

    click.secho("all up. Ctrl-C to stop.", fg="green")
    try:
        while procs:
            for item in list(procs):
                name, proc = item
                rc = proc.poll()
                if rc is not None:
                    click.secho(f"[{name}] exited with code {rc}", fg="red")
                    procs.remove(item)
            time.sleep(0.5)
    except KeyboardInterrupt:
        click.secho("shutting down", fg="yellow")
    finally:
        for _, proc in procs:
            try:
                proc.send_signal(signal.SIGINT)
            except ProcessLookupError:
                pass
        for _, proc in procs:
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
