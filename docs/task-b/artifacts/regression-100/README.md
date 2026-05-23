# Task B 100 题回归实验产物

这些文件从美国 RTX 4090 实验服务器同步回来，用来在 GitHub 里轻量保存 Task B 的回归证据。

## 已包含文件

```text
qwen25_3b_vllm_math500_100_legacy.json
qwen25_3b_vllm_math500_100_skill.json
qwen25_3b_vllm_math500_100_skill_v2.json
qwen25_3b_vllm_math500_100_skill_v3.json
qwen25_3b_vllm_math500_100_skill_v4.json
qwen25_3b_vllm_math500_100_skill_v5.json
qwen25_3b_vllm_math500_100_skill_legacy.json
task_b_regression_analysis.json
task_b_regression_analysis_with_v3.json
task_b_regression_analysis_with_v4.json
task_b_regression_analysis_with_v5.json
task_b_regression_analysis_with_skill_legacy.json
run_math500_100_regression.sh
run_math500_100_skill_v2.sh
run_math500_100_skill_v3.sh
run_math500_100_skill_v4.sh
run_math500_100_skill_v5.sh
run_math500_100_skill_legacy.sh
readable/qwen25_3b_vllm_math500_100_legacy_rollouts.md
readable/qwen25_3b_vllm_math500_100_skill_rollouts.md
readable/qwen25_3b_vllm_math500_100_skill_v2_rollouts.md
readable/qwen25_3b_vllm_math500_100_skill_v3_rollouts.md
readable/qwen25_3b_vllm_math500_100_skill_v4_rollouts.md
readable/qwen25_3b_vllm_math500_100_skill_v5_rollouts.md
readable/qwen25_3b_vllm_math500_100_skill_legacy_rollouts.md
```

这些 `.json` 结果文件其实是 JSONL 文件：一行代表一道题的完整回归 rollout。每一行里都包含原始题目信息、rollout `history` 和 `rewards`。

如果直接用 VS Code 打开 JSONL，会感觉“看不到完整 rollout”，因为每道题都压在一行里。更适合阅读的是：

```text
readable/qwen25_3b_vllm_math500_100_legacy_rollouts.md
readable/qwen25_3b_vllm_math500_100_skill_rollouts.md
readable/qwen25_3b_vllm_math500_100_skill_v2_rollouts.md
readable/qwen25_3b_vllm_math500_100_skill_v3_rollouts.md
readable/qwen25_3b_vllm_math500_100_skill_v4_rollouts.md
readable/qwen25_3b_vllm_math500_100_skill_v5_rollouts.md
readable/qwen25_3b_vllm_math500_100_skill_legacy_rollouts.md
```

这些 Markdown 文件已经把 100 道题拆成 `Sample 000` 到 `Sample 099`，每题都有题目、标准答案、reward、模型输出和可展开的完整 history。

## 未包含文件

下面这些文件没有提交到仓库：

```text
custom_data/test.parquet
qwen25_3b_vllm_math500_100_*.parquet
server logs under /tmp/*.log
model files under models/
conda environment files
```

原因：

```text
仓库 .gitignore 排除了 data/ 和 *.parquet。
JSONL 输出文件体积较小，已经包含 Task B 所需的轨迹证据。
parquet 文件可以在服务器上保留，或者之后重新生成。
```

## 结果汇总

| version | avg@1 | pass@1 | corrected accuracy | note |
|---|---:|---:|---:|---|
| legacy | 0.58 | 0.58 | 0.58 | old `<python_code>` prompt |
| skill | 0.38 | 0.38 | 0.38 | structured `<tool_call>` prompt |
| skill_v2 | 0.32 | 0.32 | 0.32 | adjusted structured prompt |
| skill_v3 | 0.28 | 0.28 | 0.28 | tool-use guidance and extra examples |
| skill_v4 | 0.33 | 0.33 | 0.33 | minimized structured prompt |
| skill_v5 | 0.11 | 0.11 | 0.11 | Bad/Good adapter prompt |
| skill_legacy | 0.48 | 0.48 | 0.48 | SKILL.md-driven legacy tag prompt |

当前结论记录在：

```text
docs/task-b/experiments.md
docs/task-b/regression-analysis.md
docs/task-b/learning-log.md
```

## 固定 100 题子集

这个子集来自 MATH-500，使用 `random.Random(0)` 抽样后排序：

```text
0,7,20,31,32,37,41,46,47,48,50,51,55,71,72,75,97,104,111,113,
122,124,128,132,133,144,149,154,155,158,161,163,166,169,170,181,
183,197,204,207,215,222,226,229,241,244,248,250,252,258,260,261,
266,272,278,280,282,286,290,298,308,312,313,316,320,327,342,350,
360,361,363,368,373,386,388,401,409,411,412,414,422,423,424,430,
432,435,443,447,455,456,461,464,465,467,468,470,478,485,488,489
```

## 如何查看

方式一：看已经导出的可读版。

```text
docs/task-b/artifacts/regression-100/readable/
```

方式二：重新导出某个 JSONL 文件。

```bash
python scripts/task_b/export_rollouts.py \
  docs/task-b/artifacts/regression-100/qwen25_3b_vllm_math500_100_skill_v5.json \
  docs/task-b/artifacts/regression-100/readable/qwen25_3b_vllm_math500_100_skill_v5_rollouts.md \
  --title "Task B skill_v5 readable rollouts"
```

方式三：用 Python 快速看某一条原始 JSONL。

```bash
python - <<'PY'
import json
from pathlib import Path

path = Path("docs/task-b/artifacts/regression-100/qwen25_3b_vllm_math500_100_skill.json")
rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
i = 2
print(rows[i]["extra_info"]["question"])
print(rows[i]["extra_info"]["ground_truth"])
print(rows[i]["rewards"])
print(rows[i]["history"][0][0])
PY
```
