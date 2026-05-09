"""Bash command classifier implementing docs/contracts/policies.md."""
from __future__ import annotations

import re

from runback_server.classifier.rules import ClassificationResult

_RERUN_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"^(npm|pnpm|yarn)\s+"
            r"(test|run\s+test|run\s+build|run\s+lint|run\s+typecheck)\b"
        ),
        "node test/build/lint command",
    ),
    (re.compile(r"^pytest\b"), "pytest"),
    (re.compile(r"^tsc\b"), "tsc"),
    (re.compile(r"^eslint\b"), "eslint"),
    (re.compile(r"^ruff\b"), "ruff"),
    (re.compile(r"^cargo\s+(test|build|check)\b"), "cargo test/build/check"),
    (re.compile(r"^go\s+(test|build)\b"), "go test/build"),
    (re.compile(r"^make\s+(test|build|lint)\b"), "make test/build/lint"),
]

_APPROVAL_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"^git\s+push\b"), "git_push", "git push: pushes commits to remote"),
    (re.compile(r"^gh\s+pr\s+create\b"), "gh_pr_create", "gh pr create: opens a pull request"),
    (
        re.compile(r"^gh\s+issue\s+comment\b"),
        "gh_issue_comment",
        "gh issue comment: posts to issue",
    ),
    (re.compile(r"^gh\s+issue\s+close\b"), "gh_issue_close", "gh issue close: closes issue"),
    (re.compile(r"^gh\s+issue\s+create\b"), "gh_issue_create", "gh issue create: creates issue"),
    (re.compile(r"^npm\s+publish\b"), "npm_publish", "npm publish: publishes package"),
    (re.compile(r"^pip\s+publish\b"), "pip_publish", "pip publish: publishes package"),
    (re.compile(r"^vercel\s+deploy\b"), "vercel_deploy", "vercel deploy: deploys to Vercel"),
    (re.compile(r"^docker\s+push\b"), "docker_push", "docker push: pushes image"),
    (re.compile(r"^terraform\s+apply\b"), "terraform_apply", "terraform apply: mutates infra"),
    (re.compile(r"^kubectl\s+apply\b"), "kubectl_apply", "kubectl apply: mutates cluster"),
    (re.compile(r"^slack-cli\s+post\b"), "slack_post", "slack-cli post: posts message"),
]

_CURL_METHOD = re.compile(r"^curl\b.*\s-X\s+(POST|PUT|PATCH|DELETE)\b")

_UNSAFE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^rm\s+-rf\b"), "rm -rf: recursive force delete"),
    (re.compile(r"^git\s+reset\s+--hard\b"), "git reset --hard: discards work"),
    (re.compile(r"^git\s+clean\s+-fd\b"), "git clean -fd: removes untracked files"),
    (re.compile(r"^dropdb\b"), "dropdb: drops database"),
    (re.compile(r"^terraform\s+destroy\b"), "terraform destroy: destroys infra"),
    (re.compile(r"^kubectl\s+delete\b"), "kubectl delete: removes resource"),
]


def classify_bash(command: str) -> ClassificationResult:
    """Classify a raw Bash command string."""
    cmd = (command or "").lstrip()
    if not cmd:
        return ClassificationResult(
            recovery_policy="unknown",
            classification_reason="empty bash command; no rule matched",
        )

    for pattern, reason in _RERUN_PATTERNS:
        if pattern.match(cmd):
            return ClassificationResult(
                recovery_policy="rerun",
                classification_reason=f"bash rerun: {reason}",
            )

    for pattern, kind, reason in _APPROVAL_PATTERNS:
        if pattern.match(cmd):
            return ClassificationResult(
                recovery_policy="requires_approval",
                classification_reason=f"bash side-effect: {reason}",
                kind=kind,
            )

    method_match = _CURL_METHOD.match(cmd)
    if method_match:
        method = method_match.group(1).lower()
        return ClassificationResult(
            recovery_policy="requires_approval",
            classification_reason=f"bash side-effect: curl HTTP {method.upper()}",
            kind=f"http_{method}",
        )

    for pattern, reason in _UNSAFE_PATTERNS:
        if pattern.match(cmd):
            return ClassificationResult(
                recovery_policy="unsafe",
                classification_reason=f"bash unsafe: {reason}",
            )

    return ClassificationResult(
        recovery_policy="unknown",
        classification_reason="bash command did not match any matrix rule",
    )
