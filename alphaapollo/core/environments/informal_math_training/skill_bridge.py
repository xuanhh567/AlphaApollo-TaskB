"""Bridge Skill tool calls into the informal math training environment."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from alphaapollo.core.skills.call_parser import ToolCall, ToolError, parse_tool_call
from alphaapollo.core.skills.dispatcher import ToolResult, dispatch_tool_call
from alphaapollo.core.skills.registry import SkillRegistry
from alphaapollo.core.skills.schema import SkillSpec


@dataclass(frozen=True)
class ParsedToolAction:
    """One parsed tool action from a model response."""

    tool_name: str | None = None
    call: ToolCall | None = None
    tool_input: Any = None
    call_format: str = "none"
    error: ToolError | None = None
    legacy_error_response: str | None = None

    @property
    def is_tool_action(self) -> bool:
        return self.tool_name is not None or self.call is not None or self.error is not None


def parse_tool_actions(action: str, registry: SkillRegistry | None = None) -> list[ParsedToolAction]:
    """Parse structured and legacy tool calls from one model action.

    Structured ``<tool_call>{...}</tool_call>`` is the canonical protocol.
    Legacy tags are accepted only when a loaded ``SkillSpec`` declares them via
    ``legacy_calls``. This keeps backward compatibility out of hard-coded env
    branches while still preserving the old model-facing behavior.
    """

    if _contains_structured_tool_call_tag(action):
        parsed = parse_tool_call(action)
        if isinstance(parsed, ToolError):
            return [
                ParsedToolAction(
                    tool_name=parsed.tool_name,
                    call_format="structured",
                    error=parsed,
                )
            ]
        return [
            ParsedToolAction(
                tool_name=parsed.name,
                call=parsed,
                tool_input=parsed.arguments,
                call_format="structured",
            )
        ]

    legacy_actions = _parse_legacy_skill_actions(action, registry)

    if not legacy_actions:
        return [ParsedToolAction()]

    return legacy_actions


def execute_skill_call_with_tool_group(
    call: ToolCall,
    registry: SkillRegistry,
    tool_group: Any,
) -> ToolResult:
    """Validate a Skill call, then execute the matching ToolGroup method.

    The registry keeps the new Skill contract in charge of tool existence and
    parameter validation. The ToolGroup keeps the old runtime behavior, including
    enable flags, timeouts, RAG configuration, ``text_result`` and ``score``.
    """

    return dispatch_tool_call(
        call,
        registry,
        executor=lambda spec, arguments: _execute_tool_group_entrypoint(spec, arguments, tool_group),
    )


def tool_error_response(error: ToolError) -> str:
    """Return a JSON string suitable for ``<tool_response>``."""

    return _to_json_text(
        {
            "status": "error",
            "error": {
                "code": error.code,
                "message": error.message,
                "field": error.field,
                "details": error.details,
            },
        }
    )


def wrap_tool_response(text_result: str) -> str:
    return "\n<tool_response>" + text_result + "</tool_response>\n"


def _contains_structured_tool_call_tag(action: str) -> bool:
    if not isinstance(action, str):
        return False
    lowered = action.lower()
    return "<tool_call>" in lowered or "</tool_call>" in lowered


def _parse_legacy_skill_actions(action: str, registry: SkillRegistry | None) -> list[ParsedToolAction]:
    if registry is None:
        return []

    actions: list[ParsedToolAction] = []
    for spec in registry.specs():
        for legacy_call in spec.legacy_calls:
            tag = legacy_call.tag
            if f"<{tag}>" not in action or f"</{tag}>" not in action:
                continue

            pattern = rf"<{re.escape(tag)}>(.*?)</{re.escape(tag)}>"
            match = re.search(pattern, action, re.DOTALL)
            if match is None:
                continue

            tool_input = match.group(1).strip()
            actions.append(
                _legacy_action_to_parsed(
                    spec,
                    legacy_call.input_format,
                    legacy_call.argument,
                    tool_input,
                    match.group(0),
                )
            )
    return actions


def _legacy_action_to_parsed(
    spec: SkillSpec,
    input_format: str,
    argument: str | None,
    tool_input: str,
    raw_text: str,
) -> ParsedToolAction:
    tool_name = spec.name
    if input_format == "text":
        if argument is None:
            return ParsedToolAction(
                tool_name=tool_name,
                tool_input=tool_input,
                call_format="legacy",
                error=ToolError(
                    code="missing_legacy_argument",
                    message=f"Legacy text input for {tool_name} must declare an argument.",
                    tool_name=tool_name,
                ),
            )
        return ParsedToolAction(
            tool_name=tool_name,
            call=ToolCall(name=tool_name, arguments={argument: tool_input}, raw_text=raw_text),
            tool_input=tool_input,
            call_format="legacy",
        )

    if input_format == "json":
        try:
            arguments = json.loads(tool_input)
        except json.JSONDecodeError:
            return ParsedToolAction(
                tool_name=tool_name,
                tool_input=tool_input,
                call_format="legacy",
                error=ToolError(
                    code="invalid_json",
                    message=f"Invalid JSON input for {tool_name}.",
                    tool_name=tool_name,
                ),
                legacy_error_response=f"Error: Invalid JSON input for {tool_name}",
            )

        if not isinstance(arguments, dict):
            return ParsedToolAction(
                tool_name=tool_name,
                tool_input=tool_input,
                call_format="legacy",
                error=ToolError(
                    code="invalid_arguments_type",
                    message=f"{tool_name} legacy input must be a JSON object.",
                    tool_name=tool_name,
                ),
                legacy_error_response=f"Error: Invalid JSON input for {tool_name}",
            )

        return ParsedToolAction(
            tool_name=tool_name,
            call=ToolCall(name=tool_name, arguments=arguments, raw_text=raw_text),
            tool_input=tool_input,
            call_format="legacy",
        )

    return ParsedToolAction(
        tool_name=tool_name,
        tool_input=tool_input,
        call_format="legacy",
        error=ToolError(
            code="unsupported_legacy_input_format",
            message=f"Unsupported legacy input format for {tool_name}: {input_format}",
            tool_name=tool_name,
        ),
    )


def _execute_tool_group_entrypoint(spec: SkillSpec, arguments: dict[str, Any], tool_group: Any) -> Any:
    tool_func = tool_group.get_tool(spec.name)
    if tool_func is None:
        raise ValueError(f"Tool is not available in InformalMathToolGroup: {spec.name}")

    raw_output = tool_group.execute_tool(spec.name, arguments)
    return _maybe_add_local_rag_hint(spec.name, raw_output, tool_group)


def _maybe_add_local_rag_hint(tool_name: str, raw_output: Any, tool_group: Any) -> Any:
    if tool_name != "python_code":
        return raw_output
    if not isinstance(raw_output, dict):
        return raw_output
    if not getattr(tool_group, "enable_local_rag", False):
        return raw_output
    if raw_output.get("score") != 0:
        return raw_output

    try:
        inner = json.loads(raw_output.get("text_result", ""))
    except json.JSONDecodeError:
        return raw_output

    inner["result"] = (
        str(inner.get("result", ""))
        + "\n\nPlease use the local_rag tool to query relevant information and resolve the code issue."
    )
    updated = dict(raw_output)
    updated["text_result"] = json.dumps(inner)
    return updated


def _to_json_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, default=str)
