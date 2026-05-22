from pathlib import Path
import os
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("ALPHAAPOLLO_SKIP_VERL_ALIAS", "1")

from alphaapollo.core.skills.loader import load_skill_from_dir
from alphaapollo.core.skills.validation import validate_arguments


SKILL = """---
name: sample_tool
description: Sample tool.
parameters:
  - name: text
    type: string
    required: true
    description: Text input.
  - name: count
    type: integer
    required: false
    default: 3
    description: Number of repetitions.
  - name: ratio
    type: number
    required: false
    description: Numeric ratio.
  - name: enabled
    type: boolean
    required: false
    description: Enable flag.
  - name: metadata
    type: object
    required: false
    description: Metadata payload.
  - name: items
    type: array
    required: false
    description: Item list.
entrypoint:
  type: python_function
  path: package.module:run
examples:
  - arguments:
      text: hello
---
"""


def load_sample_spec(tmp_path: Path):
    skill_dir = tmp_path / "sample_tool"
    skill_dir.mkdir(exist_ok=True)
    (skill_dir / "SKILL.md").write_text(SKILL, encoding="utf-8")
    result = load_skill_from_dir(skill_dir)
    assert result.ok
    assert result.spec is not None
    return result.spec


def test_validate_fills_optional_default(tmp_path):
    spec = load_sample_spec(tmp_path)

    normalized, errors = validate_arguments(spec, {"text": "hello"})

    assert errors == []
    assert normalized == {"text": "hello", "count": 3}


def test_missing_required_argument_returns_error(tmp_path):
    spec = load_sample_spec(tmp_path)

    normalized, errors = validate_arguments(spec, {})

    assert normalized == {"count": 3}
    assert len(errors) == 1
    assert errors[0].code == "missing_required_argument"
    assert errors[0].field == "text"
    assert errors[0].tool_name == "sample_tool"


def test_invalid_string_argument_returns_error(tmp_path):
    spec = load_sample_spec(tmp_path)

    _, errors = validate_arguments(spec, {"text": 123})

    assert len(errors) == 1
    assert errors[0].code == "invalid_argument_type"
    assert errors[0].field == "text"
    assert errors[0].details == {"expected": "string", "actual": "int"}


def test_integer_rejects_bool(tmp_path):
    spec = load_sample_spec(tmp_path)

    _, errors = validate_arguments(spec, {"text": "hello", "count": True})

    assert len(errors) == 1
    assert errors[0].code == "invalid_argument_type"
    assert errors[0].field == "count"


def test_number_accepts_int_and_float_but_rejects_bool(tmp_path):
    spec = load_sample_spec(tmp_path)

    _, int_errors = validate_arguments(spec, {"text": "hello", "ratio": 2})
    _, float_errors = validate_arguments(spec, {"text": "hello", "ratio": 2.5})
    _, bool_errors = validate_arguments(spec, {"text": "hello", "ratio": False})

    assert int_errors == []
    assert float_errors == []
    assert len(bool_errors) == 1
    assert bool_errors[0].code == "invalid_argument_type"
    assert bool_errors[0].field == "ratio"


def test_object_array_and_boolean_types(tmp_path):
    spec = load_sample_spec(tmp_path)

    normalized, errors = validate_arguments(
        spec,
        {
            "text": "hello",
            "enabled": True,
            "metadata": {"source": "test"},
            "items": [1, 2, 3],
        },
    )

    assert errors == []
    assert normalized["enabled"] is True
    assert normalized["metadata"] == {"source": "test"}
    assert normalized["items"] == [1, 2, 3]


def test_unexpected_argument_returns_error(tmp_path):
    spec = load_sample_spec(tmp_path)

    _, errors = validate_arguments(spec, {"text": "hello", "extra": 1})

    assert len(errors) == 1
    assert errors[0].code == "unexpected_argument"
    assert errors[0].field == "extra"


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        test_validate_fills_optional_default(tmp_path)
        test_missing_required_argument_returns_error(tmp_path)
        test_invalid_string_argument_returns_error(tmp_path)
        test_integer_rejects_bool(tmp_path)
        test_number_accepts_int_and_float_but_rejects_bool(tmp_path)
        test_object_array_and_boolean_types(tmp_path)
        test_unexpected_argument_returns_error(tmp_path)
    print("skill argument validation tests passed")
