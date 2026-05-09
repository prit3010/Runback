"""`runback runner` command."""
from __future__ import annotations

import signal

import anyio
import click

from runback.runner.daemon import RunnerDaemon


@click.command("runner")
def runner() -> None:
    """Start the runner daemon."""
    daemon = RunnerDaemon()

    async def main() -> None:
        async with anyio.create_task_group() as tg:
            tg.start_soon(daemon.serve_forever)
            with anyio.open_signal_receiver(signal.SIGINT, signal.SIGTERM) as signals:
                async for sig in signals:
                    click.secho(f"received {sig.name}, shutting down", fg="yellow", err=True)
                    await daemon.stop()
                    tg.cancel_scope.cancel()
                    return

    anyio.run(main)
