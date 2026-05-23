from pathlib import Path
import importlib.util
import os
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("ALPHAAPOLLO_SKIP_VERL_ALIAS", "1")

from alphaapollo.core.skills.prompt import render_skill_prompt_block
from alphaapollo.core.skills.registry import get_builtin_skill_dirs, load_skill_registry_from_dirs

PROMPT_PATH = PROJECT_ROOT / "alphaapollo/core/environments/prompts/informal_math_training.py"
PROMPT_SPEC = importlib.util.spec_from_file_location("informal_math_training_prompt", PROMPT_PATH)
assert PROMPT_SPEC is not None
prompt_module = importlib.util.module_from_spec(PROMPT_SPEC)
assert PROMPT_SPEC.loader is not None
sys.modules[PROMPT_SPEC.name] = prompt_module
PROMPT_SPEC.loader.exec_module(prompt_module)

get_policy_training_prompt = prompt_module.get_policy_training_prompt


def load_builtin_specs(names):
    result = load_skill_registry_from_dirs(get_builtin_skill_dirs(), enabled_skills=names)
    assert result.ok
    return result.registry.specs()


def test_render_skill_prompt_block_includes_metadata():
    specs = load_builtin_specs(["python_code", "local_rag"])

    block = render_skill_prompt_block(specs)

    assert "python_code" in block
    assert "Execute Python code" in block
    assert "code (string, required)" in block
    assert "local_rag" in block
    assert "repo_name (string, required)" in block
    assert "top_k (integer, optional, default=3)" in block


def test_render_skill_prompt_block_renders_tool_call_examples():
    specs = load_builtin_specs(["python_code"])

    block = render_skill_prompt_block(specs)

    assert '<tool_call>{"name":"python_code","arguments":{"code":"print(1 + 1)"}}</tool_call>' in block
    assert "Tool schemas:" in block
    assert "arguments:" in block


def test_render_skill_prompt_block_can_escape_format_braces():
    specs = load_builtin_specs(["python_code"])

    block = render_skill_prompt_block(specs, escape_braces=True)

    assert '{{"name":"python_code","arguments":{{"code":"print(1 + 1)"}}}}' in block


def test_training_prompt_uses_structured_tool_call_specs():
    specs = load_builtin_specs(["python_code", "local_rag"])

    template = get_policy_training_prompt(use_history=False, max_steps=4, tool_specs=specs)
    prompt = template.format(question="What is 1+1?")

    assert "<tool_call>" in prompt
    assert "python_code" in prompt
    assert "local_rag" in prompt
    assert "<python_code>" not in prompt
    assert "<local_rag>" not in prompt


def test_training_prompt_without_tools_has_no_tool_call():
    template = get_policy_training_prompt(use_history=False, max_steps=4, tool_specs=[])
    prompt = template.format(question="What is 1+1?")

    assert "<tool_call>" not in prompt
    assert "<answer>" in prompt


def test_training_prompt_with_history_keeps_history_placeholders():
    specs = load_builtin_specs(["python_code"])

    template = get_policy_training_prompt(use_history=True, max_steps=4, tool_specs=specs)

    assert "{memory_context}" in template
    assert "{step_count}" in template
    prompt = template.format(question="What is 1+1?", memory_context="old step", step_count=1)
    assert "old step" in prompt
    assert "1 step(s)" in prompt


def test_training_prompt_legacy_tool_config_still_supported():
    template = get_policy_training_prompt(
        use_history=False,
        max_steps=4,
        tool_config={"enable_python_code": True, "enable_local_rag": False},
    )

    assert "<python_code>" in template
    assert "<tool_call>" not in template


if __name__ == "__main__":
    test_render_skill_prompt_block_includes_metadata()
    test_render_skill_prompt_block_renders_tool_call_examples()
    test_render_skill_prompt_block_can_escape_format_braces()
    test_training_prompt_uses_structured_tool_call_specs()
    test_training_prompt_without_tools_has_no_tool_call()
    test_training_prompt_with_history_keeps_history_placeholders()
    test_training_prompt_legacy_tool_config_still_supported()
    print("skill prompt renderer tests passed")
