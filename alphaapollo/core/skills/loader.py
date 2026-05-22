"""Load and validate SKILL.md metadata files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .schema import (
    SkillEntrypoint,
    SkillExample,
    SkillLoadError,
    SkillLoadResult,
    SkillParameter,
    SkillSpec,
)

REQUIRED_TOP_LEVEL_FIELDS = {"name", "description", "parameters", "entrypoint", "examples"}
SUPPORTED_PARAMETER_TYPES = {"string", "integer", "number", "boolean", "object", "array"}
SUPPORTED_ENTRYPOINT_TYPES = {"python_function"}
SKILL_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
PYTHON_FUNCTION_PATH_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*:[A-Za-z_][A-Za-z0-9_]*$")


def load_skill_from_dir(skill_dir: str | Path) -> SkillLoadResult:
    """Load ``SKILL.md`` from a skill directory."""

    return load_skill_file(Path(skill_dir) / "SKILL.md")


def load_skill_file(skill_file: str | Path) -> SkillLoadResult:
    """Load and validate one ``SKILL.md`` file."""

    path = Path(skill_file)
    if not path.exists():
        return SkillLoadResult.failure(
            SkillLoadError(
                code="skill_file_not_found",
                message=f"Skill file not found: {path}",
                path=path,
            )
        )
    if not path.is_file():
        return SkillLoadResult.failure(
            SkillLoadError(
                code="skill_file_not_file",
                message=f"Skill path is not a file: {path}",
                path=path,
            )
        )

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return SkillLoadResult.failure(
            SkillLoadError(
                code="skill_file_read_error",
                message=f"Failed to read skill file: {exc}",
                path=path,
            )
        )

    frontmatter_result = _extract_frontmatter(text, path)
    if isinstance(frontmatter_result, SkillLoadError):
        return SkillLoadResult.failure(frontmatter_result)

    yaml_result = _parse_yaml(frontmatter_result, path)
    if isinstance(yaml_result, SkillLoadError):
        return SkillLoadResult.failure(yaml_result)

    return _build_skill_spec(yaml_result, path)


def _extract_frontmatter(text: str, path: Path) -> str | SkillLoadError:
    if not text.startswith("---"):
        return SkillLoadError(
            code="missing_frontmatter",
            message="SKILL.md must start with YAML frontmatter delimited by '---'.",
            path=path,
        )

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return SkillLoadError(
            code="missing_frontmatter",
            message="SKILL.md must start with a standalone '---' line.",
            path=path,
        )

    end_idx = None
    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = idx
            break

    if end_idx is None:
        return SkillLoadError(
            code="unterminated_frontmatter",
            message="YAML frontmatter must end with a standalone '---' line.",
            path=path,
        )

    return "\n".join(lines[1:end_idx])


def _parse_yaml(frontmatter: str, path: Path) -> dict[str, Any] | SkillLoadError:
    try:
        import yaml
    except ImportError as exc:
        return SkillLoadError(
            code="yaml_dependency_missing",
            message=f"PyYAML is required to parse SKILL.md: {exc}",
            path=path,
        )

    try:
        data = yaml.safe_load(frontmatter)
    except yaml.YAMLError as exc:
        return SkillLoadError(
            code="invalid_yaml",
            message=f"Invalid YAML frontmatter: {exc}",
            path=path,
        )

    if not isinstance(data, dict):
        return SkillLoadError(
            code="invalid_frontmatter_type",
            message="YAML frontmatter must be a mapping.",
            path=path,
        )

    return data


def _build_skill_spec(data: dict[str, Any], path: Path) -> SkillLoadResult:
    errors: list[SkillLoadError] = []
    errors.extend(_validate_top_level_fields(data, path))
    if errors:
        return SkillLoadResult.failure(errors)

    parameters = _parse_parameters(data["parameters"], path)
    entrypoint = _parse_entrypoint(data["entrypoint"], path)
    examples = _parse_examples(data["examples"], path)
    timeout = _parse_timeout(data.get("timeout"), path)

    for parsed in [parameters, entrypoint, examples, timeout]:
        if isinstance(parsed, list) and parsed and isinstance(parsed[0], SkillLoadError):
            errors.extend(parsed)
        elif isinstance(parsed, SkillLoadError):
            errors.append(parsed)

    if errors:
        return SkillLoadResult.failure(errors)

    spec = SkillSpec(
        name=data["name"],
        description=data["description"],
        parameters=parameters,
        entrypoint=entrypoint,
        examples=examples,
        source_path=path,
        timeout=timeout,
    )
    return SkillLoadResult.success(spec)


def _validate_top_level_fields(data: dict[str, Any], path: Path) -> list[SkillLoadError]:
    errors: list[SkillLoadError] = []

    for field in sorted(REQUIRED_TOP_LEVEL_FIELDS):
        if field not in data:
            errors.append(
                SkillLoadError(
                    code="missing_required_field",
                    message=f"Missing required field: {field}",
                    path=path,
                    field=field,
                )
            )

    if errors:
        return errors

    if not isinstance(data["name"], str) or not data["name"].strip():
        errors.append(_type_error(path, "name", "non-empty string"))
    elif not SKILL_NAME_RE.match(data["name"]):
        errors.append(
            SkillLoadError(
                code="invalid_field_value",
                message="Skill name must start with a lowercase letter and contain only lowercase letters, digits, and underscores.",
                path=path,
                field="name",
            )
        )

    if not isinstance(data["description"], str) or not data["description"].strip():
        errors.append(_type_error(path, "description", "non-empty string"))

    if not isinstance(data["parameters"], list):
        errors.append(_type_error(path, "parameters", "list"))

    if not isinstance(data["entrypoint"], dict):
        errors.append(_type_error(path, "entrypoint", "mapping"))

    if not isinstance(data["examples"], list):
        errors.append(_type_error(path, "examples", "list"))
    elif not data["examples"]:
        errors.append(
            SkillLoadError(
                code="invalid_field_value",
                message="Field examples must contain at least one example.",
                path=path,
                field="examples",
            )
        )

    return errors


def _parse_parameters(value: list[Any], path: Path) -> list[SkillParameter] | list[SkillLoadError]:
    errors: list[SkillLoadError] = []
    parameters: list[SkillParameter] = []

    for idx, item in enumerate(value):
        prefix = f"parameters[{idx}]"
        item_errors: list[SkillLoadError] = []
        if not isinstance(item, dict):
            errors.append(_type_error(path, prefix, "mapping"))
            continue

        for field in ["name", "type", "required", "description"]:
            if field not in item:
                item_errors.append(_missing_error(path, f"{prefix}.{field}"))

        if item_errors:
            errors.extend(item_errors)
            continue

        if not isinstance(item["name"], str) or not item["name"].strip():
            item_errors.append(_type_error(path, f"{prefix}.name", "non-empty string"))
        if not isinstance(item["type"], str):
            item_errors.append(_type_error(path, f"{prefix}.type", "string"))
        elif item["type"] not in SUPPORTED_PARAMETER_TYPES:
            item_errors.append(
                SkillLoadError(
                    code="unsupported_parameter_type",
                    message=f"Unsupported parameter type: {item['type']}",
                    path=path,
                    field=f"{prefix}.type",
                )
            )
        if not isinstance(item["required"], bool):
            item_errors.append(_type_error(path, f"{prefix}.required", "boolean"))
        if not isinstance(item["description"], str) or not item["description"].strip():
            item_errors.append(_type_error(path, f"{prefix}.description", "non-empty string"))

        if item_errors:
            errors.extend(item_errors)
            continue

        parameters.append(
            SkillParameter(
                name=item["name"],
                type=item["type"],
                required=item["required"],
                description=item["description"],
                default=item.get("default"),
            )
        )

    return errors if errors else parameters


def _parse_entrypoint(value: dict[str, Any], path: Path) -> SkillEntrypoint | SkillLoadError:
    for field in ["type", "path"]:
        if field not in value:
            return _missing_error(path, f"entrypoint.{field}")

    entrypoint_type = value["type"]
    entrypoint_path = value["path"]

    if not isinstance(entrypoint_type, str):
        return _type_error(path, "entrypoint.type", "string")
    if entrypoint_type not in SUPPORTED_ENTRYPOINT_TYPES:
        return SkillLoadError(
            code="unsupported_entrypoint_type",
            message=f"Unsupported entrypoint type: {entrypoint_type}",
            path=path,
            field="entrypoint.type",
        )
    if not isinstance(entrypoint_path, str) or not entrypoint_path.strip():
        return _type_error(path, "entrypoint.path", "non-empty string")
    if entrypoint_type == "python_function" and not PYTHON_FUNCTION_PATH_RE.match(entrypoint_path):
        return SkillLoadError(
            code="invalid_entrypoint_path",
            message="python_function entrypoint path must use 'module.path:function_name' format.",
            path=path,
            field="entrypoint.path",
        )

    return SkillEntrypoint(type=entrypoint_type, path=entrypoint_path)


def _parse_examples(value: list[Any], path: Path) -> list[SkillExample] | list[SkillLoadError]:
    errors: list[SkillLoadError] = []
    examples: list[SkillExample] = []

    for idx, item in enumerate(value):
        prefix = f"examples[{idx}]"
        if not isinstance(item, dict):
            errors.append(_type_error(path, prefix, "mapping"))
            continue
        if "arguments" not in item:
            errors.append(_missing_error(path, f"{prefix}.arguments"))
            continue
        if not isinstance(item["arguments"], dict):
            errors.append(_type_error(path, f"{prefix}.arguments", "mapping"))
            continue
        if "name" in item and item["name"] is not None and not isinstance(item["name"], str):
            errors.append(_type_error(path, f"{prefix}.name", "string"))
            continue

        examples.append(SkillExample(name=item.get("name"), arguments=item["arguments"]))

    return errors if errors else examples


def _parse_timeout(value: Any, path: Path) -> int | None | SkillLoadError:
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        return SkillLoadError(
            code="invalid_field_value",
            message="Field timeout must be a positive integer.",
            path=path,
            field="timeout",
        )
    return value


def _missing_error(path: Path, field: str) -> SkillLoadError:
    return SkillLoadError(
        code="missing_required_field",
        message=f"Missing required field: {field}",
        path=path,
        field=field,
    )


def _type_error(path: Path, field: str, expected: str) -> SkillLoadError:
    return SkillLoadError(
        code="invalid_field_type",
        message=f"Field {field} must be {expected}.",
        path=path,
        field=field,
    )
