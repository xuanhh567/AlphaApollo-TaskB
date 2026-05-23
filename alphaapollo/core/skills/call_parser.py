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
TOOL_CALLS_OPEN_RE = re.compile(r"<tool_calls>", re.IGNORECASE)
TOOL_CALLS_CLOSE_RE = re.compile(r"</tool_calls>", re.IGNORECASE)
TOOL_CALLS_BLOCK_RE = re.compile(r"<tool_calls>(.*?)</tool_calls>", re.IGNORECASE | re.DOTALL)


def parse_tool_call(text: str) -> ToolCall | ToolError:
    """Parse one model tool call block from model text.

    The canonical Task B protocol is ``<tool_call>{...}</tool_call>``.  Some
    Qwen/Hermes-style templates emit a plural ``<tool_calls>`` block or an
    OpenAI-like ``{"function": ...}`` object, so this parser accepts those
    shapes and normalizes them into the same internal ``ToolCall`` contract.
    """

    if not isinstance(text, str):
        return ToolError(
            code="invalid_tool_call_text",
            message="Tool call text must be a string.",
        )

    singular_open_count = len(TOOL_CALL_OPEN_RE.findall(text))
    singular_close_count = len(TOOL_CALL_CLOSE_RE.findall(text))
    plural_open_count = len(TOOL_CALLS_OPEN_RE.findall(text))
    plural_close_count = len(TOOL_CALLS_CLOSE_RE.findall(text))
    open_count = singular_open_count + plural_open_count
    close_count = singular_close_count + plural_close_count

    if open_count == 0 and close_count == 0:
        return ToolError(
            code="missing_tool_call",
            message="No <tool_call> or <tool_calls> block found.",
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

    if singular_open_count and plural_open_count:
        return ToolError(
            code="multiple_tool_calls",
            message="Only one tool call block is allowed.",
            details={"count": open_count},
        )

    match = TOOL_CALL_BLOCK_RE.search(text) or TOOL_CALLS_BLOCK_RE.search(text)
    if match is None:
        return ToolError(
            code="invalid_tool_call_tag",
            message="Could not extract a complete tool call block.",
        )

    payload_text = match.group(1).strip()
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        return ToolError(
            code="invalid_json",
            message=f"Invalid JSON in tool call: {exc.msg}",
            details={"line": exc.lineno, "column": exc.colno},
        )

    return _payload_to_tool_call(payload, raw_text=match.group(0))


def _payload_to_tool_call(payload: Any, raw_text: str) -> ToolCall | ToolError:
    """Normalize canonical, Hermes-like, and OpenAI-like payloads."""

    if isinstance(payload, list):
        if len(payload) != 1:
            return ToolError(
                code="multiple_tool_calls",
                message="Only one tool call is allowed.",
                details={"count": len(payload)},
            )
        payload = payload[0]

    if not isinstance(payload, dict):
        return ToolError(
            code="invalid_tool_call_payload",
            message="Tool call JSON payload must be an object.",
        )

    if "tool_calls" in payload:
        tool_calls = payload["tool_calls"]
        if isinstance(tool_calls, dict):
            tool_calls = [tool_calls]
        if not isinstance(tool_calls, list):
            return ToolError(
                code="invalid_tool_call_payload",
                message="tool_calls must be an array or object.",
                field="tool_calls",
            )
        if len(tool_calls) != 1:
            return ToolError(
                code="multiple_tool_calls",
                message="Only one tool call is allowed.",
                details={"count": len(tool_calls)},
            )
        payload = tool_calls[0]
        if not isinstance(payload, dict):
            return ToolError(
                code="invalid_tool_call_payload",
                message="Each tool_calls item must be an object.",
                field="tool_calls",
            )

    if "function" in payload:
        function_payload = payload["function"]
        if not isinstance(function_payload, dict):
            return ToolError(
                code="invalid_tool_call_payload",
                message="function must be an object.",
                field="function",
            )
        payload = function_payload

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
    if isinstance(arguments, str):
        stripped_arguments = arguments.strip()
        if stripped_arguments.startswith("{"):
            try:
                arguments = json.loads(stripped_arguments)
            except json.JSONDecodeError as exc:
                return ToolError(
                    code="invalid_json",
                    message=f"Invalid JSON in tool-call arguments: {exc.msg}",
                    tool_name=name,
                    field="arguments",
                    details={"line": exc.lineno, "column": exc.colno},
                )

    if not isinstance(arguments, dict):
        return ToolError(
            code="invalid_arguments_type",
            message="Tool call arguments must be an object.",
            tool_name=name,
            field="arguments",
        )

    return ToolCall(name=name.strip(), arguments=arguments, raw_text=raw_text)
