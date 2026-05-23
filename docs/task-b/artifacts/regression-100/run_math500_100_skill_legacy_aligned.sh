#!/usr/bin/env bash
set -euo pipefail
SUFFIX=${1:-skill_legacy_aligned}
TOOL_FORMAT=skill_legacy
PROJECT_ROOT=/root/AlphaApollo-TaskB
PY=/root/miniconda3/envs/alphaapollo/bin/python
MODEL_PATH=$PROJECT_ROOT/models/Qwen2.5-3B-Instruct
DATA_ROOT=$PROJECT_ROOT/data/task-b-regression-100
DATA_PATH=$DATA_ROOT/custom_data/test.parquet
OUT_PARQUET=$DATA_ROOT/qwen25_3b_vllm_math500_100_${SUFFIX}.parquet
OUT_JSON=$DATA_ROOT/qwen25_3b_vllm_math500_100_${SUFFIX}.json
cd "$PROJECT_ROOT"
echo "=== RUN FORMAT=$SUFFIX TOOL_FORMAT=$TOOL_FORMAT ==="
echo "HEAD=$(git rev-parse --short HEAD)"
$PY - <<PY
import pandas as pd
p = '$DATA_PATH'
df = pd.read_parquet(p)
print('rows', len(df))
print('first_indices', [row.get('index') for row in df['extra_info'].head(10).tolist()])
PY
PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/alphaapollo/core/generation" \
  "$PY" -m alphaapollo.core.generation.verl.trainer.main_generation \
    trainer.nnodes=1 \
    trainer.n_gpus_per_node=1 \
    data.path="$DATA_PATH" \
    data.prompt_key=prompt \
    data.n_samples=1 \
    data.batch_size=1 \
    data.return_raw_chat=True \
    data.truncation=right \
    data.output_path="$OUT_PARQUET" \
    data.save2json=true \
    data.json_output_path="$OUT_JSON" \
    model.path="$MODEL_PATH" \
    rollout.name=vllm \
    rollout.do_sample=false \
    rollout.temperature=0.0 \
    rollout.top_k=-1 \
    rollout.top_p=1.0 \
    rollout.prompt_length=2048 \
    rollout.response_length=1024 \
    rollout.tensor_model_parallel_size=1 \
    rollout.gpu_memory_utilization=0.65 \
    rollout.max_num_batched_tokens=4096 \
    env.env_name=informal_math_training \
    '+env.skills=[python_code]' \
    +env.tool_prompt_format="$TOOL_FORMAT" \
    env.seed=0 \
    env.max_steps=2 \
    env.history_length=2 \
    env.resources_per_worker.num_cpus=0.1 \
    env.informal_math.memory_type=simple \
    env.informal_math.log_requests=false \
    env.informal_math.python_code_timeout=30 \
    env.informal_math.enable_python_code=true \
    env.informal_math.enable_local_rag=false

echo "=== SUMMARY FORMAT=$SUFFIX ==="
ls -lh "$OUT_PARQUET" "$OUT_JSON"
$PY - <<PY
import json
from pathlib import Path
path = Path('$OUT_JSON')
rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
correct = 0
has_answer = 0
has_boxed_answer = 0
has_structured_tool = 0
has_legacy_tool = 0
for row in rows:
    rewards = row.get('rewards') or []
    def nums(value):
        if isinstance(value, (int, float)):
            return [float(value)]
        if isinstance(value, list):
            result = []
            for item in value:
                result.extend(nums(item))
            return result
        return []
    score = max(nums(rewards), default=0.0)
    correct += int(score > 0)
    hist = row.get('history') or []
    text = hist[0][0] if hist and hist[0] else ''
    assistant_fragments = text.split('assistant\n')[1:]
    generated = '\n'.join(assistant_fragments) if assistant_fragments else text
    has_answer += int('<answer>' in generated)
    has_boxed_answer += int('<answer>' in generated and '\\boxed{' in generated)
    has_structured_tool += int('<tool_call>' in generated)
    has_legacy_tool += int('<python_code>' in generated or '<local_rag>' in generated)
print('jsonl_rows', len(rows))
print('correct_count', correct)
print('accuracy', correct / len(rows) if rows else 0)
print('assistant_has_answer', has_answer)
print('assistant_answer_contains_boxed', has_boxed_answer)
print('assistant_has_structured_tool_call', has_structured_tool)
print('assistant_has_legacy_tool_tag', has_legacy_tool)
PY
