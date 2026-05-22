"""Registry helpers for discovered SKILL.md metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .loader import load_skill_from_dir
from .schema import SkillLoadError, SkillSpec


@dataclass(frozen=True)
class SkillRegistryError:
    """Structured error returned while building or querying a registry."""

    code: str
    message: str
    path: Path | None = None
    skill_name: str | None = None


@dataclass
class SkillRegistry:
    """In-memory mapping from skill name to validated ``SkillSpec``."""

    _skills: dict[str, SkillSpec] = field(default_factory=dict)

    def register(self, spec: SkillSpec) -> list[SkillRegistryError]:
        """Register one skill spec unless its name is already present."""

        existing = self._skills.get(spec.name)
        if existing is not None:
            return [
                SkillRegistryError(
                    code="duplicate_skill",
                    message=f"Duplicate skill name: {spec.name}",
                    path=spec.source_path,
                    skill_name=spec.name,
                )
            ]

        self._skills[spec.name] = spec
        return []

    def get(self, name: str) -> SkillSpec | None:
        """Return a skill by name, or ``None`` if it is not registered."""

        return self._skills.get(name)

    def require(self, name: str) -> SkillSpec:
        """Return a skill by name, raising ``KeyError`` if missing."""

        spec = self.get(name)
        if spec is None:
            raise KeyError(f"Unknown skill: {name}")
        return spec

    def names(self) -> list[str]:
        """Return registered skill names in stable order."""

        return sorted(self._skills)

    def specs(self) -> list[SkillSpec]:
        """Return registered skill specs in stable name order."""

        return [self._skills[name] for name in self.names()]


@dataclass(frozen=True)
class SkillRegistryLoadResult:
    """Result returned after scanning multiple skill directories."""

    registry: SkillRegistry
    loaded: list[str] = field(default_factory=list)
    errors: list[SkillRegistryError] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def get_builtin_skill_dirs() -> list[Path]:
    """Return built-in skill directories that contain a ``SKILL.md`` file."""

    builtin_root = Path(__file__).resolve().parent / "builtin"
    if not builtin_root.exists():
        return []

    return sorted(
        [path for path in builtin_root.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()]
    )


def load_skill_registry_from_dirs(
    skill_dirs: Iterable[str | Path],
    enabled_skills: Iterable[str] | None = None,
) -> SkillRegistryLoadResult:
    """Load skill directories into a registry.

    All directories are parsed so users can see malformed ``SKILL.md`` files
    early. If ``enabled_skills`` is provided, only matching valid skills are
    registered.
    """

    registry = SkillRegistry()
    errors: list[SkillRegistryError] = []
    loaded_names: list[str] = []
    discovered_names: set[str] = set()
    enabled_set = set(enabled_skills) if enabled_skills is not None else None

    for skill_dir in skill_dirs:
        path = Path(skill_dir)
        result = load_skill_from_dir(path)
        if not result.ok or result.spec is None:
            errors.extend(_loader_errors_to_registry_errors(result.errors))
            continue

        spec = result.spec
        discovered_names.add(spec.name)
        if enabled_set is not None and spec.name not in enabled_set:
            continue

        register_errors = registry.register(spec)
        if register_errors:
            errors.extend(register_errors)
            continue

        loaded_names.append(spec.name)

    if enabled_set is not None:
        for missing_name in sorted(enabled_set - discovered_names):
            errors.append(
                SkillRegistryError(
                    code="unknown_enabled_skill",
                    message=f"Enabled skill was not found: {missing_name}",
                    skill_name=missing_name,
                )
            )

    return SkillRegistryLoadResult(
        registry=registry,
        loaded=sorted(loaded_names),
        errors=errors,
    )


def resolve_enabled_skill_names(config: Any, env_section: str = "informal_math") -> list[str]:
    """Resolve enabled skill names from new ``env.skills`` or legacy flags.

    ``env.skills`` wins when present. Without it, legacy booleans under
    ``env.<env_section>`` are translated into skill names. Callers may also
    pass a direct env subsection, in which case ``skills`` and legacy flags are
    read from that object.
    """

    explicit_skills = _select_config(config, "env.skills")
    if explicit_skills is None:
        explicit_skills = _select_config(config, "skills")
    if explicit_skills is not None:
        return _normalize_skill_names(explicit_skills)

    legacy_prefix = f"env.{env_section}"
    legacy_section = _select_config(config, legacy_prefix)
    if legacy_section is None:
        legacy_section = _select_config(config, env_section)
    if legacy_section is None:
        legacy_section = config

    enabled: list[str] = []
    if bool(_select_config(config, f"{legacy_prefix}.enable_python_code")) or bool(
        _select_config(legacy_section, "enable_python_code")
    ):
        enabled.append("python_code")
    if bool(_select_config(config, f"{legacy_prefix}.enable_local_rag")) or bool(
        _select_config(legacy_section, "enable_local_rag")
    ):
        enabled.append("local_rag")
    return enabled


def _loader_errors_to_registry_errors(errors: Iterable[SkillLoadError]) -> list[SkillRegistryError]:
    return [
        SkillRegistryError(
            code=error.code,
            message=error.message,
            path=error.path,
            skill_name=None,
        )
        for error in errors
    ]


def _normalize_skill_names(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Iterable):
        return [str(item) for item in value]
    return []


def _select_config(config: Any, dotted_path: str) -> Any:
    try:
        from omegaconf import OmegaConf

        selected = OmegaConf.select(config, dotted_path, default=None)
        if selected is not None:
            return selected
    except Exception:
        pass

    current = config
    for part in dotted_path.split("."):
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)
    return current
