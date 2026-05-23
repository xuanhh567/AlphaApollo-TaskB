"""Data structures for SKILL.md metadata.

These classes are the internal contract between the SKILL.md loader and later
components such as the registry, dispatcher, and prompt renderer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SkillParameter:
    """One argument accepted by a skill."""

    name: str
    type: str
    required: bool
    description: str
    default: Any = None


@dataclass(frozen=True)
class SkillEntrypoint:
    """Where the dispatcher should execute a skill after validation."""

    type: str
    path: str


@dataclass(frozen=True)
class SkillExample:
    """A sample argument payload used for docs and prompt generation."""

    arguments: dict[str, Any]
    name: str | None = None


@dataclass(frozen=True)
class SkillLegacyCall:
    """Backward-compatible text tag accepted for a skill call."""

    tag: str
    input_format: str
    argument: str | None = None


@dataclass(frozen=True)
class SkillSpec:
    """Validated metadata for one skill."""

    name: str
    description: str
    parameters: list[SkillParameter]
    entrypoint: SkillEntrypoint
    examples: list[SkillExample]
    source_path: Path
    timeout: int | None = None
    legacy_calls: list[SkillLegacyCall] = field(default_factory=list)


@dataclass(frozen=True)
class SkillLoadError:
    """Structured error returned when a SKILL.md file cannot be loaded."""

    code: str
    message: str
    path: Path | None = None
    field: str | None = None


@dataclass(frozen=True)
class SkillLoadResult:
    """Result wrapper for SKILL.md loading.

    A successful result has ``ok=True`` and ``spec`` populated. A failed result
    has ``ok=False`` and one or more structured ``errors``.
    """

    ok: bool
    spec: SkillSpec | None = None
    errors: list[SkillLoadError] = field(default_factory=list)

    @classmethod
    def success(cls, spec: SkillSpec) -> "SkillLoadResult":
        return cls(ok=True, spec=spec)

    @classmethod
    def failure(cls, errors: list[SkillLoadError] | SkillLoadError) -> "SkillLoadResult":
        if isinstance(errors, SkillLoadError):
            errors = [errors]
        return cls(ok=False, errors=errors)
