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
服务器已能跑 1 题和 5 题 smoke/sanity test，但 alphaapollo5090 里的 vLLM 在 RTX 5090 上存在 kernel 兼容问题。
HF rollout 能跑通链路，但生成质量异常重复，不适合直接作为正式回归后端。
```

建议后续至少固定随机种子抽样 100 题，再视资源跑全量 500 题。

## 3.1 4090 服务器 vLLM 单题链路验证

### 目的

在新的 RTX 4090 服务器上验证 Task B 的真实推理链路：

```text
parquet 数据
-> Qwen2.5-3B-Instruct 本地模型
-> vLLM rollout
-> SkillSpec 自动生成 prompt
-> informal_math_training env
-> reward
-> JSON / parquet 输出
```

这一步比单元测试更接近真实使用，因为它真的加载模型、真的生成文本、真的让 env 评分。

### 服务器与模型

```text
服务器: RTX 4090
仓库: /root/AlphaApollo-TaskB
conda 环境: /root/miniconda3/envs/alphaapollo
模型: /root/AlphaApollo-TaskB/models/Qwen2.5-3B-Instruct
模型来源: ModelScope Qwen/Qwen2.5-3B-Instruct
```

国内服务器访问 Hugging Face 容易慢或超时，所以这里使用 ModelScope 下载模型。

### 运行中发现的问题

第一个问题是 vLLM 参数兼容：

```text
ValueError: top_k must be -1 (disable), or at least 1, got 0.
```

处理方式：

```bash
rollout.top_k=-1
```

通俗解释：旧配置里 `top_k=0` 在部分后端里表示“不限制”，但 vLLM 0.8.5 要求用 `-1` 表示“不限制”。

第二个问题是单样本保存结果时，`main_generation.py` 对嵌套 list 做 `np.transpose` 不稳定：

```text
ValueError: axes don't match array
```

处理方式：把保存前的转置逻辑改成显式的 Python list 转置，避免 `n_samples=1` 时 numpy 推断维度出错。

第三个问题是模型一开始只输出：

```xml
<think>...</think>
```

然后就停止，没有继续输出：

```xml
<answer>\boxed{2}</answer>
```

这会导致 env 认为本轮已经结束，然后进入评分，但因为没有最终答案，所以 reward 是 0。

处理方式：在 structured skill prompt 里补充一句：

```text
Do not stop after </think>. A response that contains only <think>...</think> is incomplete and invalid.
```

通俗解释：模型本来已经“想明白了”，但没有“交卷”。这句话是在提醒模型：写完草稿以后，还必须把最终答案写进 `<answer>`。

### 最终结果

单题输入：

```text
What is 1+1? Put the final answer in \boxed{}.
```

模型输出关键片段：

```xml
<think>Let's solve the problem step-by-step. The problem is simply to add 1 and 1 together. We can do this directly without needing any computation or external tools. </think>

<answer>\boxed{2}</answer>
```

指标：

```text
avg@1: 1.0000
pass@1: 1.0000
Reward: 1.0
```

输出文件：

```text
/root/AlphaApollo-TaskB/data/task-b-single-smoke/qwen25_3b_vllm_no_think_only.json
/root/AlphaApollo-TaskB/data/task-b-single-smoke/qwen25_3b_vllm_no_think_only.parquet
```

### 结论

Task B 的核心链路在 4090 服务器上已经跑通：

```text
SKILL.md
-> SkillSpec
-> prompt 自动生成
-> structured <tool_call> 协议保留
-> vLLM 真实生成
-> env 评分
-> 结果保存
```

下一步可以从“单题 smoke test”推进到“小样本 sanity test”，例如先跑 5 题或 10 题，再决定是否跑 MATH-500 子集回归。

## 3.2 4090 服务器 vLLM：MATH-500 5 题 Sanity Test

### 目的

在单题跑通后，继续用 MATH-500 前 5 题检查：

```text
1. vLLM 多题连续 rollout 是否稳定。
2. prompt 是否能让模型按 <answer> 或 <tool_call> 格式输出。
3. 结果能否正常保存成 JSONL / parquet。
```

### 数据

本机已有数据：

```text
data/task-b-sanity-5/custom_data/test.parquet
```

上传到服务器后路径为：

```text
/root/AlphaApollo-TaskB/data/task-b-sanity-5/custom_data/test.parquet
```

5 条样本的 ground truth：

```text
0: \left( 3, \frac{\pi}{2} \right)
1: p - q
2: \frac{14}{3}
3: 9
4: \text{Evelyn}
```

### 第一次运行：只禁止 think-only

输出文件：

```text
/root/AlphaApollo-TaskB/data/task-b-sanity-5/qwen25_3b_vllm_math500_5.json
/root/AlphaApollo-TaskB/data/task-b-sanity-5/qwen25_3b_vllm_math500_5.parquet
```

结果：

```text
avg@1: 0.4000
pass@1: 0.4000
```

观察：

```text
第 0、1 题正确。
第 2、3、4 题失败。
失败题里，模型尝试调用 python_code，但 <tool_call> 格式不稳定：
- 有的少了最外层 JSON 大括号。
- 有的写成 key-value 文本。
- 有的混入了 Markdown / HTML code 片段。
```

通俗解释：模型知道“可能要用工具”，但还没有稳定学会“工具调用必须是一整块 JSON”。

### 第二次运行：补充严格格式模板

prompt 中新增：

```text
Valid direct-answer format:
<think>...</think>
<answer>\boxed{...}</answer>

Valid tool-call format:
<think>...</think>
<tool_call>{"name":"python_code","arguments":{"code":"print(1 + 1)"}}</tool_call>

Never write tool calls as Markdown, YAML, XML attributes, or key-value text.
The content inside <tool_call> must be one JSON object enclosed in braces.
```

输出文件：

```text
/root/AlphaApollo-TaskB/data/task-b-sanity-5/qwen25_3b_vllm_math500_5_strict_format.json
/root/AlphaApollo-TaskB/data/task-b-sanity-5/qwen25_3b_vllm_math500_5_strict_format.parquet
```

结果：

```text
avg@1: 0.6000
pass@1: 0.6000
```

逐题结果：

```text
0: correct, 输出 <answer>\boxed{(3, \frac{\pi}{2})}</answer>
1: correct, 输出 <answer>\boxed{p - q}</answer>
2: wrong, 输出 <answer>\boxed{\frac{1}{2}}</answer>，正确答案是 \frac{14}{3}
3: correct, 输出 <answer>\boxed{9}</answer>
4: wrong, 输出 <answer>\boxed{\text{Carla}}</answer>，正确答案是 \text{Evelyn}
```

结论：

```text
严格格式提示后，模型输出格式明显更稳定，5 题指标从 0.4 提升到 0.6。
剩下错题主要是模型解题能力或读图能力问题，不是 Skill registry / dispatcher / env bridge 断链。
```

注意：

```text
main_generation 的 JSON 输出是 JSONL（一行一个 JSON 对象），不是一个普通 JSON 数组。
读取时要按行 json.loads，不能直接 json.loads(整个文件)。
```

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

## 5. 服务器 Sanity Test：MATH-500 5 题

### 目的

在 1 题 smoke test 后，继续验证 5 个样本连续 rollout 是否稳定。

### 数据准备

本机生成 MATH-500 前 5 题：

```bash
python -m alphaapollo.data_preprocess.prepare_custom_data \
  --data_source HuggingFaceH4/MATH-500 \
  --splits test \
  --sample_indices 0,1,2,3,4 \
  --local_dir ./data/task-b-sanity-5
```

生成数据：

```text
rows: 5
indices: [0, 1, 2, 3, 4]
answers:
  - \left( 3, \frac{\pi}{2} \right)
  - p - q
  - \frac{14}{3}
  - 9
  - \text{Evelyn}
```

服务器输入输出路径：

```text
输入数据: /home/ubuntu/AlphaApollo-TaskB/data/task-b-sanity-5/custom_data/test.parquet
贪心输出 JSON: /home/ubuntu/AlphaApollo-TaskB/data/task-b-sanity-5/skill_sanity_hf.json
采样输出 JSON: /home/ubuntu/AlphaApollo-TaskB/data/task-b-sanity-5/skill_sanity_hf_sample.json
```

### 运行结果

贪心 HF rollout：

```text
Status: completed
Rows: 5
avg@1: 0.0000
pass@1: 0.0000
rewards: [0.0, 0.0, 0.0, 0.0, 0.0]
prompt_has_tool_call: 5 / 5
assistant_tool_calls: 0 / 5
assistant_answers: 0 / 5
```

采样 HF rollout，参数参考官方脚本：

```text
temperature: 0.6
top_k: 20
top_p: 0.95
```

结果：

```text
Status: completed
Rows: 5
avg@1: 0.0000
pass@1: 0.0000
rewards: [0.0, 0.0, 0.0, 0.0, 0.0]
prompt_has_tool_call: 5 / 5
assistant_tool_calls: 0 / 5
assistant_answers: 0 / 5
```

### 结论

这次 5 题 sanity test 证明：

```text
数据 parquet -> 模型加载 -> env -> reward -> JSON/parquet 保存
```

这条链路可以连续跑多个样本。

但它也暴露了一个新问题：

```text
HF rollout 的模型输出严重重复，没有稳定生成 <answer> 或 <tool_call>。
```

因此，不建议直接用当前 HF rollout 跑 20/100 题回归。否则大概率只是得到更多 0 分重复文本，对 Task B 回归没有解释力。

## 6. 推理后端排查

### 本地模型文件是否正常

在服务器上直接用 transformers 读取同一个本地模型：

```text
/home/ubuntu/wjx/AlphaApollo/models/Qwen2.5-3B-Instruct
```

最小生成测试输出正常，能自然回答极坐标问题。因此：

```text
模型文件本身没有明显损坏。
```

### alphaapollo5090 的 vLLM 状态

`alphaapollo5090` 环境：

```text
torch 2.8.0+cu128
vllm 0.10.2
```

运行 AlphaApollo vLLM rollout 时失败：

```text
CUDA error: no kernel image is available for execution on the device
```

### 独立 vllm 环境状态

服务器还有一个 `vllm` conda 环境：

```text
/home/ubuntu/miniconda3/envs/vllm/bin/python
torch 2.11.0+cu130
vllm 0.20.0
transformers 5.9.0
CUDA 可用: True
```

这个环境可以直接用 vLLM 跑本地 Qwen 模型，输出正常。

但它缺少 AlphaApollo 运行依赖：

```text
ray: False
datasets: False
omegaconf: False
pandas: False
pyarrow: False
tensordict: False
accelerate: False
codetiming: False
hydra: False
```

### 当前判断

最稳的下一步不是继续跑 20 题，而是先准备一个真正可用于 AlphaApollo 的 vLLM 环境：

```text
保留 vllm 环境中适配 RTX 5090 的 torch/vllm，
补齐 AlphaApollo 需要的 ray/datasets/omegaconf/pandas/pyarrow 等依赖，
然后重新跑 5 题 sanity。
```

如果新的 vLLM-AlphaApollo 环境能跑通 5 题并生成正常答案，再继续：

```text
5 题 sanity -> 20 题 mini regression -> 100 题正式子集回归
```

## 7. 建议回归入口

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
2. alphaapollo5090 中的 vLLM 在 RTX 5090 上 kernel 不兼容。
3. HF rollout 能跑但输出异常重复，不适合作为正式回归。
4. 独立 vllm 环境能正常推理，但需要补齐 AlphaApollo 运行依赖。
```
