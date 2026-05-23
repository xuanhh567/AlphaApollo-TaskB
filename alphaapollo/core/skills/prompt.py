"""Render SkillSpec metadata into model-facing prompt instructions."""

from __future__ import annotations

import json
from typing import Iterable

from .schema import SkillExample, SkillLegacyCall, SkillParameter, SkillSpec


def render_skill_prompt_block(specs: Iterable[SkillSpec], escape_braces: bool = False) -> str:
    """Render enabled skills as structured ``<tool_call>`` instructions."""

    sorted_specs = sorted(specs, key=lambda spec: spec.name)
    if not sorted_specs:
        return ""

    sections = [
        "Tool schemas:",
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


def render_legacy_skill_prompt_block(specs: Iterable[SkillSpec], escape_braces: bool = False) -> str:
    """Render enabled skills as legacy tag instructions from ``SkillSpec``."""

    lines: list[str] = []
    action_index = 1
    for spec in sorted(specs, key=lambda item: item.name):
        if not spec.legacy_calls:
            continue
        legacy_call = spec.legacy_calls[0]
        lines.append(_render_legacy_skill_action(action_index, spec, legacy_call))
        action_index += 1

    rendered = "\n".join(lines)
    if escape_braces:
        return _escape_format_braces(rendered)
    return rendered


def _render_skill_section(index: int, spec: SkillSpec) -> str:
    lines = [
        f"{index}. {spec.name}: {spec.description}",
    ]

    if spec.parameters:
        parameters = "; ".join(_render_parameter(parameter) for parameter in spec.parameters)
        lines.append(f"   arguments: {parameters}")
    else:
        lines.append("   arguments: none")

    if spec.examples:
        lines.append("   example: " + render_tool_call_example(spec, spec.examples[0]))

    return "\n".join(lines)


def _render_legacy_skill_action(index: int, spec: SkillSpec, legacy_call: SkillLegacyCall) -> str:
    tag = legacy_call.tag
    example = _render_legacy_call_example(spec, legacy_call)
    if legacy_call.input_format == "text":
        return (
            f"{index}) <{tag}>...</{tag}>: If computation/checking is helpful, "
            f"emit exactly ONE <{tag}>...</{tag}> block with pure Python 3. "
            f"Inspect the <tool_response> (stdout from your code). "
            f"If it disagrees with your reasoning, correct yourself. Example: {example}"
        )

    parameter_names = ", ".join(parameter.name for parameter in spec.parameters) or "arguments"
    return (
        f"{index}) <{tag}>...</{tag}>: {spec.description} "
        f"Emit exactly ONE <{tag}>...</{tag}> block containing a JSON object "
        f"with {parameter_names}. Example: {example}"
    )


def _render_legacy_call_example(spec: SkillSpec, legacy_call: SkillLegacyCall) -> str:
    arguments = spec.examples[0].arguments if spec.examples else {}
    tag = legacy_call.tag

    if legacy_call.input_format == "text":
        value = arguments.get(legacy_call.argument or "", "")
        return f"<{tag}>{value}</{tag}>"

    return f"<{tag}>{json.dumps(arguments, ensure_ascii=False, separators=(',', ':'))}</{tag}>"


def _render_parameter(parameter: SkillParameter) -> str:
    requirement = "required" if parameter.required else "optional"
    default_text = ""
    if not parameter.required and parameter.default is not None:
        default_text = f", default={json.dumps(parameter.default, ensure_ascii=False)}"
    return f"{parameter.name} ({parameter.type}, {requirement}{default_text}): {parameter.description}"


def _escape_format_braces(text: str) -> str:
    return text.replace("{", "{{").replace("}", "}}")
