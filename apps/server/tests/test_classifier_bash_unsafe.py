"""Bash matrix: unsafe band."""
from __future__ import annotations

import pytest
from runback_server.classifier.bash import classify_bash


@pytest.mark.parametrize(
    "command",
    [
        "rm -rf",
        "rm -rf node_modules",
        "rm -rf /tmp/foo",
        "git reset --hard",
        "git reset --hard HEAD~1",
        "git reset --hard origin/main",
        "git clean -fd",
        "dropdb",
        "dropdb mydb",
        "terraform destroy",
        "terraform destroy -auto-approve",
        "kubectl delete",
        "kubectl delete pod foo",
    ],
)
def test_unsafe_commands(command: str):
    result = classify_bash(command)
    assert result.recovery_policy == "unsafe"
    assert result.kind is None
    assert result.idempotency_key is None
    assert result.classification_reason
