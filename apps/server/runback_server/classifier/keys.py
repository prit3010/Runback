"""Idempotency key generators per docs/contracts/policies.md."""
from __future__ import annotations

import hashlib
import re
import shlex
from urllib.parse import urlparse


def _safe_shlex(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def parse_git_push(command: str) -> dict[str, str]:
    """Extract remote and branch from common git push command shapes."""
    tokens = _safe_shlex(command)
    raw_args = tokens[2:] if len(tokens) >= 2 else []
    args: list[str] = []
    skip_next = False
    for arg in raw_args:
        if skip_next:
            skip_next = False
            continue
        if arg in {"-u", "--set-upstream"}:
            continue
        if arg.startswith("--"):
            if "=" not in arg:
                skip_next = False
            continue
        if arg.startswith("-"):
            continue
        args.append(arg)
    remote = args[0] if len(args) >= 1 else "origin"
    branch = args[1] if len(args) >= 2 else "HEAD"
    return {"remote": remote, "branch": branch}


def parse_gh_pr_create(command: str) -> dict[str, str]:
    return {}


def parse_npm_publish(command: str) -> dict[str, str]:
    return {}


_SLACK_CHANNEL = re.compile(r"--channel(?:\s+|=)([^\s]+)")
_SLACK_MESSAGE = re.compile(r"-m\s+(?:'([^']*)'|\"([^\"]*)\"|(\S+))")


def parse_slack_post(command: str) -> dict[str, str]:
    channel = "unknown"
    channel_match = _SLACK_CHANNEL.search(command)
    if channel_match:
        raw = channel_match.group(1).strip().strip("'").strip('"')
        channel = raw if raw.startswith("#") else f"#{raw}"

    message = ""
    message_match = _SLACK_MESSAGE.search(command)
    if message_match:
        message = message_match.group(1) or message_match.group(2) or message_match.group(3) or ""

    return {"channel": channel, "message": message}


_GH_ISSUE_NUM = re.compile(r"^gh\s+issue\s+(?:comment|close)\s+(\d+)")
_GH_ISSUE_BODY = re.compile(r"-b\s+(?:'([^']*)'|\"([^\"]*)\"|(\S+))")


def parse_gh_issue_comment(command: str) -> dict[str, str]:
    issue = "0"
    body = ""
    issue_match = _GH_ISSUE_NUM.match(command)
    if issue_match:
        issue = issue_match.group(1)
    body_match = _GH_ISSUE_BODY.search(command)
    if body_match:
        body = body_match.group(1) or body_match.group(2) or body_match.group(3) or ""
    return {"issue": issue, "body": body}


_CURL_URL = re.compile(r"\bhttps?://[^\s'\"]+")
_CURL_DATA = re.compile(
    r"(?:^|\s)(?:-d|--data|--data-binary|--data-raw)\s+"
    r"(?:'([^']*)'|\"([^\"]*)\"|(\S+))"
)


def parse_curl(command: str) -> dict[str, str]:
    url_match = _CURL_URL.search(command)
    parsed = urlparse(url_match.group(0)) if url_match else None
    host = parsed.hostname if parsed and parsed.hostname else "unknown"
    path = parsed.path if parsed and parsed.path else "/"
    data_match = _CURL_DATA.search(command)
    body = ""
    if data_match:
        body = data_match.group(1) or data_match.group(2) or data_match.group(3) or ""
    return {"host": host, "path": path, "body": body}


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def derive_key(
    *,
    kind: str,
    command: str,
    cwd_repo: str | None = None,
    head_sha: str | None = None,
    head_branch: str | None = None,
    package_name: str | None = None,
    package_version: str | None = None,
    project: str | None = None,
) -> str:
    """Return a stable idempotency key for a classified side-effect command."""
    if kind == "gh_pr_create":
        return f"gh:pr:{cwd_repo or 'unknown/unknown'}:{head_branch or 'HEAD'}"

    if kind == "git_push":
        parsed = parse_git_push(command)
        branch = parsed["branch"] if parsed["branch"] != "HEAD" else (head_branch or "HEAD")
        return f"git:push:{cwd_repo or 'unknown/unknown'}:{branch}:{head_sha or 'unknown'}"

    if kind == "gh_issue_comment":
        parsed = parse_gh_issue_comment(command)
        body_hash = _sha256(parsed["body"])
        return f"gh:issue:{cwd_repo or 'unknown/unknown'}:{parsed['issue']}:{body_hash}"

    if kind == "gh_issue_close":
        parsed = parse_gh_issue_comment(command)
        return f"gh:issue:{cwd_repo or 'unknown/unknown'}:gh_issue_close:{parsed['issue']}"

    if kind == "gh_issue_create":
        return f"gh:issue:{cwd_repo or 'unknown/unknown'}:gh_issue_create:{_sha256(command)}"

    if kind == "slack_post":
        parsed = parse_slack_post(command)
        return f"slack:{parsed['channel']}:{_sha256(parsed['message'])}"

    if kind == "npm_publish":
        return f"npm:{package_name or 'unknown'}:{package_version or 'unknown'}"

    if kind == "pip_publish":
        return f"pip:{package_name or 'unknown'}:{package_version or 'unknown'}"

    if kind == "vercel_deploy":
        return f"vercel:{project or 'unknown'}:{head_sha or 'unknown'}"

    if kind == "docker_push":
        tokens = _safe_shlex(command)
        image = tokens[2] if len(tokens) >= 3 else "unknown"
        return f"docker:{image}"

    if kind == "terraform_apply":
        return f"terraform:apply:{cwd_repo or 'unknown'}:{head_sha or _sha256(command)}"

    if kind == "kubectl_apply":
        return f"kubectl:apply:{_sha256(command)}"

    if kind in {"http_post", "http_put", "http_patch", "http_delete"}:
        parsed = parse_curl(command)
        method = kind.split("_", 1)[1]
        return f"http:{method}:{parsed['host']}:{parsed['path']}:{_sha256(parsed['body'])}"

    return f"unknown:{kind}:{_sha256(command)}"


def derive_key_for_post(
    *,
    kind: str,
    pre_key: str,
    command: str,
    tool_response_stdout: str | None = None,
) -> str:
    """Return the final PostToolUse key. MVP keeps the PreToolUse key stable."""
    return pre_key
