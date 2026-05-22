from pathlib import Path
import os
import sys

TEST_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = TEST_ROOT.parents[0]
if str(TEST_ROOT) not in sys.path:
    sys.path.insert(0, str(TEST_ROOT))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("ALPHAAPOLLO_SKIP_VERL_ALIAS", "1")

from alphaapollo.core.skills.call_parser import ToolCall
from alphaapollo.core.skills.dispatcher import ToolResult, dispatch_tool_call
from alphaapollo.core.skills.loader import load_skill_from_dir
from alphaapollo.core.skills.registry import SkillRegistry
from alphaapollo.core.skills.schema import SkillSpec


SKILL = """---
name: {name}
description: Test dispatcher skill.
parameters:
  - name: text
    type: string
    required: true
    description: Text input.
  - name: count
    type: integer
    required: false
    default: 2
    description: Repeat count.
entrypoint:
  type: python_function
  path: {entrypoint}
examples:
  - arguments:
      text: hi
---
"""


def write_skill(tmp_path: Path, name: str, entrypoint: str) -> Path:
    skill_dir = tmp_path / name
    skill_dir.mkdir(exist_ok=True)
    (skill_dir / "SKILL.md").write_text(SKILL.format(name=name, entrypoint=entrypoint), encoding="utf-8")
    return skill_dir


def load_registry(tmp_path: Path, name: str = "echo_tool", entrypoint: str = "skill_dispatcher_fixtures:echo_tool"):
    skill_dir = write_skill(tmp_path, name, entrypoint)
    load_result = load_skill_from_dir(skill_dir)
    assert load_result.ok
    assert load_result.spec is not None
    registry = SkillRegistry()
    assert registry.register(load_result.spec) == []
    return registry


def assert_result_error(result: ToolResult, code: str, field: str | None = None) -> None:
    assert not result.ok
    assert result.score == 0
    assert result.error is not None
    assert result.error.code == code
    assert result.error.field == field


def test_unknown_skill_returns_error(tmp_path):
    registry = load_registry(tmp_path)

    result = dispatch_tool_call(ToolCall(name="missing_tool", arguments={}), registry)

    assert_result_error(result, "unknown_skill")


def test_missing_required_argument_returns_error(tmp_path):
    registry = load_registry(tmp_path)

    result = dispatch_tool_call(ToolCall(name="echo_tool", arguments={}), registry)

    assert_result_error(result, "missing_required_argument", "text")


def test_invalid_argument_type_returns_error(tmp_path):
    registry = load_registry(tmp_path)

    result = dispatch_tool_call(ToolCall(name="echo_tool", arguments={"text": "hi", "count": True}), registry)

    assert_result_error(result, "invalid_argument_type", "count")


def test_default_argument_is_used(tmp_path):
    registry = load_registry(tmp_path)

    result = dispatch_tool_call(ToolCall(name="echo_tool", arguments={"text": "ha"}), registry)

    assert result.ok
    assert result.text_result == "haha"
    assert result.score == 1
    assert result.raw_output == {"text_result": "haha", "score": 1}


def test_runtime_executor_receives_validated_arguments(tmp_path):
    registry = load_registry(tmp_path)
    calls = []

    def executor(spec: SkillSpec, arguments: dict):
        calls.append((spec.name, arguments))
        return {"text_result": arguments["text"] * arguments["count"], "score": 1}

    result = dispatch_tool_call(ToolCall(name="echo_tool", arguments={"text": "ha"}), registry, executor=executor)

    assert result.ok
    assert result.text_result == "haha"
    assert result.score == 1
    assert calls == [("echo_tool", {"text": "ha", "count": 2})]


def test_runtime_executor_is_not_called_when_validation_fails(tmp_path):
    registry = load_registry(tmp_path)
    calls = []

    def executor(spec: SkillSpec, arguments: dict):
        calls.append((spec.name, arguments))
        return {"text_result": "should not run", "score": 1}

    result = dispatch_tool_call(ToolCall(name="echo_tool", arguments={}), registry, executor=executor)

    assert_result_error(result, "missing_required_argument", "text")
    assert calls == []


def test_dispatcher_normalizes_plain_object_output(tmp_path):
    registry = load_registry(tmp_path, name="value_tool", entrypoint="skill_dispatcher_fixtures:value_tool")

    result = dispatch_tool_call(ToolCall(name="value_tool", arguments={"text": "ok"}), registry)

    assert result.ok
    assert result.text_result == '{"value": "ok"}'
    assert result.raw_output == {"value": "ok"}


def test_entrypoint_import_error_returns_error(tmp_path):
    registry = load_registry(tmp_path, entrypoint="skill_dispatcher_fixtures:missing_function")

    result = dispatch_tool_call(ToolCall(name="echo_tool", arguments={"text": "hi"}), registry)

    assert_result_error(result, "entrypoint_import_error", "entrypoint.path")


def test_not_callable_entrypoint_returns_error(tmp_path):
    registry = load_registry(tmp_path, entrypoint="skill_dispatcher_fixtures:NOT_CALLABLE")

    result = dispatch_tool_call(ToolCall(name="echo_tool", arguments={"text": "hi"}), registry)

    assert_result_error(result, "entrypoint_import_error", "entrypoint.path")


def test_tool_execution_error_returns_error(tmp_path):
    registry = load_registry(tmp_path, entrypoint="skill_dispatcher_fixtures:failing_tool")

    result = dispatch_tool_call(ToolCall(name="echo_tool", arguments={"text": "hi"}), registry)

    assert_result_error(result, "tool_execution_error")
    assert result.error is not None
    assert result.error.details == {"exception_type": "RuntimeError"}


def test_runtime_executor_error_returns_error(tmp_path):
    registry = load_registry(tmp_path)

    def executor(spec: SkillSpec, arguments: dict):
        raise RuntimeError("boom")

    result = dispatch_tool_call(ToolCall(name="echo_tool", arguments={"text": "hi"}), registry, executor=executor)

    assert_result_error(result, "tool_execution_error")
    assert result.error is not None
    assert result.error.details == {"exception_type": "RuntimeError"}


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        test_unknown_skill_returns_error(tmp_path)
        test_missing_required_argument_returns_error(tmp_path)
        test_invalid_argument_type_returns_error(tmp_path)
        test_default_argument_is_used(tmp_path)
        test_runtime_executor_receives_validated_arguments(tmp_path)
        test_runtime_executor_is_not_called_when_validation_fails(tmp_path)
        test_dispatcher_normalizes_plain_object_output(tmp_path)
        test_entrypoint_import_error_returns_error(tmp_path)
        test_not_callable_entrypoint_returns_error(tmp_path)
        test_tool_execution_error_returns_error(tmp_path)
        test_runtime_executor_error_returns_error(tmp_path)
    print("skill dispatcher tests passed")
