from pathlib import Path
import os
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("ALPHAAPOLLO_SKIP_VERL_ALIAS", "1")

from alphaapollo.core.skills.loader import load_skill_from_dir


VALID_SKILL = """---
name: python_code
description: Execute Python code.
parameters:
  - name: code
    type: string
    required: true
    description: Python code to execute.
entrypoint:
  type: python_function
  path: alphaapollo.core.tools.python_code:execute_python_code
timeout: 30
examples:
  - name: compute
    arguments:
      code: "print(1 + 1)"
---
# Python Code
"""


def write_skill(tmp_path: Path, content: str, name: str = "skill") -> Path:
    skill_dir = tmp_path / name
    skill_dir.mkdir(exist_ok=True)
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
    return skill_dir


def assert_first_error(result, code: str, field: str) -> None:
    assert not result.ok
    assert result.errors
    assert result.errors[0].code == code
    assert result.errors[0].field == field


def test_load_valid_skill(tmp_path):
    skill_dir = write_skill(tmp_path, VALID_SKILL)

    result = load_skill_from_dir(skill_dir)

    assert result.ok
    assert result.spec is not None
    assert result.spec.name == "python_code"
    assert result.spec.description == "Execute Python code."
    assert result.spec.parameters[0].name == "code"
    assert result.spec.parameters[0].type == "string"
    assert result.spec.parameters[0].required is True
    assert result.spec.entrypoint.type == "python_function"
    assert result.spec.entrypoint.path == "alphaapollo.core.tools.python_code:execute_python_code"
    assert result.spec.timeout == 30
    assert result.spec.examples[0].arguments == {"code": "print(1 + 1)"}


def test_missing_name_returns_structured_error(tmp_path):
    skill_dir = write_skill(tmp_path, VALID_SKILL.replace("name: python_code\n", ""))

    result = load_skill_from_dir(skill_dir)

    assert_first_error(result, "missing_required_field", "name")


def test_parameters_must_be_list(tmp_path):
    content = VALID_SKILL.replace(
        "parameters:\n"
        "  - name: code\n"
        "    type: string\n"
        "    required: true\n"
        "    description: Python code to execute.\n",
        "parameters:\n"
        "  code:\n"
        "    type: string\n",
    )
    skill_dir = write_skill(tmp_path, content)

    result = load_skill_from_dir(skill_dir)

    assert_first_error(result, "invalid_field_type", "parameters")


def test_entrypoint_path_must_use_module_colon_function(tmp_path):
    content = VALID_SKILL.replace(
        "alphaapollo.core.tools.python_code:execute_python_code",
        "alphaapollo.core.tools.python_code.execute_python_code",
    )
    skill_dir = write_skill(tmp_path, content)

    result = load_skill_from_dir(skill_dir)

    assert_first_error(result, "invalid_entrypoint_path", "entrypoint.path")


def test_example_must_have_arguments(tmp_path):
    content = VALID_SKILL.replace(
        "    arguments:\n"
        "      code: \"print(1 + 1)\"\n",
        "",
    )
    skill_dir = write_skill(tmp_path, content)

    result = load_skill_from_dir(skill_dir)

    assert_first_error(result, "missing_required_field", "examples[0].arguments")


def test_missing_frontmatter_returns_structured_error(tmp_path):
    skill_dir = write_skill(tmp_path, "name: python_code\n")

    result = load_skill_from_dir(skill_dir)

    assert_first_error(result, "missing_frontmatter", None)


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        test_load_valid_skill(tmp_path)
        test_missing_name_returns_structured_error(tmp_path)
        test_parameters_must_be_list(tmp_path)
        test_entrypoint_path_must_use_module_colon_function(tmp_path)
        test_example_must_have_arguments(tmp_path)
        test_missing_frontmatter_returns_structured_error(tmp_path)
    print("skill loader tests passed")
