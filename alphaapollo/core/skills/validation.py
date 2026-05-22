"""Validate tool call arguments against SkillSpec parameters."""

from __future__ import annotations

from typing import Any

from .call_parser import ToolError
from .schema import SkillParameter, SkillSpec


def validate_arguments(spec: SkillSpec, arguments: dict[str, Any]) -> tuple[dict[str, Any], list[ToolError]]:
    """Validate and normalize arguments for a skill.

    Returns a copy of ``arguments`` with supported defaults filled in and a
    list of structured errors. Callers must not execute the tool when errors
    are returned.
    """

    normalized = dict(arguments)
    errors: list[ToolError] = []
    parameter_by_name = {parameter.name: parameter for parameter in spec.parameters}

    for parameter in spec.parameters:
        if parameter.name not in normalized:
            if parameter.required:
                errors.append(
                    ToolError(
                        code="missing_required_argument",
                        message=f"Missing required argument: {parameter.name}",
                        tool_name=spec.name,
                        field=parameter.name,
                    )
                )
            elif parameter.default is not None:
                normalized[parameter.name] = parameter.default
            continue

        value = normalized[parameter.name]
        if not _matches_parameter_type(value, parameter):
            errors.append(
                ToolError(
                    code="invalid_argument_type",
                    message=f"Argument {parameter.name} must be {parameter.type}.",
                    tool_name=spec.name,
                    field=parameter.name,
                    details={
                        "expected": parameter.type,
                        "actual": type(value).__name__,
                    },
                )
            )

    for argument_name in normalized:
        if argument_name not in parameter_by_name:
            errors.append(
                ToolError(
                    code="unexpected_argument",
                    message=f"Unexpected argument: {argument_name}",
                    tool_name=spec.name,
                    field=argument_name,
                )
            )

    return normalized, errors


def _matches_parameter_type(value: Any, parameter: SkillParameter) -> bool:
    if parameter.type == "string":
        return isinstance(value, str)
    if parameter.type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if parameter.type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if parameter.type == "boolean":
        return isinstance(value, bool)
    if parameter.type == "object":
        return isinstance(value, dict)
    if parameter.type == "array":
        return isinstance(value, list)
    return False
