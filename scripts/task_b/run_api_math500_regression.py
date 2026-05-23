"""Run Task B MATH-500 regression with an API-hosted chat model.

This runner replaces only the model-generation part of the local verl/vLLM
pipeline. Prompt rendering, skill parsing, tool execution, and reward scoring
still use the project implementation.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _enabled_skills(enable_python_code: bool, enable_local_rag: bool) -> list[str]:
    skills: list[str] = []
    if enable_python_code:
        skills.append("python_code")
    if enable_local_rag:
        skills.append("local_rag")
    return skills


def _load_tool_specs(skill_names: list[str]):
    from alphaapollo.core.skills.registry import get_builtin_skill_dirs, load_skill_registry_from_dirs

    result = load_skill_registry_from_dirs(get_builtin_skill_dirs(), enabled_skills=skill_names)
    if not result.ok:
        details = "; ".join(f"{error.code}: {error.message}" for error in result.errors)
        raise ValueError(f"Failed to load skills: {details}")
    return result.registry.specs()


def _tool_call_style(tool_prompt_format: str) -> str:
    normalized = tool_prompt_format.lower()
    if normalized in {"skill_legacy", "legacy_adapter"}:
        return "legacy"
    if normalized in {"skill_hermes", "hermes", "qwen_hermes"}:
        return "hermes"
    return "structured"


def _render_prompt(
    *,
    question: str,
    memory_context: str,
    step_count: int,
    max_steps: int,
    tool_prompt_format: str,
    enable_python_code: bool,
    enable_local_rag: bool,
) -> str:
    from alphaapollo.core.environments.prompts.informal_math_training import get_policy_training_prompt

    use_history = bool(memory_context)
    if tool_prompt_format == "legacy":
        template = get_policy_training_prompt(
            use_history=use_history,
            max_steps=max_steps,
            tool_config={
                "enable_python_code": enable_python_code,
                "enable_local_rag": enable_local_rag,
            },
        )
    else:
        skills = _enabled_skills(enable_python_code, enable_local_rag)
        template = get_policy_training_prompt(
            use_history=use_history,
            max_steps=max_steps,
            tool_specs=_load_tool_specs(skills),
            tool_call_style=_tool_call_style(tool_prompt_format),
        )

    values = {"question": question}
    if use_history:
        values.update({"memory_context": memory_context, "step_count": step_count})
    return template.format(**values)


def _make_env_config(args: argparse.Namespace):
    from omegaconf import OmegaConf

    return OmegaConf.create(
        {
            "skills": _enabled_skills(args.enable_python_code, args.enable_local_rag),
            "enable_python_code": args.enable_python_code,
            "enable_local_rag": args.enable_local_rag,
            "python_code_timeout": args.python_code_timeout,
            "log_requests": False,
        }
    )


def _row_value(row: Any, key: str, default: Any = None) -> Any:
    value = row.get(key, default)
    return value if value is not None else default


def _extra_info(row: Any) -> dict[str, Any]:
    value = _row_value(row, "extra_info", {})
    return value if isinstance(value, dict) else {}


def _reward_model(row: Any) -> dict[str, Any]:
    value = _row_value(row, "reward_model", {})
    return value if isinstance(value, dict) else {}


def _env_kwargs(row: Any) -> dict[str, Any]:
    value = _row_value(row, "env_kwargs", {})
    return value if isinstance(value, dict) else {}


def _question_and_answer(row: Any) -> tuple[str, str]:
    extra_info = _extra_info(row)
    env_kwargs = _env_kwargs(row)
    reward_model = _reward_model(row)

    question = extra_info.get("question") or env_kwargs.get("question")
    ground_truth = (
        extra_info.get("ground_truth")
        or env_kwargs.get("ground_truth")
        or reward_model.get("ground_truth")
    )
    if question is None or ground_truth is None:
        raise ValueError("Each row must contain question and ground_truth")
    return str(question), str(ground_truth)


def _history_text(messages: list[dict[str, str]]) -> str:
    parts: list[str] = []
    for message in messages:
        parts.append(str(message.get("role", "")))
        parts.append(str(message.get("content", "")))
    return "\n".join(parts).strip()


def _memory_context(messages: list[dict[str, str]]) -> str:
    if not messages:
        return ""
    return "\n\n".join(f"{item['role']}\n{item['content']}" for item in messages)


def _existing_rows(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def _run_one(row_no: int, row: Any, args: argparse.Namespace, client: Any) -> dict[str, Any]:
    from alphaapollo.core.environments.informal_math_training.env import InformalMathTrainingEnv

    question, ground_truth = _question_and_answer(row)
    extra_info = dict(_extra_info(row))
    env_kwargs = dict(_env_kwargs(row))
    data_source = str(_row_value(row, "data_source", "unknown"))

    env = InformalMathTrainingEnv(_make_env_config(args))
    env.reset(
        {
            "question": question,
            "ground_truth": ground_truth,
            "max_steps": args.max_steps,
            "data_source": data_source,
        }
    )

    messages: list[dict[str, str]] = [{"role": "user", "content": ""}]
    rewards: list[float] = []
    infos: list[Any] = []
    raw_api_responses: list[dict[str, Any]] = []

    for step_no in range(args.max_steps):
        prompt = _render_prompt(
            question=question,
            memory_context=_memory_context(messages[1:]),
            step_count=step_no,
            max_steps=args.max_steps,
            tool_prompt_format=args.tool_prompt_format,
            enable_python_code=args.enable_python_code,
            enable_local_rag=args.enable_local_rag,
        )
        messages[0] = {"role": "user", "content": prompt}

        result = client.generate(
            model=args.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            top_p=args.top_p,
        )
        assistant_output = result.text
        raw_api_responses.append(result.raw if args.save_raw_api else {})
        messages.append({"role": "assistant", "content": assistant_output})

        step_output = env.step(action=assistant_output, text_actions=assistant_output)
        rewards.append(float(step_output["reward"]))
        infos.append(step_output.get("metadata"))

        if step_output["done"]:
            break

        observations = step_output.get("observations") or []
        observation_text = "\n".join(obs.get("content", "") for obs in observations if obs)
        if observation_text:
            messages.append({"role": "user", "content": observation_text})

    return {
        "data_source": data_source,
        "prompt": _row_value(row, "prompt"),
        "ability": _row_value(row, "ability"),
        "reward_model": _reward_model(row),
        "extra_info": extra_info,
        "metadata": _row_value(row, "metadata"),
        "env_kwargs": env_kwargs or {"question": question, "ground_truth": ground_truth},
        "history": [_history_text(messages)],
        "rewards": [rewards],
        "tool_infos": infos,
        "api_model": args.model,
        "api_base_url": args.base_url,
        "tool_prompt_format": args.tool_prompt_format,
        "raw_api_responses": raw_api_responses if args.save_raw_api else None,
        "row_no": row_no,
    }


def run(args: argparse.Namespace) -> None:
    import pandas as pd
    from alphaapollo.core.generation.api_client import OpenAICompatibleChatClient

    api_key = os.environ.get(args.api_key_env) or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(f"Set {args.api_key_env} or OPENAI_API_KEY before running")

    df = pd.read_parquet(args.data)
    if args.limit is not None:
        df = df.head(args.limit)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    skip = _existing_rows(args.output) if args.resume else 0
    mode = "a" if args.resume and skip else "w"

    client = OpenAICompatibleChatClient(
        api_key=api_key,
        base_url=args.base_url,
        timeout=args.timeout,
        retries=args.retries,
    )

    with args.output.open(mode, encoding="utf-8") as handle:
        for row_no, (_, row) in enumerate(df.iterrows()):
            if row_no < skip:
                continue
            output_row = _run_one(row_no, row, args, client)
            handle.write(json.dumps(output_row, ensure_ascii=False, default=_json_default) + "\n")
            handle.flush()
            rewards = output_row["rewards"][0]
            score = max(rewards, default=0.0)
            print(f"[{row_no + 1}/{len(df)}] score={score} rewards={rewards}")


def _json_default(value: Any) -> Any:
    if hasattr(value, "tolist"):
        return value.tolist()
    if hasattr(value, "item"):
        return value.item()
    return str(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--base-url", default=os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"))
    parser.add_argument("--api-key-env", default="LLM_API_KEY")
    parser.add_argument("--tool-prompt-format", default="skill_legacy")
    parser.add_argument("--max-steps", type=int, default=2)
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--save-raw-api", action="store_true")
    parser.add_argument("--enable-python-code", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--enable-local-rag", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--python-code-timeout", type=int, default=30)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
