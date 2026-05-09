"""Idempotency key generators per docs/contracts/policies.md."""
from __future__ import annotations

import hashlib

from runback_server.classifier.keys import (
    derive_key,
    derive_key_for_post,
    parse_curl,
    parse_gh_pr_create,
    parse_git_push,
    parse_npm_publish,
    parse_slack_post,
)


def test_imported_parse_helpers_are_callable():
    assert parse_gh_pr_create("gh pr create") == {}
    assert parse_npm_publish("npm publish") == {}
    assert parse_slack_post("slack-cli post")
    assert parse_curl("curl https://example.com")


def test_gh_pr_create_key_with_branch_and_repo():
    key = derive_key(
        kind="gh_pr_create",
        command="gh pr create --title 'fix' --body 'body'",
        cwd_repo="acme/widget",
        head_branch="fix/issue-1",
    )
    assert key == "gh:pr:acme/widget:fix/issue-1"


def test_gh_pr_create_key_falls_back_to_unknown_repo_when_missing():
    key = derive_key(kind="gh_pr_create", command="gh pr create", head_branch="fix/issue-1")
    assert key == "gh:pr:unknown/unknown:fix/issue-1"


def test_git_push_key_extracts_branch_from_command():
    parsed = parse_git_push("git push -u origin fix/issue-1")
    assert parsed["remote"] == "origin"
    assert parsed["branch"] == "fix/issue-1"


def test_git_push_key_format():
    key = derive_key(
        kind="git_push",
        command="git push origin fix/issue-1",
        cwd_repo="acme/widget",
        head_sha="abc1234",
    )
    assert key == "git:push:acme/widget:fix/issue-1:abc1234"


def test_git_push_key_no_branch_arg_uses_head():
    key = derive_key(
        kind="git_push",
        command="git push",
        cwd_repo="acme/widget",
        head_sha="abc1234",
    )
    assert key == "git:push:acme/widget:HEAD:abc1234"


def test_slack_post_key_includes_channel_and_message_hash():
    expected_hash = hashlib.sha256(b"hello world").hexdigest()
    key = derive_key(kind="slack_post", command="slack-cli post --channel growth -m 'hello world'")
    assert key == f"slack:#growth:{expected_hash}"


def test_slack_post_key_handles_hash_prefix_idempotently():
    key1 = derive_key(kind="slack_post", command="slack-cli post --channel growth -m 'hi'")
    key2 = derive_key(kind="slack_post", command="slack-cli post --channel '#growth' -m 'hi'")
    assert key1 == key2


def test_npm_publish_key_uses_package_and_version():
    key = derive_key(
        kind="npm_publish",
        command="npm publish",
        package_name="my-package",
        package_version="1.2.3",
    )
    assert key == "npm:my-package:1.2.3"


def test_npm_publish_key_unknown_when_missing_meta():
    assert derive_key(kind="npm_publish", command="npm publish") == "npm:unknown:unknown"


def test_vercel_deploy_key_format():
    key = derive_key(
        kind="vercel_deploy",
        command="vercel deploy --prod",
        project="myapp",
        head_sha="abc1234",
    )
    assert key == "vercel:myapp:abc1234"


def test_gh_issue_comment_key_includes_body_hash():
    body = "Fixed by #42"
    expected_hash = hashlib.sha256(body.encode()).hexdigest()
    key = derive_key(
        kind="gh_issue_comment",
        command=f"gh issue comment 42 -b '{body}'",
        cwd_repo="acme/widget",
    )
    assert key == f"gh:issue:acme/widget:42:{expected_hash}"


def test_http_post_key_format():
    body = '{"a":1}'
    expected_hash = hashlib.sha256(body.encode()).hexdigest()
    key = derive_key(
        kind="http_post",
        command=f"curl -X POST https://example.com/api/v1/things -d '{body}'",
    )
    assert key == f"http:post:example.com:/api/v1/things:{expected_hash}"


def test_http_put_key_format():
    body = "x=1"
    expected_hash = hashlib.sha256(body.encode()).hexdigest()
    key = derive_key(
        kind="http_put",
        command=f"curl -X PUT https://api.example.com/foo -d '{body}'",
    )
    assert key == f"http:put:api.example.com:/foo:{expected_hash}"


def test_http_post_no_body_uses_empty_hash():
    expected_hash = hashlib.sha256(b"").hexdigest()
    key = derive_key(kind="http_post", command="curl -X POST https://example.com/api")
    assert key == f"http:post:example.com:/api:{expected_hash}"


def test_unknown_kind_returns_fallback_key():
    assert derive_key(kind="weird_thing", command="echo hi").startswith("unknown:weird_thing:")


def test_derive_key_for_post_uses_pre_key_when_complete():
    pre_key = "git:push:acme/widget:fix/x:abc1234"
    out = derive_key_for_post(
        kind="git_push",
        pre_key=pre_key,
        command="git push origin fix/x",
        tool_response_stdout="To github.com:acme/widget.git\n   abc1234..def5678  fix/x -> fix/x",
    )
    assert out == pre_key
