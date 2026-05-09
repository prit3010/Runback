"""Runback CLI entrypoint."""
from __future__ import annotations

import click

from runback.commands.claude_cmd import claude as claude_cmd
from runback.commands.dev_cmd import dev as dev_cmd
from runback.commands.init_cmd import init as init_cmd
from runback.commands.replay_cmd import replay as replay_cmd
from runback.commands.runner_cmd import runner as runner_cmd


@click.group()
@click.version_option(package_name="runback-cli")
def cli() -> None:
    """Runback - checkpointing and replay for Claude Code workflows."""


cli.add_command(init_cmd)
cli.add_command(dev_cmd)
cli.add_command(claude_cmd)
cli.add_command(replay_cmd)
cli.add_command(runner_cmd)


if __name__ == "__main__":
    cli()
