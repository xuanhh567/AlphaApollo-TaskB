"""Parse structured model tool calls."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field as dataclass_field
from typing import Any


@dataclass(frozen=True)
class ToolCall:
    """A structured request from the model to call one skill."""

    name: str
    arguments: dict[str, Any]
    raw_text: str | None = None


@dataclass(frozen=True)
class ToolError:
    """Structured error returned while parsing, validating, or dispatching."""

    code: str
    message: str
    tool_name: str | None = None
    field: str | None = None
    details: dict[str, Any] = dataclass_field(default_factory=dict)


TOOL_CALL_OPEN_RE = re.compile(r"<tool_call>", re.IGNORECASE)
TOOL_CALL_CLOSE_RE = re.compile(r"</tool_call>", re.IGNORECASE)
TOOL_CALL_BLOCK_RE = re.compile(r"<tool_call>(.*?)</tool_call>", re.IGNORECASE | re.DOTALL)


def parse_tool_call(text: str) -> ToolCall | ToolError:
    """Parse one ``<tool_call>{...}</tool_call>`` block from model text."""

    if not isinstance(text, str):
        return ToolError(
            code="invalid_tool_call_text",
            message="Tool call text must be a string.",
        )

    open_count = len(TOOL_CALL_OPEN_RE.findall(text))
    close_count = len(TOOL_CALL_CLOSE_RE.findall(text))

    if open_count == 0 and close_count == 0:
        return ToolError(
            code="missing_tool_call",
            message="No <tool_call> block found.",
        )
    if open_count != close_count:
        return ToolError(
            code="invalid_tool_call_tag",
            message="Mismatched <tool_call> tags.",
            details={"open_count": open_count, "close_count": close_count},
        )
    if open_count > 1:
        return ToolError(
            code="multiple_tool_calls",
            message="Only one <tool_call> block is allowed.",
            details={"count": open_count},
        )

    match = TOOL_CALL_BLOCK_RE.search(text)
    if match is None:
        return ToolError(
            code="invalid_tool_call_tag",
            message="Could not extract a complete <tool_call> block.",
        )

    payload_text = match.group(1).strip()
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        return ToolError(
            code="invalid_json",
            message=f"Invalid JSON in <tool_call>: {exc.msg}",
            details={"line": exc.lineno, "column": exc.colno},
        )

    if not isinstance(payload, dict):
        return ToolError(
            code="invalid_tool_call_payload",
            message="Tool call JSON payload must be an object.",
        )

    if "name" not in payload:
        return ToolError(
            code="missing_tool_name",
            message="Tool call JSON must include a name field.",
            field="name",
        )
    name = payload["name"]
    if not isinstance(name, str) or not name.strip():
        return ToolError(
            code="invalid_tool_name",
            message="Tool call name must be a non-empty string.",
            field="name",
        )

    if "arguments" not in payload:
        return ToolError(
            code="missing_arguments",
            message="Tool call JSON must include an arguments field.",
            tool_name=name,
            field="arguments",
        )
    arguments = payload["arguments"]
    if not isinstance(arguments, dict):
        return ToolError(
            code="invalid_arguments_type",
            message="Tool call arguments must be an object.",
            tool_name=name,
            field="arguments",
        )

    return ToolCall(name=name.strip(), arguments=arguments, raw_text=match.group(0))
