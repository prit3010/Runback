"""Verify hook event schemas parse captured spike payloads."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from runback_server.schemas.hook_events import parse_hook_event

SPIKES = Path(__file__).resolve().parents[3] / ".spikes" / "payloads"


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def test_pretooluse_todowrite_parses():
    files = list(SPIKES.glob("oq1-*/pre-*.json"))
    assert files, "OQ1 spike payloads not found"
    for file in files:
        evt = parse_hook_event(_load(file))
        assert evt.hook_event_name == "PreToolUse"
        assert evt.tool_name == "TodoWrite"
        assert evt.session_id
        assert evt.cwd
        assert evt.tool_input is not None
        assert "todos" in evt.tool_input


def test_posttooluse_bash_parses_and_extracts_persisted_path():
    files = list(SPIKES.glob("oq4-*/post-*.json"))
    assert files, "OQ4 spike payloads not found"
    evt = parse_hook_event(_load(files[0]))
    assert evt.hook_event_name == "PostToolUse"
    assert evt.tool_name == "Bash"
    assert evt.tool_response is not None
    assert evt.tool_response.persisted_output_path is not None
    assert evt.tool_response.persisted_output_size
    assert evt.tool_response.persisted_output_size > 30000
    assert len(evt.tool_response.stdout) <= 30000


def test_unknown_event_keeps_raw():
    raw = {
        "session_id": "s1",
        "hook_event_name": "FutureEvent",
        "cwd": "/tmp",
        "tool_name": None,
        "extra_field": "ok",
    }
    evt = parse_hook_event(raw)
    assert evt.hook_event_name == "FutureEvent"
    assert evt.extra == {"extra_field": "ok"}


def test_required_fields_missing_raises():
    with pytest.raises(ValidationError):
        parse_hook_event({})
