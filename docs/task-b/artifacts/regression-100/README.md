# Task B 100-Question Regression Artifacts

> These files are copied from the US RTX 4090 experiment server for lightweight GitHub archival.

## Included

```text
qwen25_3b_vllm_math500_100_legacy.json
qwen25_3b_vllm_math500_100_skill.json
qwen25_3b_vllm_math500_100_skill_v2.json
qwen25_3b_vllm_math500_100_skill_v3.json
task_b_regression_analysis.json
task_b_regression_analysis_with_v3.json
run_math500_100_regression.sh
run_math500_100_skill_v2.sh
run_math500_100_skill_v3.sh
```

The `.json` result files are JSONL files: one JSON object per line. Each row includes the original prompt metadata, rollout `history`, and `rewards`.

## Not Included

The following files were intentionally not committed:

```text
custom_data/test.parquet
qwen25_3b_vllm_math500_100_*.parquet
server logs under /tmp/*.log
model files under models/
conda environment files
```

Reason:

```text
The repository .gitignore excludes data/ and *.parquet.
The JSONL outputs are small enough for review and contain the trajectory evidence needed for Task B.
The parquet files can be regenerated or kept on the experiment server.
```

## Result Summary

| version | avg@1 | pass@1 | corrected accuracy | note |
|---|---:|---:|---:|---|
| legacy | 0.58 | 0.58 | 0.58 | old `<python_code>` prompt |
| skill | 0.38 | 0.38 | 0.38 | structured `<tool_call>` prompt |
| skill_v2 | 0.32 | 0.32 | 0.32 | adjusted structured prompt |
| skill_v3 | 0.28 | 0.28 | 0.28 | tool-use guidance and extra examples |

The current conclusion is documented in:

```text
docs/task-b/experiments.md
docs/task-b/regression-analysis.md
docs/task-b/learning-log.md
```

## Fixed 100-Sample Subset

The subset was sampled from MATH-500 with `random.Random(0)` and sorted:

```text
0,7,20,31,32,37,41,46,47,48,50,51,55,71,72,75,97,104,111,113,
122,124,128,132,133,144,149,154,155,158,161,163,166,169,170,181,
183,197,204,207,215,222,226,229,241,244,248,250,252,258,260,261,
266,272,278,280,282,286,290,298,308,312,313,316,320,327,342,350,
360,361,363,368,373,386,388,401,409,411,412,414,422,423,424,430,
432,435,443,447,455,456,461,464,465,467,468,470,478,485,488,489
```

## How To Inspect

Example:

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
