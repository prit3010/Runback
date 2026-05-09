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


def test_init_exits_nonzero_outside_git_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["init"])
    assert result.exit_code != 0
    assert "git" in result.output.lower()


def test_long_running_subcommands_are_not_stubs():
    runner = CliRunner()
    for subcommand in ("dev", "runner"):
        result = runner.invoke(cli, [subcommand, "--help"])
        assert result.exit_code == 0
        assert "Not implemented" not in result.output


def test_claude_requires_prompt():
    result = CliRunner().invoke(cli, ["claude"])
    assert result.exit_code != 0
    assert "prompt" in result.output.lower() or "missing" in result.output.lower()


def test_replay_requires_args():
    result = CliRunner().invoke(cli, ["replay"])
    assert result.exit_code != 0
