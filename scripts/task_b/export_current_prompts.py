"""Render current Task B prompt variants into a Markdown gallery."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from alphaapollo.core.environments.prompts.informal_math_training import get_policy_training_prompt
from alphaapollo.core.skills.registry import get_builtin_skill_dirs, load_skill_registry_from_dirs
from alphaapollo.core.skills.schema import SkillSpec


QUESTION = "Evaluate $(1+2i)6-3i$."
MEMORY_CONTEXT = """<think>I will use Python to check the arithmetic.</think>
<python_code>print((1+2j)*6-3j)</python_code>
<tool_response>{"result":"(6+9j)","status":"success"}</tool_response>"""


@dataclass(frozen=True)
class PromptCase:
    name: str
    note: str
    use_history: bool
    max_steps: int = 4
    tool_config: dict[str, bool] | None = None
    skill_names: tuple[str, ...] | None = None
    tool_call_style: str = "structured"


def _load_specs(names: Iterable[str]) -> list[SkillSpec]:
    result = load_skill_registry_from_dirs(get_builtin_skill_dirs(), enabled_skills=list(names))
    if not result.ok:
        details = "\n".join(f"- {error.path}: {error.message}" for error in result.errors)
        raise RuntimeError(f"Failed to load builtin skills:\n{details}")
    return result.registry.specs()


def _render_case(case: PromptCase) -> str:
    specs = _load_specs(case.skill_names) if case.skill_names is not None else None
    template = get_policy_training_prompt(
        use_history=case.use_history,
        max_steps=case.max_steps,
        tool_config=case.tool_config,
        tool_specs=specs,
        tool_call_style=case.tool_call_style,
    )
    values = {"question": QUESTION}
    if case.use_history:
        values.update({"step_count": 1, "memory_context": MEMORY_CONTEXT})
    return template.format(**values).strip()


def _prompt_cases() -> list[PromptCase]:
    cases: list[PromptCase] = []

    def add_pair(prefix: str, note: str, **kwargs) -> None:
        cases.append(PromptCase(f"{prefix}_no_history", note, use_history=False, **kwargs))
        cases.append(PromptCase(f"{prefix}_with_history", note, use_history=True, **kwargs))

    add_pair(
        "no_tool",
        "没有工具时的 prompt。通常对应 max_steps=1，只允许直接回答。",
        max_steps=1,
        tool_config={"enable_python_code": False, "enable_local_rag": False},
    )
    add_pair(
        "legacy_python_only",
        "Task A 风格旧手写 prompt。模型看到 <python_code> 标签；不经过 SKILL.md 自动生成说明。",
        tool_config={"enable_python_code": True, "enable_local_rag": False},
    )
    add_pair(
        "legacy_python_rag",
        "Task A 风格旧手写 prompt，同时包含 <python_code> 和 <local_rag>。",
        tool_config={"enable_python_code": True, "enable_local_rag": True},
    )
    add_pair(
        "legacy_rag_only",
        "Task A 风格旧手写 prompt，只包含 <local_rag>。",
        tool_config={"enable_python_code": False, "enable_local_rag": True},
    )
    add_pair(
        "structured_skill_python_only",
        "SKILL.md 自动生成的结构化 <tool_call> JSON prompt，只启用 python_code。",
        skill_names=("python_code",),
        tool_call_style="structured",
    )
    add_pair(
        "structured_skill_python_rag",
        "SKILL.md 自动生成的结构化 <tool_call> JSON prompt，启用 python_code 和 local_rag。",
        skill_names=("python_code", "local_rag"),
        tool_call_style="structured",
    )
    add_pair(
        "skill_legacy_adapter_python_only",
        "SKILL.md 自动生成的 legacy 标签 prompt；模型看到旧标签，内部仍转成 ToolCall。",
        skill_names=("python_code",),
        tool_call_style="legacy",
    )
    add_pair(
        "skill_legacy_adapter_python_rag",
        "SKILL.md 自动生成的 legacy 标签 prompt；模型看到旧标签，内部仍转成 ToolCall。",
        skill_names=("python_code", "local_rag"),
        tool_call_style="legacy",
    )
    add_pair(
        "skill_hermes_python_only",
        "SKILL.md 自动生成的 Hermes-like function schema prompt，只启用 python_code。",
        skill_names=("python_code",),
        tool_call_style="hermes",
    )
    add_pair(
        "skill_hermes_python_rag",
        "SKILL.md 自动生成的 Hermes-like function schema prompt，启用 python_code 和 local_rag。",
        skill_names=("python_code", "local_rag"),
        tool_call_style="hermes",
    )
    return cases


def _stats(prompt: str) -> dict[str, int]:
    return {
        "chars": len(prompt),
        "lines": len(prompt.splitlines()),
        "tool_call": prompt.count("<tool_call>"),
        "tool_calls": prompt.count("<tool_calls>"),
        "python_code": prompt.count("<python_code>"),
        "local_rag": prompt.count("<local_rag>"),
    }


def export_prompt_gallery(output_path: Path) -> None:
    rendered = [(case, _render_case(case)) for case in _prompt_cases()]

    lines: list[str] = [
        "# Task B Prompt 展示",
        "",
        "这个文件由当前代码实际渲染生成，用来展示 Task B 现在所有主要 prompt 分支。",
        "",
        f"- 示例题目：`{QUESTION}`",
        "- `no_tool`: 不允许工具，只能最终回答。",
        "- `legacy_*`: Task A 风格旧手写 prompt。",
        "- `structured_skill_*`: SKILL.md 驱动的 `<tool_call>{JSON}</tool_call>` prompt。",
        "- `skill_legacy_adapter_*`: SKILL.md 驱动的 `<python_code>` / `<local_rag>` prompt。",
        "- `skill_hermes_*`: SKILL.md 驱动的 Hermes-like function schema prompt。",
        "",
        "## 汇总表",
        "",
        "| prompt | 字符数 | 行数 | `<tool_call>` | `<tool_calls>` | `<python_code>` | `<local_rag>` |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    for case, prompt in rendered:
        stats = _stats(prompt)
        lines.append(
            f"| `{case.name}` | {stats['chars']} | {stats['lines']} | "
            f"{stats['tool_call']} | {stats['tool_calls']} | "
            f"{stats['python_code']} | {stats['local_rag']} |"
        )

    for case, prompt in rendered:
        stats = _stats(prompt)
        lines.extend(
            [
                "",
                f"## {case.name}",
                "",
                case.note,
                "",
                f"- 字符数：`{stats['chars']}`",
                f"- 行数：`{stats['lines']}`",
                "",
                "```text",
                *prompt.splitlines(),
                "```",
            ]
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(line.rstrip() for line in lines) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/task-b/prompts/current-prompt-gallery.md"),
    )
    args = parser.parse_args()
    export_prompt_gallery(args.output)


if __name__ == "__main__":
    main()
