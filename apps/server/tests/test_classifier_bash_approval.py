"""Bash matrix: requires_approval band."""
from __future__ import annotations

import pytest
from runback_server.classifier.bash import classify_bash


@pytest.mark.parametrize(
    "command,expected_kind",
    [
        ("git push", "git_push"),
        ("git push origin main", "git_push"),
        ("git push -u origin fix/branch", "git_push"),
        ("gh pr create", "gh_pr_create"),
        ("gh pr create --title 'fix' --body 'b'", "gh_pr_create"),
        ("gh issue comment 42 -b 'hello'", "gh_issue_comment"),
        ("gh issue close 42", "gh_issue_close"),
        ("gh issue create --title 'x'", "gh_issue_create"),
        ("npm publish", "npm_publish"),
        ("npm publish --access=public", "npm_publish"),
        ("pip publish", "pip_publish"),
        ("vercel deploy", "vercel_deploy"),
        ("vercel deploy --prod", "vercel_deploy"),
        ("docker push", "docker_push"),
        ("docker push myimg:tag", "docker_push"),
        ("terraform apply", "terraform_apply"),
        ("terraform apply -auto-approve", "terraform_apply"),
        ("kubectl apply", "kubectl_apply"),
        ("kubectl apply -f deploy.yaml", "kubectl_apply"),
        ("slack-cli post", "slack_post"),
        ("slack-cli post --channel growth -m 'hi'", "slack_post"),
        ("curl -X POST https://example.com/api", "http_post"),
        ("curl -X PUT https://example.com/api", "http_put"),
        ("curl -X PATCH https://example.com/api", "http_patch"),
        ("curl -X DELETE https://example.com/api", "http_delete"),
        ("curl -fsS -X POST https://example.com/api -d @-", "http_post"),
    ],
)
def test_requires_approval_commands(command: str, expected_kind: str):
    result = classify_bash(command)
    assert result.recovery_policy == "requires_approval"
    assert result.kind == expected_kind
    assert result.classification_reason
