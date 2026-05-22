from pathlib import Path
import os
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("ALPHAAPOLLO_SKIP_VERL_ALIAS", "1")

from alphaapollo.core.skills.call_parser import ToolCall, ToolError, parse_tool_call


def assert_error(result, code: str, field: str | None = None) -> ToolError:
    assert isinstance(result, ToolError)
    assert result.code == code
    assert result.field == field
    return result


def test_parse_valid_tool_call():
    result = parse_tool_call(
        'Before <tool_call>{"name":"python_code","arguments":{"code":"print(1 + 1)"}}</tool_call> after'
    )

    assert isinstance(result, ToolCall)
    assert result.name == "python_code"
    assert result.arguments == {"code": "print(1 + 1)"}
    assert result.raw_text == '<tool_call>{"name":"python_code","arguments":{"code":"print(1 + 1)"}}</tool_call>'


def test_parse_multiline_tool_call():
    result = parse_tool_call(
        """
<tool_call>
{"name": "local_rag", "arguments": {"repo_name": "sympy", "query": "solve equations", "top_k": 3}}
</tool_call>
"""
    )

    assert isinstance(result, ToolCall)
    assert result.name == "local_rag"
    assert result.arguments["repo_name"] == "sympy"
    assert result.arguments["top_k"] == 3


def test_missing_tool_call_returns_error():
    result = parse_tool_call("<answer>2</answer>")

    assert_error(result, "missing_tool_call")


def test_mismatched_tool_call_tags_returns_error():
    result = parse_tool_call('<tool_call>{"name":"python_code","arguments":{}}')

    error = assert_error(result, "invalid_tool_call_tag")
    assert error.details == {"open_count": 1, "close_count": 0}


def test_multiple_tool_calls_returns_error():
    result = parse_tool_call(
        '<tool_call>{"name":"a","arguments":{}}</tool_call>'
        '<tool_call>{"name":"b","arguments":{}}</tool_call>'
    )

    error = assert_error(result, "multiple_tool_calls")
    assert error.details == {"count": 2}


def test_invalid_json_returns_error():
    result = parse_tool_call('<tool_call>{"name": "python_code",</tool_call>')

    assert_error(result, "invalid_json")


def test_payload_must_be_object():
    result = parse_tool_call('<tool_call>["python_code"]</tool_call>')

    assert_error(result, "invalid_tool_call_payload")


def test_missing_name_returns_error():
    result = parse_tool_call('<tool_call>{"arguments": {}}</tool_call>')

    assert_error(result, "missing_tool_name", "name")


def test_name_must_be_non_empty_string():
    result = parse_tool_call('<tool_call>{"name": "", "arguments": {}}</tool_call>')

    assert_error(result, "invalid_tool_name", "name")


def test_missing_arguments_returns_error():
    result = parse_tool_call('<tool_call>{"name": "python_code"}</tool_call>')

    assert_error(result, "missing_arguments", "arguments")


def test_arguments_must_be_object():
    result = parse_tool_call('<tool_call>{"name": "python_code", "arguments": "print(1)"}</tool_call>')

    error = assert_error(result, "invalid_arguments_type", "arguments")
    assert error.tool_name == "python_code"


if __name__ == "__main__":
    test_parse_valid_tool_call()
    test_parse_multiline_tool_call()
    test_missing_tool_call_returns_error()
    test_mismatched_tool_call_tags_returns_error()
    test_multiple_tool_calls_returns_error()
    test_invalid_json_returns_error()
    test_payload_must_be_object()
    test_missing_name_returns_error()
    test_name_must_be_non_empty_string()
    test_missing_arguments_returns_error()
    test_arguments_must_be_object()
    print("tool call parser tests passed")
