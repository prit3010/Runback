"""Factories for synthetic Claude hook payloads."""
from __future__ import annotations

import uuid
from typing import Any


def _session() -> str:
    return str(uuid.uuid4())


def user_prompt_submit(
    *,
    session_id: str | None = None,
    prompt: str = "Fix the bug",
    cwd: str = "/tmp/sandbox",
) -> dict[str, Any]:
    return {
        "session_id": session_id or _session(),
        "hook_event_name": "UserPromptSubmit",
        "cwd": cwd,
        "prompt": prompt,
    }


def pre_tool_use(
    *,
    session_id: str,
    tool_name: str,
    tool_use_id: str | None = None,
    tool_input: dict[str, Any] | None = None,
    cwd: str = "/tmp/sandbox",
) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "hook_event_name": "PreToolUse",
        "cwd": cwd,
        "tool_name": tool_name,
        "tool_use_id": tool_use_id or f"toolu_{uuid.uuid4().hex[:24]}",
        "tool_input": tool_input or {},
    }


def post_tool_use(
    *,
    session_id: str,
    tool_name: str,
    tool_use_id: str,
    stdout: str = "",
    stderr: str = "",
    interrupted: bool = False,
    persisted_output_path: str | None = None,
    persisted_output_size: int | None = None,
    cwd: str = "/tmp/sandbox",
    tool_input: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "stdout": stdout,
        "stderr": stderr,
        "interrupted": interrupted,
        "isImage": False,
        "noOutputExpected": False,
    }
    if persisted_output_path is not None:
        response["persistedOutputPath"] = persisted_output_path
        response["persistedOutputSize"] = persisted_output_size or len(stdout)
    return {
        "session_id": session_id,
        "hook_event_name": "PostToolUse",
        "cwd": cwd,
        "tool_name": tool_name,
        "tool_use_id": tool_use_id,
        "tool_input": tool_input or {},
        "tool_response": response,
    }


def post_tool_use_failure(
    *,
    session_id: str,
    tool_name: str,
    tool_use_id: str,
    error: str = "boom",
    cwd: str = "/tmp/sandbox",
) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "hook_event_name": "PostToolUseFailure",
        "cwd": cwd,
        "tool_name": tool_name,
        "tool_use_id": tool_use_id,
        "tool_input": {},
        "tool_response": {
            "stdout": "",
            "stderr": error,
            "interrupted": True,
            "isImage": False,
            "noOutputExpected": False,
        },
    }


def todowrite_pre(
    *,
    session_id: str,
    todos: list[dict[str, Any]],
    tool_use_id: str | None = None,
    cwd: str = "/tmp/sandbox",
) -> dict[str, Any]:
    return pre_tool_use(
        session_id=session_id,
        tool_name="TodoWrite",
        tool_use_id=tool_use_id,
        tool_input={"todos": todos},
        cwd=cwd,
    )


def stop(*, session_id: str, cwd: str = "/tmp/sandbox") -> dict[str, Any]:
    return {
        "session_id": session_id,
        "hook_event_name": "Stop",
        "cwd": cwd,
    }


def stop_failure(
    *,
    session_id: str,
    cwd: str = "/tmp/sandbox",
    reason: str = "session ended unexpectedly",
) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "hook_event_name": "StopFailure",
        "cwd": cwd,
        "extra": {"reason": reason},
    }


def todos(*items: tuple[str, str]) -> list[dict[str, Any]]:
    """Build a TodoWrite todos array from (content, status) pairs."""
    return [
        {"content": content, "status": status, "activeForm": content}
        for content, status in items
    ]
