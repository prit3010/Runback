from __future__ import annotations

import json

from runback_server.ingest.archive import (
    EventArchive,
    compute_event_key,
    is_duplicate_key,
    record_event_key,
)


def test_compute_event_key_stable():
    payload = {
        "session_id": "s1",
        "hook_event_name": "PreToolUse",
        "tool_use_id": "t1",
        "cwd": "/tmp",
        "tool_name": "Read",
    }
    assert compute_event_key("run_1", payload) == compute_event_key("run_1", payload)


def test_compute_event_key_differs_on_distinct_payloads():
    first = compute_event_key(
        "run_1", {"session_id": "s1", "hook_event_name": "Pre", "tool_use_id": "t1"}
    )
    second = compute_event_key(
        "run_1", {"session_id": "s1", "hook_event_name": "Post", "tool_use_id": "t1"}
    )
    assert first != second


def test_compute_event_key_differs_across_runs():
    payload = {"session_id": "s1", "hook_event_name": "Pre", "tool_use_id": "t1"}
    assert compute_event_key("run_1", payload) != compute_event_key("run_2", payload)


def test_dedup_seen_keys(tmp_path):
    archive = EventArchive(run_id="run_1", root=tmp_path)
    payload = {
        "session_id": "s",
        "hook_event_name": "PreToolUse",
        "tool_use_id": "t1",
        "cwd": "/tmp",
        "tool_name": "Read",
    }
    key = compute_event_key("run_1", payload)
    assert not is_duplicate_key(archive, key)
    record_event_key(archive, key)
    assert is_duplicate_key(archive, key)


def test_archive_appends_jsonl(tmp_path):
    archive = EventArchive(run_id="run_1", root=tmp_path)
    archive.append({"session_id": "s", "hook_event_name": "PreToolUse"})
    archive.append({"session_id": "s", "hook_event_name": "PostToolUse"})
    path = tmp_path / "runs" / "run_1" / "events.jsonl"
    assert path.exists()
    lines = path.read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["hook_event_name"] == "PreToolUse"
    assert json.loads(lines[1])["hook_event_name"] == "PostToolUse"


def test_archive_creates_parent_dirs(tmp_path):
    archive = EventArchive(run_id="run_xyz", root=tmp_path)
    archive.append({"hook_event_name": "X"})
    assert (tmp_path / "runs" / "run_xyz" / "events.jsonl").exists()
