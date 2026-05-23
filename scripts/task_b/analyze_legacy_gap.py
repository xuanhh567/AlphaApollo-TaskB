"""Compare legacy and skill_legacy Task B regression artifacts.

The output is intentionally lightweight Markdown so it can be committed as
evidence for prompt/debug decisions.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RowSummary:
    row_no: int
    dataset_index: int
    question: str
    ground_truth: str
    correct: bool
    assistant: str
    has_answer: bool
    answer_has_boxed: bool
    has_python_code: bool
    history_has_tool_response: bool
    no_action: bool


def _flatten(value: Any) -> list[Any]:
    if isinstance(value, list):
        result: list[Any] = []
        for item in value:
            result.extend(_flatten(item))
        return result
    if value is None:
        return []
    return [value]


def _is_correct(row: dict[str, Any]) -> bool:
    values = _flatten(row.get("rewards"))
    return any(isinstance(value, (int, float)) and value > 0 for value in values)


def _history_text(row: dict[str, Any]) -> str:
    history = row.get("history")
    if not isinstance(history, list):
        return str(history or "")

    parts: list[str] = []
    for item in history:
        if isinstance(item, list):
            parts.append("\n\n".join(str(part) for part in item))
        else:
            parts.append(str(item))
    return "\n\n".join(parts)


def _assistant_output(row: dict[str, Any]) -> str:
    text = _history_text(row)
    marker = "\nassistant\n"
    if marker not in text:
        return text.strip()
    return text.rsplit(marker, 1)[-1].strip()


def _summarize(row_no: int, row: dict[str, Any]) -> RowSummary:
    assistant = _assistant_output(row)
    history = _history_text(row)
    extra_info = row.get("extra_info") or {}
    env_kwargs = row.get("env_kwargs") or {}
    question = extra_info.get("question") or env_kwargs.get("question") or ""
    ground_truth = (
        extra_info.get("ground_truth")
        or env_kwargs.get("ground_truth")
        or (row.get("reward_model") or {}).get("ground_truth")
        or ""
    )
    has_answer = "<answer>" in assistant
    has_python_code = "<python_code>" in assistant
    return RowSummary(
        row_no=row_no,
        dataset_index=int(extra_info.get("index", row_no)),
        question=str(question),
        ground_truth=str(ground_truth),
        correct=_is_correct(row),
        assistant=assistant,
        has_answer=has_answer,
        answer_has_boxed=bool(re.search(r"<answer>.*?\\boxed\s*\{", assistant, flags=re.DOTALL)),
        has_python_code=has_python_code,
        history_has_tool_response="<tool_response>" in history,
        no_action=not has_answer and not has_python_code,
    )


def _load(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _short(text: str, limit: int = 220) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


def _count(rows: list[RowSummary], attr: str) -> int:
    return sum(1 for row in rows if getattr(row, attr))


def write_report(legacy_path: Path, skill_legacy_path: Path, output_path: Path) -> None:
    legacy_rows = [_summarize(i, row) for i, row in enumerate(_load(legacy_path))]
    skill_rows = [_summarize(i, row) for i, row in enumerate(_load(skill_legacy_path))]

    if len(legacy_rows) != len(skill_rows):
        raise ValueError("legacy and skill_legacy files must contain the same number of rows")

    both_correct = []
    legacy_only = []
    skill_only = []
    both_wrong = []
    for legacy, skill in zip(legacy_rows, skill_rows, strict=True):
        if legacy.correct and skill.correct:
            both_correct.append((legacy, skill))
        elif legacy.correct and not skill.correct:
            legacy_only.append((legacy, skill))
        elif not legacy.correct and skill.correct:
            skill_only.append((legacy, skill))
        else:
            both_wrong.append((legacy, skill))

    lines = [
        "# Legacy vs Skill Legacy 差异分析",
        "",
        "这份报告比较固定 100 题中旧 `<python_code>` baseline 和 `skill_legacy` 的结果。",
        "",
        "## 总览",
        "",
        "| 类型 | 数量 |",
        "|---|---:|",
        f"| legacy 对，skill_legacy 也对 | {len(both_correct)} |",
        f"| legacy 对，skill_legacy 错 | {len(legacy_only)} |",
        f"| legacy 错，skill_legacy 对 | {len(skill_only)} |",
        f"| legacy 错，skill_legacy 也错 | {len(both_wrong)} |",
        "",
        "## 行为统计",
        "",
        "| 版本 | answer 数 | answer 含 boxed | assistant 含 python_code | history 含 tool_response | 无动作 |",
        "|---|---:|---:|---:|---:|---:|",
        (
            f"| legacy | {_count(legacy_rows, 'has_answer')} | {_count(legacy_rows, 'answer_has_boxed')} | "
            f"{_count(legacy_rows, 'has_python_code')} | {_count(legacy_rows, 'history_has_tool_response')} | "
            f"{_count(legacy_rows, 'no_action')} |"
        ),
        (
            f"| skill_legacy | {_count(skill_rows, 'has_answer')} | {_count(skill_rows, 'answer_has_boxed')} | "
            f"{_count(skill_rows, 'has_python_code')} | {_count(skill_rows, 'history_has_tool_response')} | "
            f"{_count(skill_rows, 'no_action')} |"
        ),
        "",
        "## 最需要看的样本：legacy 对，skill_legacy 错",
        "",
        "| row | dataset index | ground truth | legacy 行为 | skill_legacy 行为 | skill_legacy 输出摘要 |",
        "|---:|---:|---|---|---|---|",
    ]

    for legacy, skill in legacy_only:
        legacy_behavior = _behavior_label(legacy)
        skill_behavior = _behavior_label(skill)
        lines.append(
            f"| {legacy.row_no} | {legacy.dataset_index} | `{legacy.ground_truth}` | "
            f"{legacy_behavior} | {skill_behavior} | {_short(skill.assistant)} |"
        )

    lines.extend(
        [
            "",
            "## 反向样本：legacy 错，skill_legacy 对",
            "",
            "| row | dataset index | ground truth | legacy 行为 | skill_legacy 行为 | skill_legacy 输出摘要 |",
            "|---:|---:|---|---|---|---|",
        ]
    )

    for legacy, skill in skill_only:
        lines.append(
            f"| {legacy.row_no} | {legacy.dataset_index} | `{skill.ground_truth}` | "
            f"{_behavior_label(legacy)} | {_behavior_label(skill)} | {_short(skill.assistant)} |"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _behavior_label(row: RowSummary) -> str:
    parts: list[str] = []
    if row.has_answer:
        parts.append("answer")
    if row.answer_has_boxed:
        parts.append("boxed")
    if row.has_python_code:
        parts.append("python_code")
    if row.history_has_tool_response:
        parts.append("tool_response")
    if row.no_action:
        parts.append("no_action")
    return ", ".join(parts) or "unknown"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy", type=Path, required=True)
    parser.add_argument("--skill-legacy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_report(args.legacy, args.skill_legacy, args.output)


if __name__ == "__main__":
    main()
