# Task B 实验记录

> 这里记录 Task B 的验证命令、trajectory 样例、回归计划和当前状态。

## 1. Smoke Test：Structured Python Code

### 目的

验证结构化 tool call 主线是否能端到端工作：

```text
auto-generated prompt
-> structured <tool_call>
-> dispatcher runtime executor
-> InformalMathToolGroup
-> <tool_response>
```

### 样例文件

```text
docs/task-b/trajectories/structured-python-code-smoke.md
```

### 结果

```text
Status: passed
Tool: python_code
Action format: structured <tool_call>
Observation: <tool_response>{"result": "2\n", "stderr": "", "status": "success", "returncode": 0}</tool_response>
Metadata: tool_call_format = structured, score = 1
```

## 2. 单元测试

当前已通过：

```bash
python tests/test_skill_prompt_renderer.py
python tests/test_informal_math_skill_bridge.py
python tests/test_skill_dispatcher.py
python tests/test_skill_argument_validation.py
python tests/test_tool_call_parser.py
python tests/test_skill_registry.py
python tests/test_skill_loader.py
```

编译检查：

```bash
python -m py_compile alphaapollo/core/skills/schema.py alphaapollo/core/skills/loader.py alphaapollo/core/skills/registry.py alphaapollo/core/skills/call_parser.py alphaapollo/core/skills/validation.py alphaapollo/core/skills/dispatcher.py alphaapollo/core/skills/prompt.py alphaapollo/core/skills/__init__.py alphaapollo/core/environments/informal_math_training/skill_bridge.py alphaapollo/core/environments/informal_math_training/env.py alphaapollo/core/environments/prompts/informal_math_training.py alphaapollo/core/environments/env_manager.py
```

## 3. MATH-500 回归状态

| 项目 | 数据集 | 状态 | 结果 |
|---|---|---|---|
| Task A baseline | MATH-500 | Pending | 未运行 |
| Task B skill version | MATH-500 | Pending | 未运行 |
| 指标差值 | MATH-500 | Pending | 未计算 |

当前没有完成正式回归的原因：

```text
MATH-500 正式回归需要稳定的数据、模型推理后端和较长运行时间。
服务器已能跑 1 题 smoke test，但 vLLM 在 RTX 5090 上存在 kernel 兼容问题，正式回归需要先确定使用 HF rollout 还是修复 vLLM 环境。
```

建议后续至少固定随机种子抽样 100 题，再视资源跑全量 500 题。

## 4. 服务器 Smoke Test：MATH-500 1 题

### 目的

验证真实服务器上能跑通最小评测链路：

```text
MATH-500 parquet
-> Qwen2.5-3B-Instruct 本地模型
-> auto-generated structured tool prompt
-> informal_math_training env
-> reward
-> JSON / parquet 输出
```

这一步不是正式指标，只是检查“能不能跑通”。

### 服务器路径

```text
仓库: /home/ubuntu/AlphaApollo-TaskB
模型: /home/ubuntu/wjx/AlphaApollo/models/Qwen2.5-3B-Instruct
环境: /home/ubuntu/miniconda3/envs/alphaapollo5090/bin/python
输入数据: /home/ubuntu/AlphaApollo-TaskB/data/task-b-smoke/custom_data/test.parquet
输出 JSON: /home/ubuntu/AlphaApollo-TaskB/data/task-b-smoke/skill_smoke_hf.json
输出 parquet: /home/ubuntu/AlphaApollo-TaskB/data/task-b-smoke/skill_smoke_hf.parquet
```

### 数据准备

服务器访问 Hugging Face 时出现超时：

```text
HTTPSConnectionPool(host='huggingface.co', port=443): connect timeout
```

所以先在本机用 `prepare_custom_data` 生成 MATH-500 第 0 题，再传到服务器：

```bash
python -m alphaapollo.data_preprocess.prepare_custom_data \
  --data_source HuggingFaceH4/MATH-500 \
  --splits test \
  --sample_indices 0 \
  --local_dir ./data/task-b-smoke
```

生成的数据：

```text
rows: 1
index: 0
ground_truth: \left( 3, \frac{\pi}{2} \right)
```

### vLLM 尝试结果

使用 `rollout.name=vllm` 时遇到两个环境问题：

```text
1. vLLM 0.10.2 要求 limit_mm_per_prompt 不能是 None。
   临时绕法: +rollout.limit_images=1

2. 继续运行后，RTX 5090 上报:
   CUDA error: no kernel image is available for execution on the device
```

通俗理解：

```text
当前 vLLM / CUDA kernel 没有正确适配 RTX 5090 的 SM 12 架构。
这不是 Task B dispatcher / skill 代码的问题，而是推理后端环境问题。
```

### HF Rollout 成功命令

改用 HuggingFace rollout 后，1 题 smoke test 跑通：

```bash
CUDA_VISIBLE_DEVICES=0 \
PYTHONPATH=/home/ubuntu/AlphaApollo-TaskB:/home/ubuntu/AlphaApollo-TaskB/alphaapollo/core/generation \
/home/ubuntu/miniconda3/envs/alphaapollo5090/bin/python \
  -m alphaapollo.core.generation.verl.trainer.main_generation \
  trainer.nnodes=1 \
  trainer.n_gpus_per_node=1 \
  data.path=/home/ubuntu/AlphaApollo-TaskB/data/task-b-smoke/custom_data/test.parquet \
  data.prompt_key=prompt \
  data.n_samples=1 \
  data.batch_size=1 \
  data.return_raw_chat=True \
  data.truncation=right \
  data.output_path=/home/ubuntu/AlphaApollo-TaskB/data/task-b-smoke/skill_smoke_hf.parquet \
  data.save2json=true \
  data.json_output_path=/home/ubuntu/AlphaApollo-TaskB/data/task-b-smoke/skill_smoke_hf.json \
  model.path=/home/ubuntu/wjx/AlphaApollo/models/Qwen2.5-3B-Instruct \
  rollout.name=hf \
  rollout.do_sample=false \
  rollout.temperature=1.0 \
  rollout.top_k=0 \
  rollout.prompt_length=2048 \
  rollout.response_length=256 \
  rollout.tensor_model_parallel_size=1 \
  env.env_name=informal_math_training \
  env.seed=0 \
  env.max_steps=2 \
  env.history_length=2 \
  env.resources_per_worker.num_cpus=0.1 \
  env.informal_math.memory_type=simple \
  env.informal_math.log_requests=false \
  env.informal_math.python_code_timeout=30 \
  env.informal_math.enable_python_code=true \
  env.informal_math.enable_local_rag=false
```

### Smoke Test 结果

```text
Status: passed
Dataset rows: 1
avg@1: 0.0000
pass@1: 0.0000
Reward: [[0.0]]
```

`avg@1=0` 不代表 Task B 失败。原因是：

- 只跑了 1 道题。
- `response_length=256` 很短。
- 模型输出中途开始重复，没有给出最终正确答案。
- 这个 smoke test 的目的只是验证链路，不是报告正式准确率。

### 关键观察

输出 JSON 的 `history` 中已经包含由 registry / `SKILL.md` 自动生成的 structured tool prompt：

```text
Available tools:

1. python_code: Execute Python code for math reasoning and return stdout, stderr, return code, and status.
Parameters:
   - code (string, required): Python code to execute.
Examples:
   - compute arithmetic: <tool_call>{"name":"python_code","arguments":{"code":"print(1 + 1)"}}</tool_call>
```

这说明真实 rollout 里已经不是旧的手写 `<python_code>` prompt，而是新的 SkillSpec 自动生成 prompt。

## 5. 建议回归入口

Task B 主线配置：

```text
examples/configs/rl_informal_math_tool.yaml
```

需要重点确认：

```text
env.env_name=informal_math_training
env.max_steps=4
env.informal_math.enable_python_code=true
env.informal_math.enable_local_rag=false
```

后续补充：

```text
Task A baseline 命令
Task B skill version 命令
运行日志路径
评估 JSON 路径
最终 accuracy / pass rate
```

正式回归前建议先解决或绕开：

```text
1. 服务器访问 Hugging Face 数据源超时。
2. vLLM 在 RTX 5090 上 kernel 不兼容。
3. 如果继续用 HF rollout，需要评估速度是否能接受 100 题以上回归。
```
