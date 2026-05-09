"""Bash matrix: rerun band."""
from __future__ import annotations

import pytest
from runback_server.classifier.bash import classify_bash


@pytest.mark.parametrize(
    "command",
    [
        "npm test",
        "npm run test",
        "npm run build",
        "npm run lint",
        "npm run typecheck",
        "pnpm test",
        "pnpm run test",
        "pnpm run build",
        "pnpm run lint",
        "pnpm run typecheck",
        "yarn test",
        "yarn run test",
        "yarn run build",
        "yarn run lint",
        "yarn run typecheck",
        "pytest",
        "pytest -v",
        "pytest tests/",
        "tsc",
        "tsc --noEmit",
        "eslint",
        "eslint src/",
        "ruff",
        "ruff check .",
        "cargo test",
        "cargo build",
        "cargo check",
        "go test",
        "go test ./...",
        "go build",
        "make test",
        "make build",
        "make lint",
    ],
)
def test_rerun_commands(command: str):
    result = classify_bash(command)
    assert result.recovery_policy == "rerun"
    assert result.kind is None
    assert result.idempotency_key is None
    assert result.classification_reason
