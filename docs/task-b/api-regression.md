# Task B：API 模型回归测试方案

这份文档说明如何用 API 模型替代本地 vLLM/HF 模型，跑 Task B 的固定 100 题回归。

## 1. 这条路线替代什么

原来的本地 7B 测试链路是：

```text
MATH-500 数据
-> 本地 Qwen2.5-7B-Instruct / vLLM
-> env 解析模型输出
-> python_code / local_rag 工具执行
-> reward
-> JSONL 结果
```

API 路线变成：

```text
MATH-500 数据
-> API 模型生成文本
-> env 解析模型输出
-> python_code / local_rag 工具执行
-> reward
-> JSONL 结果
```

也就是说，API 只替代“模型生成”这一层。Skill、parser、tool、reward 仍然使用项目自己的代码。

## 2. 新增文件

```text
alphaapollo/core/generation/api_client.py
scripts/task_b/run_api_math500_regression.py
```

`api_client.py` 是一个轻量 OpenAI-compatible `/chat/completions` client。

`run_api_math500_regression.py` 是 Task B 专用 runner。

## 3. 环境变量

不要把 API key 写进代码或文档，使用环境变量：

```bash
export LLM_API_KEY="你的 API key"
export LLM_BASE_URL="https://你的服务商地址/v1"
```

如果使用 OpenAI 官方兼容接口，也可以只设置：

```bash
export OPENAI_API_KEY="你的 API key"
```

## 4. 先跑小样本 smoke test

建议先跑 5 题确认接口、prompt、tool、reward 都通：

```bash
python scripts/task_b/run_api_math500_regression.py \
  --data data/task-b-regression-100/custom_data/test.parquet \
  --output data/task-b-regression-100/api_7b_math500_5_legacy.json \
  --model qwen2.5-7b-instruct \
  --tool-prompt-format legacy \
  --limit 5
```

如果要测试 Task B 主线：

```bash
python scripts/task_b/run_api_math500_regression.py \
  --data data/task-b-regression-100/custom_data/test.parquet \
  --output data/task-b-regression-100/api_7b_math500_5_skill_legacy.json \
  --model qwen2.5-7b-instruct \
  --tool-prompt-format skill_legacy \
  --limit 5
```

## 5. 正式 100 题对比

Task A 风格 baseline：

```bash
python scripts/task_b/run_api_math500_regression.py \
  --data data/task-b-regression-100/custom_data/test.parquet \
  --output data/task-b-regression-100/api_7b_math500_100_legacy.json \
  --model qwen2.5-7b-instruct \
  --tool-prompt-format legacy
```

Task B 主线：

```bash
python scripts/task_b/run_api_math500_regression.py \
  --data data/task-b-regression-100/custom_data/test.parquet \
  --output data/task-b-regression-100/api_7b_math500_100_skill_legacy.json \
  --model qwen2.5-7b-instruct \
  --tool-prompt-format skill_legacy
```

可选 Hermes 探索分支：

```bash
python scripts/task_b/run_api_math500_regression.py \
  --data data/task-b-regression-100/custom_data/test.parquet \
  --output data/task-b-regression-100/api_7b_math500_100_skill_hermes.json \
  --model qwen2.5-7b-instruct \
  --tool-prompt-format skill_hermes
```

## 6. 断点续跑

如果 API 中途失败，可以加 `--resume`：

```bash
python scripts/task_b/run_api_math500_regression.py \
  --data data/task-b-regression-100/custom_data/test.parquet \
  --output data/task-b-regression-100/api_7b_math500_100_skill_legacy.json \
  --model qwen2.5-7b-instruct \
  --tool-prompt-format skill_legacy \
  --resume
```

runner 会读取已有 JSONL 行数，跳过已经完成的样本。

## 7. 输出怎么看

输出仍然是 JSONL：

```text
一行 = 一道题
history = prompt / assistant output / tool response
rewards = 每一步 reward
tool_infos = 工具调用解析和执行信息
```

可以复用已有可读版导出脚本：

```bash
python scripts/task_b/export_rollouts.py \
  data/task-b-regression-100/api_7b_math500_100_skill_legacy.json \
  docs/task-b/artifacts/regression-100/readable/api_7b_math500_100_skill_legacy_rollouts.md \
  --title "API 7B skill_legacy rollouts"
```

## 8. 重要边界

API 路线适合：

```text
回归测试
prompt 对比
Skill / parser / tool 行为验证
```

API 路线不适合直接做 PPO/RL 训练：

```text
普通 API 不提供训练需要的 logprob、value、梯度和权重更新。
```

因此它是 Task B 评测替代路线，不是 RL 训练替代路线。
