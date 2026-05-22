from dataclasses import replace
from pathlib import Path
import os
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("ALPHAAPOLLO_SKIP_VERL_ALIAS", "1")

from alphaapollo.core.skills.loader import load_skill_from_dir
from alphaapollo.core.skills.registry import (
    SkillRegistry,
    get_builtin_skill_dirs,
    load_skill_registry_from_dirs,
    resolve_enabled_skill_names,
)


VALID_SKILL = """---
name: {name}
description: Test skill.
parameters:
  - name: text
    type: string
    required: true
    description: Text input.
entrypoint:
  type: python_function
  path: package.module:run
timeout: 10
examples:
  - name: echo
    arguments:
      text: hello
---
# Test Skill
"""


INVALID_SKILL = """---
description: Missing name.
parameters:
  - name: text
    type: string
    required: true
    description: Text input.
entrypoint:
  type: python_function
  path: package.module:run
examples:
  - arguments:
      text: hello
---
"""


def write_skill(tmp_path: Path, name: str, content: str) -> Path:
    skill_dir = tmp_path / name
    skill_dir.mkdir(exist_ok=True)
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
    return skill_dir


def load_spec(tmp_path: Path, name: str):
    skill_dir = write_skill(tmp_path, name, VALID_SKILL.format(name=name))
    result = load_skill_from_dir(skill_dir)
    assert result.ok
    assert result.spec is not None
    return result.spec


def test_register_and_get_skill(tmp_path):
    spec = load_spec(tmp_path, "alpha_skill")
    registry = SkillRegistry()

    errors = registry.register(spec)

    assert errors == []
    assert registry.get("alpha_skill") == spec
    assert registry.require("alpha_skill") == spec
    assert registry.names() == ["alpha_skill"]
    assert registry.specs() == [spec]


def test_duplicate_skill_returns_error(tmp_path):
    spec = load_spec(tmp_path, "alpha_skill")
    duplicate = replace(spec)
    registry = SkillRegistry()

    assert registry.register(spec) == []
    errors = registry.register(duplicate)

    assert len(errors) == 1
    assert errors[0].code == "duplicate_skill"
    assert errors[0].skill_name == "alpha_skill"


def test_load_registry_collects_errors_and_continues(tmp_path):
    good_dir = write_skill(tmp_path, "good", VALID_SKILL.format(name="good_skill"))
    bad_dir = write_skill(tmp_path, "bad", INVALID_SKILL)
    other_dir = write_skill(tmp_path, "other", VALID_SKILL.format(name="other_skill"))

    result = load_skill_registry_from_dirs([good_dir, bad_dir, other_dir])

    assert result.registry.names() == ["good_skill", "other_skill"]
    assert result.loaded == ["good_skill", "other_skill"]
    assert len(result.errors) == 1
    assert result.errors[0].code == "missing_required_field"


def test_enabled_skills_filter_registry(tmp_path):
    good_dir = write_skill(tmp_path, "good", VALID_SKILL.format(name="good_skill"))
    other_dir = write_skill(tmp_path, "other", VALID_SKILL.format(name="other_skill"))

    result = load_skill_registry_from_dirs([good_dir, other_dir], enabled_skills=["other_skill"])

    assert result.ok
    assert result.registry.names() == ["other_skill"]
    assert result.loaded == ["other_skill"]


def test_unknown_enabled_skill_returns_error(tmp_path):
    good_dir = write_skill(tmp_path, "good", VALID_SKILL.format(name="good_skill"))

    result = load_skill_registry_from_dirs([good_dir], enabled_skills=["good_skill", "missing_tool"])

    assert result.registry.names() == ["good_skill"]
    assert [error.code for error in result.errors] == ["unknown_enabled_skill"]
    assert result.errors[0].skill_name == "missing_tool"


def test_builtin_skill_dirs_include_python_code_and_local_rag():
    dirs = get_builtin_skill_dirs()
    names = sorted(path.name for path in dirs)

    assert "python_code" in names
    assert "local_rag" in names

    result = load_skill_registry_from_dirs(dirs, enabled_skills=["python_code", "local_rag"])

    assert result.ok
    assert result.registry.names() == ["local_rag", "python_code"]


def test_resolve_enabled_skill_names_prefers_env_skills():
    config = {
        "env": {
            "skills": ["local_rag"],
            "informal_math": {
                "enable_python_code": True,
                "enable_local_rag": True,
            },
        }
    }

    assert resolve_enabled_skill_names(config) == ["local_rag"]


def test_resolve_enabled_skill_names_from_legacy_flags():
    config = {
        "env": {
            "informal_math": {
                "enable_python_code": True,
                "enable_local_rag": False,
            },
        }
    }

    assert resolve_enabled_skill_names(config) == ["python_code"]


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        test_register_and_get_skill(tmp_path)
        test_duplicate_skill_returns_error(tmp_path)
        test_load_registry_collects_errors_and_continues(tmp_path)
        test_enabled_skills_filter_registry(tmp_path)
        test_unknown_enabled_skill_returns_error(tmp_path)
        test_builtin_skill_dirs_include_python_code_and_local_rag()
        test_resolve_enabled_skill_names_prefers_env_skills()
        test_resolve_enabled_skill_names_from_legacy_flags()
    print("skill registry tests passed")
