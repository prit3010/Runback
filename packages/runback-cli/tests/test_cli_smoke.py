"""Smoke test every documented subcommand."""
from __future__ import annotations

from click.testing import CliRunner
from runback.__main__ import cli


def test_root_help():
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    for subcommand in ("init", "dev", "claude", "replay", "runner"):
        assert subcommand in result.output


def test_subcommand_helps():
    runner = CliRunner()
    for subcommand in ("init", "dev", "claude", "replay", "runner"):
        result = runner.invoke(cli, [subcommand, "--help"])
        assert result.exit_code == 0, f"{subcommand} --help failed: {result.output}"


def test_each_subcommand_stub_exits_nonzero_when_invoked():
    runner = CliRunner()
    for subcommand in ("init", "dev", "runner"):
        result = runner.invoke(cli, [subcommand])
        assert result.exit_code != 0
        assert "Not implemented" in result.output


def test_claude_requires_prompt():
    result = CliRunner().invoke(cli, ["claude"])
    assert result.exit_code != 0
    assert "prompt" in result.output.lower() or "missing" in result.output.lower()


def test_replay_requires_args():
    result = CliRunner().invoke(cli, ["replay"])
    assert result.exit_code != 0
