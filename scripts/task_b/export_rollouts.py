"""Export Task B JSONL rollout artifacts into readable Markdown.

The regression artifacts are JSONL files: one complete sample per line.
This script keeps the original data intact and creates a human-readable
Markdown view for debugging prompt/output/reward behavior.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, indent=2)


def _assistant_output(history_text: str) -> str:
    marker = "\nassistant\n"
    if marker not in history_text:
        return history_text
    return history_text.rsplit(marker, 1)[-1].strip()


def _iter_history_texts(history: Any) -> list[str]:
    """Normalize several possible history shapes into printable strings."""
    if not isinstance(history, list):
        return [_text(history)]

    texts: list[str] = []
    for item in history:
        if isinstance(item, list):
            texts.append("\n\n".join(_text(part) for part in item))
        else:
            texts.append(_text(item))
    return texts


def export_rollouts(input_path: Path, output_path: Path, title: str) -> None:
    rows = [
        json.loads(line)
        for line in input_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    lines: list[str] = [
        f"# {title}",
        "",
        f"- Source: `{input_path}`",
        f"- Samples: `{len(rows)}`",
        "",
        "说明：这里展示的是回归测试 rollout，不是 PPO 训练时每个 batch 的参数更新日志。"
        "每个样本里最重要的是 `history` 和 `rewards`。",
        "",
    ]

    for row_no, row in enumerate(rows):
        extra_info = row.get("extra_info") or {}
        reward_model = row.get("reward_model") or {}
        histories = _iter_history_texts(row.get("history"))
        rewards = row.get("rewards")
        question = extra_info.get("question") or row.get("env_kwargs", {}).get("question")
        ground_truth = (
            extra_info.get("ground_truth")
            or row.get("env_kwargs", {}).get("ground_truth")
            or reward_model.get("ground_truth")
        )
        dataset_index = extra_info.get("index", row_no)

        lines.extend(
            [
                f"## Sample {row_no:03d} / dataset index {dataset_index}",
                "",
                f"- Reward: `{_text(rewards)}`",
                f"- Ground truth: `{ground_truth}`",
                "",
                "### Question",
                "",
                _text(question),
                "",
            ]
        )

        for history_no, history_text in enumerate(histories):
            lines.extend(
                [
                    f"### Trajectory {history_no}",
                    "",
                    "#### Assistant Output",
                    "",
                    "```text",
                    _assistant_output(history_text),
                    "```",
                    "",
                    "<details>",
                    "<summary>完整 history</summary>",
                    "",
                    "```text",
                    history_text,
                    "```",
                    "",
                    "</details>",
                    "",
                ]
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--title", default="Task B Rollouts")
    args = parser.parse_args()

    export_rollouts(args.input, args.output, args.title)


if __name__ == "__main__":
    main()
