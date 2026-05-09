"""Bash matrix: no match."""
from __future__ import annotations

import pytest
from runback_server.classifier.bash import classify_bash


@pytest.mark.parametrize(
    "command",
    [
        "ls",
        "cat README.md",
        "echo hello",
        "git status",
        "git diff",
        "git log --oneline",
        "cd /tmp",
        "mkdir foo",
        "find . -name '*.py'",
        "grep -r foo .",
        "wc -l file.txt",
        "",
        "   ",
    ],
)
def test_unknown_commands(command: str):
    result = classify_bash(command)
    assert result.recovery_policy == "unknown"
    assert result.kind is None
    assert result.idempotency_key is None


def test_curl_get_is_unknown_not_approval():
    result = classify_bash("curl -X GET https://example.com")
    assert result.recovery_policy == "unknown"


def test_curl_no_method_flag_is_unknown():
    result = classify_bash("curl https://example.com")
    assert result.recovery_policy == "unknown"
