# Task B：3B 实验整理与 7B 测试交接

这份文档用于迁移服务器前后快速确认：

```text
1. 3B 实验哪些结果是正式证据。
2. 3B 数据和文档分别放在哪里。
3. 下一步 7B 模型应该跑哪几组对比。
```

## 1. 当前 3B 主结论

当前固定 100 题 MATH-500 回归里，最重要的对比是：

| 版本 | 模型 | prompt / tool 形式 | 正确数 | accuracy | 是否通过 B6 |
|---|---|---|---:|---:|---|
| Task A baseline `legacy` | Qwen2.5-3B-Instruct | 旧 `<python_code>` prompt | 58 / 100 | 0.58 | 作为基线 |
| Task B `skill_legacy_aligned` | Qwen2.5-3B-Instruct | `SKILL.md` 驱动旧标签 prompt，内部转 `ToolCall` | 62 / 100 | 0.62 | 通过 |

MiniProject 要求：

```text
Task B 相对 Task A baseline 不得回退超过 3%。
```

现在：

```text
0.62 - 0.58 = +0.04
```

所以 3B 的固定 100 题回归已经满足 B6 前置门槛。

## 2. 3B 全部实验结果

| 版本 | accuracy | 作用 | 结论 |
|---|---:|---|---|
| `legacy` | 0.58 | Task A 风格旧基线 | 需要对齐的对象 |
| `skill` | 0.38 | 初版 structured `<tool_call>` | 退化明显 |
| `skill_v2` | 0.32 | 强调工具优先 | 继续退化 |
| `skill_v3` | 0.28 | 加长说明和 examples | 说明堆太多无效 |
| `skill_v4` | 0.33 | 精简 structured prompt | 有回升但不够 |
| `skill_v5` | 0.11 | Bad/Good 格式纠偏 | 诱导模型照抄，失败 |
| `skill_legacy` | 0.48 | SKILL.md 驱动旧标签 | 明显改善但仍未过 |
| `skill_legacy_aligned` | 0.62 | 去掉多余内联例子，贴近旧 prompt | 主线通过 |
| `skill_hermes` | 0.44 | Hermes-like function schema | 有帮助但不如 legacy adapter |
| `skill_hermes_boxed` | 0.44 | Hermes-like + 强调 boxed | 格式改善，分数不变 |

通俗理解：

```text
3B 模型不是不会做数学，而是不稳定输出严格 JSON tool call。
把工具说明做成现代 structured JSON 后，它经常写错格式。
把模型侧格式保持为熟悉的 <python_code>，但内部仍走 SKILL.md / registry / dispatcher，效果最好。
```

## 3. 3B 证据文件地图

### 正式结果 JSONL

位置：

```text
docs/task-b/artifacts/regression-100/
```

关键文件：

```text
qwen25_3b_vllm_math500_100_legacy.json
qwen25_3b_vllm_math500_100_skill_legacy_aligned.json
task_b_regression_analysis_with_skill_legacy_aligned.json
```

说明：

```text
这些 .json 文件实际是 JSONL。
一行是一道题，里面有 question、ground_truth、history、rewards。
```

### 可读 rollout

位置：

```text
docs/task-b/artifacts/regression-100/readable/
```

最重要的两份：

```text
qwen25_3b_vllm_math500_100_legacy_rollouts.md
qwen25_3b_vllm_math500_100_skill_legacy_aligned_rollouts.md
```

用途：

```text
人工查看每道题模型到底怎么答、有没有调用工具、reward 是多少。
```

### 分析文档

重点阅读顺序：

```text
1. docs/task-b/regression-analysis.md
2. docs/task-b/legacy-vs-skill-legacy-analysis.md
3. docs/task-b/legacy-vs-skill-legacy-aligned-analysis.md
4. docs/task-b/prompts/current-prompt-gallery.md
5. docs/task-b/experiments.md
6. docs/task-b/learning-log.md
```

### 服务器原始 parquet

本地已备份：

```text
docs/task-b/artifacts/regression-100/qwen25_3b_vllm_math500_100_*.parquet
```

但这些文件被 `.gitignore` 忽略，不上传 GitHub。GitHub 上保留的是更轻量、可读性更好的 JSONL / Markdown / 分析文档。

## 4. 3B 实验里最值得保留的判断

### 判断 1：不要用最初 structured `skill` 当主线

它是 Task B 新系统最直观的实现，但 3B 上分数只有 0.38。

原因不是 parser 完全坏了，而是模型经常输出：

```text
<tool_call>python_code ...
<tool_call> name: python_code
<tool_call>...</tool_call>
未闭合 JSON
双重 <tool_call>
```

这些都不是严格 JSON tool call。

### 判断 2：`skill_legacy_aligned` 是当前主线

它满足“现有 python_code / local_rag 改写为 SKILL.md skill，行为不变”的精神：

```text
模型看到的仍接近旧 <python_code> 标签。
工具定义来自 SKILL.md。
环境内部解析成统一 ToolCall。
后续执行走 registry / dispatcher。
```

这比强迫 3B 立刻学会新 JSON 格式更稳定。

### 判断 3：Hermes 是探索分支，不是当前主线

`skill_hermes` 参考 Qwen / vLLM 的 Hermes-style tool use，但 3B 结果只有 0.44。

它可以作为未来优化方向，但目前不应替代已经通过的 `skill_legacy_aligned`。

## 5. 下一步 7B 应该怎么测

7B 测试的目标不是重新探索所有 prompt，而是验证：

```text
更强的 Qwen2.5-7B-Instruct 是否能在同样 Task B 框架下保持或扩大 skill_legacy_aligned 的优势。
```

优先跑两组：

| 顺序 | 版本 | 作用 |
|---:|---|---|
| 1 | `legacy_7b` | 7B 的 Task A 风格基线 |
| 2 | `skill_legacy_aligned_7b` | 7B 的 Task B 主线结果 |

可选第三组：

| 版本 | 作用 |
|---|---|
| `skill_hermes_7b` | 观察 7B 是否比 3B 更适应 Hermes-like tool call |

## 6. 7B 推荐运行命令

前提：

```text
项目路径: /root/AlphaApollo-TaskB
conda 环境: /root/miniconda3/envs/alphaapollo
7B 模型路径: /root/AlphaApollo-TaskB/models/Qwen2.5-7B-Instruct
输入数据: /root/AlphaApollo-TaskB/data/task-b-regression-100/custom_data/test.parquet
```

脚本默认会限制 Ray 使用的 CPU 数：

```text
RAY_NUM_CPUS=8
DATALOADER_NUM_WORKERS=0
```

原因是 `ray_init.num_cpus=null` 会让 Ray 使用所有 CPU，在部分云容器里可能卡在 worker 初始化阶段。

### 7B baseline

```bash
cd /root/AlphaApollo-TaskB
bash docs/task-b/artifacts/regression-100/run_math500_100_7b_regression.sh legacy_7b legacy
```

如果使用干净运行目录，例如 `/root/AlphaApollo-TaskB-7B`，用环境变量覆盖：

```bash
cd /root/AlphaApollo-TaskB-7B
PROJECT_ROOT=/root/AlphaApollo-TaskB-7B \
bash docs/task-b/artifacts/regression-100/run_math500_100_7b_regression.sh legacy_7b legacy
```

预期输出：

```text
data/task-b-regression-100/qwen25_7b_vllm_math500_100_legacy_7b.json
data/task-b-regression-100/qwen25_7b_vllm_math500_100_legacy_7b.parquet
```

### 7B Task B 主线

```bash
cd /root/AlphaApollo-TaskB
bash docs/task-b/artifacts/regression-100/run_math500_100_7b_regression.sh skill_legacy_aligned_7b skill_legacy
```

如果使用干净运行目录：

```bash
cd /root/AlphaApollo-TaskB-7B
PROJECT_ROOT=/root/AlphaApollo-TaskB-7B \
bash docs/task-b/artifacts/regression-100/run_math500_100_7b_regression.sh skill_legacy_aligned_7b skill_legacy
```

预期输出：

```text
data/task-b-regression-100/qwen25_7b_vllm_math500_100_skill_legacy_aligned_7b.json
data/task-b-regression-100/qwen25_7b_vllm_math500_100_skill_legacy_aligned_7b.parquet
```

### 如果 vLLM 仍失败

可以尝试 HF rollout fallback：

```bash
cd /root/AlphaApollo-TaskB
bash docs/task-b/artifacts/regression-100/run_math500_100_7b_hf_regression.sh legacy_7b_hf legacy
bash docs/task-b/artifacts/regression-100/run_math500_100_7b_hf_regression.sh skill_legacy_aligned_7b_hf skill_legacy
```

不过如果使用 H100 80GB，优先使用 vLLM 版本。

## 7. 7B 机器选择

之前在单张 RTX 4090 24GB 上已经验证：

```text
7B + vLLM: OOM
7B + HF rollout: OOM
```

所以 7B 推荐：

```text
最低建议: A100 40GB
更稳建议: H100 80GB / A100 80GB / L40S 48GB
```

你当前准备迁移到 H100 80GB，是合适的。

## 8. 新服务器迁移检查清单

在新服务器上依次检查：

```bash
cd /root
git clone https://github.com/xuanhh567/AlphaApollo-TaskB.git
cd AlphaApollo-TaskB
git rev-parse --short HEAD
```

应看到至少包含当前提交：

```text
2751d9e feat: align skill prompts and record regressions
```

然后检查数据：

```bash
ls -lh data/task-b-regression-100/custom_data/test.parquet
```

如果没有这个文件，需要从旧服务器或本地同步输入数据。

检查模型：

```bash
ls -lh models/Qwen2.5-7B-Instruct
```

如果没有模型，需要重新从 ModelScope 下载到这个路径。

检查环境：

```bash
/root/miniconda3/envs/alphaapollo/bin/python - <<'PY'
import torch
print(torch.__version__)
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0))
PY
```

最后先跑 1 个小检查：

```bash
nvidia-smi
bash docs/task-b/artifacts/regression-100/run_math500_100_7b_regression.sh legacy_7b legacy
```

如果第一组能完整生成 JSONL，再跑 `skill_legacy_aligned_7b`。

## 9. 7B 结果回来后要补的文档

跑完 7B 后，把结果同步回本地并补充：

```text
docs/task-b/artifacts/regression-100/qwen25_7b_vllm_math500_100_legacy_7b.json
docs/task-b/artifacts/regression-100/qwen25_7b_vllm_math500_100_skill_legacy_aligned_7b.json
docs/task-b/artifacts/regression-100/readable/qwen25_7b_vllm_math500_100_legacy_7b_rollouts.md
docs/task-b/artifacts/regression-100/readable/qwen25_7b_vllm_math500_100_skill_legacy_aligned_7b_rollouts.md
```

并更新：

```text
docs/task-b/regression-analysis.md
docs/task-b/experiments.md
docs/task-b/learning-log.md
```

7B 最终表格应该长这样：

| 模型 | 版本 | accuracy | 对比结论 |
|---|---|---:|---|
| Qwen2.5-3B-Instruct | legacy | 0.58 | 3B baseline |
| Qwen2.5-3B-Instruct | skill_legacy_aligned | 0.62 | 3B Task B 通过 |
| Qwen2.5-7B-Instruct | legacy_7b | 待填 | 7B baseline |
| Qwen2.5-7B-Instruct | skill_legacy_aligned_7b | 待填 | 7B Task B 对比 |
