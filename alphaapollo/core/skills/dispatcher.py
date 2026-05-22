"""Dispatch validated tool calls to skill entrypoints."""

from __future__ import annotations

import importlib
import json
from dataclasses import dataclass
from typing import Any, Callable

from .call_parser import ToolCall, ToolError
from .registry import SkillRegistry
from .schema import SkillSpec
from .validation import validate_arguments

RuntimeExecutor = Callable[[SkillSpec, dict[str, Any]], Any]


@dataclass(frozen=True)
class ToolResult:
    """Normalized result of dispatching one tool call."""

    ok: bool
    tool_name: str
    text_result: str
    score: int | float | None = None
    raw_output: Any = None
    error: ToolError | None = None


def dispatch_tool_call(
    call: ToolCall,
    registry: SkillRegistry,
    executor: RuntimeExecutor | None = None,
) -> ToolResult:
    """Validate and execute one tool call through a skill registry."""

    spec = registry.get(call.name)
    if spec is None:
        return _error_result(
            call.name,
            ToolError(
                code="unknown_skill",
                message=f"Unknown skill: {call.name}",
                tool_name=call.name,
            ),
        )

    normalized_arguments, validation_errors = validate_arguments(spec, call.arguments)
    if validation_errors:
        return _error_result(spec.name, validation_errors[0])

    if executor is not None:
        try:
            raw_output = executor(spec, normalized_arguments)
        except Exception as exc:
            return _error_result(
                spec.name,
                ToolError(
                    code="tool_execution_error",
                    message=f"Tool execution failed: {exc}",
                    tool_name=spec.name,
                    details={"exception_type": type(exc).__name__},
                ),
            )

        return _normalize_output(spec.name, raw_output)

    if spec.entrypoint.type != "python_function":
        return _error_result(
            spec.name,
            ToolError(
                code="unsupported_entrypoint_type",
                message=f"Unsupported entrypoint type: {spec.entrypoint.type}",
                tool_name=spec.name,
                field="entrypoint.type",
            ),
        )

    function_or_error = _load_python_function(spec)
    if isinstance(function_or_error, ToolError):
        return _error_result(spec.name, function_or_error)

    try:
        raw_output = function_or_error(**normalized_arguments)
    except Exception as exc:
        return _error_result(
            spec.name,
            ToolError(
                code="tool_execution_error",
                message=f"Tool execution failed: {exc}",
                tool_name=spec.name,
                details={"exception_type": type(exc).__name__},
            ),
        )

    return _normalize_output(spec.name, raw_output)


def _load_python_function(spec: SkillSpec) -> Callable[..., Any] | ToolError:
    module_name, separator, function_name = spec.entrypoint.path.partition(":")
    if not separator:
        return ToolError(
            code="entrypoint_import_error",
            message="python_function entrypoint must use 'module:function' format.",
            tool_name=spec.name,
            field="entrypoint.path",
        )

    try:
        module = importlib.import_module(module_name)
        function = getattr(module, function_name)
    except Exception as exc:
        return ToolError(
            code="entrypoint_import_error",
            message=f"Could not import entrypoint {spec.entrypoint.path}: {exc}",
            tool_name=spec.name,
            field="entrypoint.path",
            details={"exception_type": type(exc).__name__},
        )

    if not callable(function):
        return ToolError(
            code="entrypoint_import_error",
            message=f"Entrypoint is not callable: {spec.entrypoint.path}",
            tool_name=spec.name,
            field="entrypoint.path",
        )
    return function


def _normalize_output(tool_name: str, raw_output: Any) -> ToolResult:
    if isinstance(raw_output, dict) and "text_result" in raw_output:
        text_result = raw_output.get("text_result", "")
        if not isinstance(text_result, str):
            text_result = _to_json_text(text_result)
        return ToolResult(
            ok=True,
            tool_name=tool_name,
            text_result=text_result,
            score=raw_output.get("score"),
            raw_output=raw_output,
        )

    return ToolResult(
        ok=True,
        tool_name=tool_name,
        text_result=_to_json_text(raw_output),
        raw_output=raw_output,
    )


def _error_result(tool_name: str, error: ToolError) -> ToolResult:
    return ToolResult(
        ok=False,
        tool_name=tool_name,
        text_result=_to_json_text(
            {
                "status": "error",
                "error": {
                    "code": error.code,
                    "message": error.message,
                    "field": error.field,
                    "details": error.details,
                },
            }
        ),
        score=0,
        error=error,
    )


def _to_json_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, default=str)
