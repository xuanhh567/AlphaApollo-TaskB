from pathlib import Path
import importlib.util
import json
import os
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("ALPHAAPOLLO_SKIP_VERL_ALIAS", "1")

from alphaapollo.core.skills.call_parser import ToolCall
from alphaapollo.core.skills.registry import get_builtin_skill_dirs, load_skill_registry_from_dirs

BRIDGE_PATH = PROJECT_ROOT / "alphaapollo/core/environments/informal_math_training/skill_bridge.py"
BRIDGE_SPEC = importlib.util.spec_from_file_location("informal_math_training_skill_bridge", BRIDGE_PATH)
assert BRIDGE_SPEC is not None
skill_bridge = importlib.util.module_from_spec(BRIDGE_SPEC)
assert BRIDGE_SPEC.loader is not None
sys.modules[BRIDGE_SPEC.name] = skill_bridge
BRIDGE_SPEC.loader.exec_module(skill_bridge)

execute_skill_call_with_tool_group = skill_bridge.execute_skill_call_with_tool_group
parse_tool_actions = skill_bridge.parse_tool_actions
wrap_tool_response = skill_bridge.wrap_tool_response


class FakeToolGroup:
    def __init__(self, enable_local_rag=True):
        self.enable_local_rag = enable_local_rag
        self.calls = []

    def get_tool(self, name):
        if name in {"python_code", "local_rag"}:
            return True
        return None

    def execute_tool(self, name, arguments):
        self.calls.append((name, arguments))
        if name == "python_code":
            return {"text_result": json.dumps({"result": "2", "status": "success"}), "score": 1}
        if name == "local_rag":
            if not self.enable_local_rag:
                return {
                    "text_result": json.dumps({
                        "result": "Local RAG is not enabled.",
                        "status": "disabled",
                    }),
                    "score": 0,
                }
            return {"text_result": json.dumps({"result": "docs", "status": "success"}), "score": 1}
        raise ValueError(name)


def load_builtin_registry():
    result = load_skill_registry_from_dirs(
        get_builtin_skill_dirs(),
        enabled_skills=["python_code", "local_rag"],
    )
    assert result.ok
    return result.registry


def test_parse_structured_python_code():
    actions = parse_tool_actions(
        '<tool_call>{"name":"python_code","arguments":{"code":"print(1 + 1)"}}</tool_call>'
    )

    assert len(actions) == 1
    assert actions[0].call is not None
    assert actions[0].call.name == "python_code"
    assert actions[0].call.arguments == {"code": "print(1 + 1)"}
    assert actions[0].call_format == "structured"


def test_parse_legacy_python_code():
    actions = parse_tool_actions("<python_code>print(1 + 1)</python_code>")

    assert len(actions) == 1
    assert actions[0].call is not None
    assert actions[0].call.name == "python_code"
    assert actions[0].call.arguments == {"code": "print(1 + 1)"}
    assert actions[0].call_format == "legacy"


def test_parse_legacy_local_rag_json():
    actions = parse_tool_actions(
        '<local_rag>{"repo_name":"sympy","query":"solve equations","top_k":3}</local_rag>'
    )

    assert len(actions) == 1
    assert actions[0].call is not None
    assert actions[0].call.name == "local_rag"
    assert actions[0].call.arguments == {
        "repo_name": "sympy",
        "query": "solve equations",
        "top_k": 3,
    }


def test_parse_structured_local_rag():
    actions = parse_tool_actions(
        '<tool_call>{"name":"local_rag","arguments":{"repo_name":"sympy","query":"solve equations","top_k":3}}</tool_call>'
    )

    assert len(actions) == 1
    assert actions[0].call is not None
    assert actions[0].call.name == "local_rag"
    assert actions[0].call.arguments == {
        "repo_name": "sympy",
        "query": "solve equations",
        "top_k": 3,
    }
    assert actions[0].call_format == "structured"


def test_parse_legacy_local_rag_invalid_json_keeps_old_error_text():
    actions = parse_tool_actions("<local_rag>not json</local_rag>")

    assert len(actions) == 1
    assert actions[0].error is not None
    assert actions[0].error.code == "invalid_json"
    assert actions[0].legacy_error_response == "Error: Invalid JSON input for local_rag"


def test_execute_skill_call_validates_before_tool_group_execution():
    registry = load_builtin_registry()
    tool_group = FakeToolGroup()

    result = execute_skill_call_with_tool_group(ToolCall(name="python_code", arguments={}), registry, tool_group)

    assert not result.ok
    assert result.error is not None
    assert result.error.code == "missing_required_argument"
    assert tool_group.calls == []


def test_execute_unknown_skill_returns_error_without_tool_group_execution():
    registry = load_builtin_registry()
    tool_group = FakeToolGroup()

    result = execute_skill_call_with_tool_group(ToolCall(name="missing_tool", arguments={}), registry, tool_group)

    assert not result.ok
    assert result.error is not None
    assert result.error.code == "unknown_skill"
    assert tool_group.calls == []


def test_execute_skill_call_uses_tool_group_for_runtime_behavior():
    registry = load_builtin_registry()
    tool_group = FakeToolGroup()

    result = execute_skill_call_with_tool_group(
        ToolCall(name="python_code", arguments={"code": "print(1 + 1)"}),
        registry,
        tool_group,
    )

    assert result.ok
    assert result.score == 1
    assert tool_group.calls == [("python_code", {"code": "print(1 + 1)"})]
    assert wrap_tool_response(result.text_result).startswith("\n<tool_response>")


def test_execute_local_rag_uses_tool_group_and_defaults_top_k():
    registry = load_builtin_registry()
    tool_group = FakeToolGroup()

    result = execute_skill_call_with_tool_group(
        ToolCall(name="local_rag", arguments={"repo_name": "sympy", "query": "solve equations"}),
        registry,
        tool_group,
    )

    assert result.ok
    assert result.score == 1
    assert tool_group.calls == [
        ("local_rag", {"repo_name": "sympy", "query": "solve equations", "top_k": 3})
    ]


def test_execute_local_rag_preserves_disabled_tool_group_response():
    registry = load_builtin_registry()
    tool_group = FakeToolGroup(enable_local_rag=False)

    result = execute_skill_call_with_tool_group(
        ToolCall(name="local_rag", arguments={"repo_name": "sympy", "query": "solve equations"}),
        registry,
        tool_group,
    )

    assert result.ok
    assert result.score == 0
    assert json.loads(result.text_result) == {
        "result": "Local RAG is not enabled.",
        "status": "disabled",
    }


if __name__ == "__main__":
    test_parse_structured_python_code()
    test_parse_legacy_python_code()
    test_parse_legacy_local_rag_json()
    test_parse_structured_local_rag()
    test_parse_legacy_local_rag_invalid_json_keeps_old_error_text()
    test_execute_skill_call_validates_before_tool_group_execution()
    test_execute_unknown_skill_returns_error_without_tool_group_execution()
    test_execute_skill_call_uses_tool_group_for_runtime_behavior()
    test_execute_local_rag_uses_tool_group_and_defaults_top_k()
    test_execute_local_rag_preserves_disabled_tool_group_response()
    print("informal math skill bridge tests passed")
