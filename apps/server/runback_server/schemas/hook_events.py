"""Pydantic schemas for Claude Code hook payloads."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ToolResponse(BaseModel):
    """Shape of tool_response in PostToolUse events."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    stdout: str = ""
    stderr: str = ""
    interrupted: bool = False
    is_image: bool = Field(default=False, alias="isImage")
    no_output_expected: bool = Field(default=False, alias="noOutputExpected")
    persisted_output_path: str | None = Field(default=None, alias="persistedOutputPath")
    persisted_output_size: int | None = Field(default=None, alias="persistedOutputSize")


class HookEvent(BaseModel):
    """Common shape for all Claude Code hook events."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    session_id: str
    hook_event_name: str
    cwd: str
    transcript_path: str | None = None
    permission_mode: str | None = None
    tool_name: str | None = None
    tool_use_id: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_response: ToolResponse | None = None
    prompt: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


def parse_hook_event(payload: dict[str, Any]) -> HookEvent:
    """Parse a raw hook payload, preserving unknown top-level fields on extra."""
    known = set(HookEvent.model_fields.keys())
    extra = {key: value for key, value in payload.items() if key not in known}
    payload_clean = {key: value for key, value in payload.items() if key in known}
    payload_clean["extra"] = extra
    return HookEvent.model_validate(payload_clean)
