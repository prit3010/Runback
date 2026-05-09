"""Resume prompt template renders with all documented variables."""
from __future__ import annotations

from pathlib import Path

import jinja2
import pytest

TEMPLATE = (
    Path(__file__).resolve().parents[1]
    / "runback_server"
    / "replay"
    / "templates"
    / "resume.md.j2"
)


@pytest.fixture
def env():
    loader = jinja2.FileSystemLoader(str(TEMPLATE.parent))
    return jinja2.Environment(loader=loader, autoescape=False, trim_blocks=True, lstrip_blocks=True)


def test_template_renders_with_documented_vars(env):
    tpl = env.get_template("resume.md.j2")
    out = tpl.render(
        original_prompt="Fix all bugs in BACKLOG.md",
        completed_groups=[
            {"label": "Ticket #1", "status": "success", "external_refs": ["PR-101"]},
            {"label": "Ticket #2", "status": "success", "external_refs": ["PR-102"]},
        ],
        cached_artifacts=[
            {"description": "Repo scan", "path": ".runback/.../grep_1/output.txt"},
            {"description": "BACKLOG.md contents", "path": ".runback/.../read_1/output.txt"},
        ],
        checkpoint_label="checkpoint_pre_edit_4",
        failed_node_label="Bash: npm test",
        failure_output="FAIL src/auth/token.test.ts\n  ...",
        already_executed_side_effects=[
            {
                "kind": "gh_pr_create",
                "external_ref": "https://github.com/x/y/pull/1",
                "key": "gh:pr:x/y:fix/issue-1",
            },
        ],
        user_context="The regression is in token refresh logic",
        scope_instruction=(
            "Continue ONLY with ticket 4. After ticket 4 succeeds, continue to ticket 5."
        ),
    )
    assert "Fix all bugs in BACKLOG.md" in out
    assert "checkpoint_pre_edit_4" in out
    assert "Bash: npm test" in out
    assert "regression is in token refresh logic" in out
    assert "PR-101" in out
    assert "Continue ONLY with ticket 4" in out
    assert "ALREADY EXECUTED" in out


def test_template_renders_with_minimum_vars(env):
    tpl = env.get_template("resume.md.j2")
    out = tpl.render(
        original_prompt="do thing",
        completed_groups=[],
        cached_artifacts=[],
        checkpoint_label="cp_0",
        failed_node_label="x",
        failure_output="",
        already_executed_side_effects=[],
        user_context=None,
        scope_instruction=None,
    )
    assert "do thing" in out
    assert "cp_0" in out
