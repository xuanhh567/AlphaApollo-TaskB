"""Render SkillSpec metadata into model-facing prompt instructions."""

from __future__ import annotations

import json
from typing import Iterable

from .schema import SkillExample, SkillParameter, SkillSpec


def render_skill_prompt_block(specs: Iterable[SkillSpec], escape_braces: bool = False) -> str:
    """Render enabled skills as structured ``<tool_call>`` instructions."""

    sorted_specs = sorted(specs, key=lambda spec: spec.name)
    if not sorted_specs:
        return ""

    sections = [
        "You may call exactly one tool by emitting exactly one <tool_call> block.",
        'The JSON inside <tool_call> must be an object with "name" and "arguments".',
        "Available tools:",
    ]

    for index, spec in enumerate(sorted_specs, start=1):
        sections.append(_render_skill_section(index, spec))

    rendered = "\n\n".join(sections)
    if escape_braces:
        return _escape_format_braces(rendered)
    return rendered


def render_tool_call_example(spec: SkillSpec, example: SkillExample) -> str:
    """Render one example as a complete ``<tool_call>`` block."""

    payload = {
        "name": spec.name,
        "arguments": example.arguments,
    }
    return f"<tool_call>{json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}</tool_call>"


def _render_skill_section(index: int, spec: SkillSpec) -> str:
    lines = [
        f"{index}. {spec.name}: {spec.description}",
        "Parameters:",
    ]

    if spec.parameters:
        for parameter in spec.parameters:
            lines.append(f"   - {_render_parameter(parameter)}")
    else:
        lines.append("   - none")

    if spec.examples:
        lines.append("Examples:")
        for example in spec.examples:
            prefix = f"   - {example.name}: " if example.name else "   - "
            lines.append(prefix + render_tool_call_example(spec, example))

    return "\n".join(lines)


def _render_parameter(parameter: SkillParameter) -> str:
    requirement = "required" if parameter.required else "optional"
    default_text = ""
    if not parameter.required and parameter.default is not None:
        default_text = f", default={json.dumps(parameter.default, ensure_ascii=False)}"
    return f"{parameter.name} ({parameter.type}, {requirement}{default_text}): {parameter.description}"


def _escape_format_braces(text: str) -> str:
    return text.replace("{", "{{").replace("}", "}}")
