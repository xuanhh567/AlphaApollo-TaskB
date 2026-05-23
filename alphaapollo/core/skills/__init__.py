"""Skill metadata primitives for AlphaApollo tool plugins."""

from alphaapollo.core.skills.call_parser import ToolCall, ToolError, parse_tool_call
from alphaapollo.core.skills.dispatcher import RuntimeExecutor, ToolResult, dispatch_tool_call
from alphaapollo.core.skills.prompt import render_skill_prompt_block, render_tool_call_example
from alphaapollo.core.skills.registry import (
    SkillRegistry,
    SkillRegistryError,
    SkillRegistryLoadResult,
    get_builtin_skill_dirs,
    load_skill_registry_from_dirs,
    resolve_enabled_skill_names,
)
from alphaapollo.core.skills.schema import (
    SkillEntrypoint,
    SkillExample,
    SkillLegacyCall,
    SkillLoadError,
    SkillLoadResult,
    SkillParameter,
    SkillSpec,
)
from alphaapollo.core.skills.validation import validate_arguments

__all__ = [
    "ToolCall",
    "ToolError",
    "ToolResult",
    "RuntimeExecutor",
    "SkillRegistry",
    "SkillRegistryError",
    "SkillRegistryLoadResult",
    "SkillEntrypoint",
    "SkillExample",
    "SkillLegacyCall",
    "SkillLoadError",
    "SkillLoadResult",
    "SkillParameter",
    "SkillSpec",
    "get_builtin_skill_dirs",
    "load_skill_registry_from_dirs",
    "parse_tool_call",
    "render_skill_prompt_block",
    "render_tool_call_example",
    "resolve_enabled_skill_names",
    "dispatch_tool_call",
    "validate_arguments",
]
