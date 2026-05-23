"""Export Task B JSONL rollout artifacts into readable Markdown.

The regression artifacts are JSONL files: one complete sample per line.
This script keeps the original data intact and creates a human-readable
Markdown view for debugging prompt/output/reward behavior.
"""

from __future__ import annotations

import argparse
import json
import re
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


def _math_friendly_markdown(text: str) -> str:
    """Make model text easier to read in Markdown preview.

    Raw rollouts must stay untouched, but the reading view should render common
    LaTeX delimiters instead of showing everything as escaped source text.
    """
    replacements = {
        "\\\\(": "\\(",
        "\\\\)": "\\)",
        "\\\\[": "\\[",
        "\\\\]": "\\]",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(
        r"\\\\(?=(frac|sqrt|left|right|mathbf|cdot|theta|cos|arccos|boxed|pi|quad|circ|le|ge|infty|text|begin|end)\b)",
        r"\\",
        text,
    )
    text = re.sub(
        r"\\\[(.*?)\\\]",
        lambda match: "\n\n$$\n" + match.group(1).strip() + "\n$$\n\n",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"\\\((.*?)\\\)",
        lambda match: "$" + match.group(1).strip() + "$",
        text,
        flags=re.DOTALL,
    )
    return text.replace("<", "&lt;").replace(">", "&gt;")


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
        "阅读提示：`Assistant Output` 是渲染友好版本，方便看数学公式；"
        "`原始 Assistant Output` 和 `完整 history` 保留未经修改的原始文本，方便调试。",
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
            assistant_output = _assistant_output(history_text)
            lines.extend(
                [
                    f"### Trajectory {history_no}",
                    "",
                    "#### Assistant Output",
                    "",
                    _math_friendly_markdown(assistant_output),
                    "",
                    "<details>",
                    "<summary>原始 Assistant Output</summary>",
                    "",
                    "```text",
                    assistant_output,
                    "```",
                    "",
                    "</details>",
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
    content = "\n".join(lines)
    output_path.write_text(
        "\n".join(line.rstrip() for line in content.splitlines()) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--title", default="Task B Rollouts")
    args = parser.parse_args()

    export_rollouts(args.input, args.output, args.title)


if __name__ == "__main__":
    main()
