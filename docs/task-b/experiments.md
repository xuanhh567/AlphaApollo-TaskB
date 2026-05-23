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
| Task A baseline | MATH-500 固定 100 题子集 | Completed | `avg@1/pass@1 = 0.58` |
| Task B skill version | MATH-500 固定 100 题子集 | Completed | `avg@1/pass@1 = 0.38` |
| Task B skill prompt v2 | MATH-500 固定 100 题子集 | Completed | `avg@1/pass@1 = 0.32` |
| Task B skill prompt v3 | MATH-500 固定 100 题子集 | Completed | `avg@1/pass@1 = 0.28` |
| Task B skill prompt v4 | MATH-500 固定 100 题子集 | Completed | `avg@1/pass@1 = 0.33` |
| Task B skill prompt v5 | MATH-500 固定 100 题子集 | Completed | `avg@1/pass@1 = 0.11` |
| Task B skill_legacy adapter | MATH-500 固定 100 题子集 | Completed | `avg@1/pass@1 = 0.48` |
| Task B skill_legacy aligned | MATH-500 固定 100 题子集 | Completed | `avg@1/pass@1 = 0.62` |
| Task B skill_hermes | MATH-500 固定 100 题子集 | Completed | `avg@1/pass@1 = 0.44` |
| Task B skill_hermes_boxed | MATH-500 固定 100 题子集 | Completed | `avg@1/pass@1 = 0.44` |
| 指标差值 | MATH-500 固定 100 题子集 | Passed | best skill 比 baseline 高 4 个百分点 |

结论：

```text
Task B 的代码链路已经能跑通，当前 `skill_legacy_aligned` 版本的回归指标已经通过 B6。
B6 要求相对 Task A baseline 误差 <= 3%，当前 best skill 是 0.62，对比 baseline 0.58，高 0.04。
```

通俗解释：新 Skill 系统会执行，但模型看到新 prompt 后，行为还没有和旧 `<python_code>` prompt 对齐。
当前主要问题不是 registry / dispatcher 崩溃，而是模型更少稳定使用工具，且最终答案正确率下降。

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

## 3.3 MATH-500 固定 100 题回归：Task A baseline vs Task B skill

### 目的

MiniProject 要求 B6 做回归：

```text
在 MATH-500 上回归（可固定种子抽样 >=100 题），
指标相对 Task A 基线不得回退（误差 <=3%）。
```

这里先跑固定 100 题子集，目的是回答一个核心问题：

```text
只把模型侧工具协议从旧标签换成 Skill 结构化调用后，准确率有没有明显下降？
```

### 对比方式

本次对比尽量只改一个变量：模型看到的工具调用格式。

```text
相同项:
- 模型: Qwen2.5-3B-Instruct
- 后端: vLLM
- 数据: MATH-500 固定 100 题子集
- n_samples: 1
- do_sample: false
- temperature: 0.0
- top_k: -1
- max_steps: 2
- enable_python_code: true
- enable_local_rag: false

不同项:
- legacy: 使用旧 `<python_code>...</python_code>` prompt
- skill: 使用新的 `<tool_call>{"name": ..., "arguments": ...}</tool_call>` prompt
- skill_v2: 调整后的 structured skill prompt，更强调先用工具再给最终答案
```

这不是 Task A 完整论文复现，只是 Task B 的迁移回归。它的价值在于比较同一个代码版本、同一个模型、同一个数据子集下，新旧工具协议是否保持接近。

因此这里的 `baseline` 更准确地说是“旧 Function Call 协议基线”，不是 MiniProject Task A 的完整模型能力复现。

### 数据子集

生成方式：

```text
从 MATH-500 的 500 题中，用 random.Random(0) 固定抽样 100 题，并排序。
```

服务器数据路径：

```text
/root/AlphaApollo-TaskB/data/task-b-regression-100/custom_data/test.parquet
```

抽样 index：

```text
0,7,20,31,32,37,41,46,47,48,50,51,55,71,72,75,97,104,111,113,
122,124,128,132,133,144,149,154,155,158,161,163,166,169,170,181,
183,197,204,207,215,222,226,229,241,244,248,250,252,258,260,261,
266,272,278,280,282,286,290,298,308,312,313,316,320,327,342,350,
360,361,363,368,373,386,388,401,409,411,412,414,422,423,424,430,
432,435,443,447,455,456,461,464,465,467,468,470,478,485,488,489
```

### 关键命令参数

服务器脚本：

```text
/tmp/run_math500_100_regression.sh
/tmp/run_math500_100_skill_v2.sh
```

核心覆盖参数：

```bash
model.path=/root/AlphaApollo-TaskB/models/Qwen2.5-3B-Instruct
data.path=/root/AlphaApollo-TaskB/data/task-b-regression-100/custom_data/test.parquet
data.n_samples=1
data.batch_size=1
rollout.name=vllm
rollout.do_sample=false
rollout.temperature=0.0
rollout.top_k=-1
rollout.top_p=1.0
rollout.prompt_length=2048
rollout.response_length=1024
env.env_name=informal_math_training
+env.skills=[python_code]
+env.tool_prompt_format=legacy  # 或 skill
env.max_steps=2
env.history_length=2
env.informal_math.enable_python_code=true
env.informal_math.enable_local_rag=false
```

注意：`env.skills` 和 `env.tool_prompt_format` 是新字段，所以 Hydra 命令行里要写成 `+env.skills=...` 和 `+env.tool_prompt_format=...`。

### 结果

| 版本 | prompt 格式 | commit | avg@1 | pass@1 | 重新统计 accuracy | answer 数 | tool call 数 | 结论 |
|---|---|---|---:|---:|---:|---:|---:|---|
| baseline | 旧 `<python_code>` 标签 | `2fe16cb` | 0.58 | 0.58 | 0.58 | 71 | 48 legacy tags | 基线 |
| skill | 新 `<tool_call>` JSON | `2fe16cb` | 0.38 | 0.38 | 0.38 | 84 | 12 structured calls | 未通过 |
| skill_v2 | 调整后的 `<tool_call>` prompt | `57c6d7a` | 0.32 | 0.32 | 0.32 | 64 | 15 structured calls | 未通过 |
| skill_v3 | 对齐工具使用说明后的 `<tool_call>` prompt | `39f2a9e` | 0.28 | 0.28 | 0.28 | 63 | 14 structured calls | 未通过 |
| skill_v4 | 最小化说明后的 `<tool_call>` prompt | `0188438` | 0.33 | 0.33 | 0.33 | 51 | 28 structured calls | 未通过 |
| skill_v5 | Bad/Good 适配后的 `<tool_call>` prompt | `7e50310` | 0.11 | 0.11 | 0.11 | 19 | 53 structured calls | 未通过 |
| skill_legacy | SKILL.md 驱动的旧 `<python_code>` 标签 | `9433df1` | 0.48 | 0.48 | 0.48 | 47 | 59 legacy tags | 未通过，但明显改善 |
| skill_legacy_aligned | 去掉 python_code 内联例子的 SKILL.md legacy prompt | `9433df1 + local patch` | 0.62 | 0.62 | 0.62 | 89 | 14 legacy tags | 通过 |
| skill_hermes | SKILL.md 生成 Hermes-like function schema | `9433df1 + local patch` | 0.44 | 0.44 | 0.44 | 74 | 46 plural calls + 1 structured call | 未通过，略好于 structured |
| skill_hermes_boxed | Hermes-like prompt + 强调 `<answer>\boxed{...}</answer>` | `9433df1 + local patch` | 0.44 | 0.44 | 0.44 | 69 | 27 plural calls + 1 structured call | 未通过，分数持平 |

输出文件：

```text
/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_legacy.json
/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_legacy.parquet

/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill.json
/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill.parquet

/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill_v2.json
/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill_v2.parquet

/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill_v3.json
/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill_v3.parquet

/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill_v4.json
/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill_v4.parquet

/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill_v5.json
/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill_v5.parquet

/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill_legacy.json
/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill_legacy.parquet

/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill_legacy_aligned.json
/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill_legacy_aligned.parquet

/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill_hermes.json
/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill_hermes.parquet

/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill_hermes_boxed.json
/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill_hermes_boxed.parquet
```

日志文件：

```text
/tmp/run_math500_100_legacy.log
/tmp/run_math500_100_skill.log
/tmp/run_math500_100_skill_v2.log
/tmp/run_math500_100_skill_v3.log
/tmp/run_math500_100_skill_v4.log
/tmp/run_math500_100_skill_v5.log
/tmp/run_math500_100_skill_legacy.log
/tmp/run_math500_100_skill_legacy_aligned.log
/tmp/run_math500_100_skill_hermes.log
/tmp/run_math500_100_skill_hermes_boxed.log
```

### 当前判断

当前 `skill_legacy_aligned` 已经通过 B6 的固定 100 题回归。

```text
允许误差: <= 3%
实际差距: 0.62 - 0.58 = +0.04
```

更细一点看，旧 prompt 里模型有 48 次使用旧工具标签，而新 prompt 里 structured tool call 只有 12 次。说明新系统虽然能解析和执行 `<tool_call>`，但 prompt 没有让模型像以前那样稳定地使用工具。`skill_v2` 试图更强调工具优先，但准确率继续下降，因此不能把它当作修复。

`skill_v3` 进一步补充了“调用工具后停止等待 `<tool_response>`”以及更多 MATH 风格的 `python_code` examples，但结果下降到 0.28。这说明简单增加格式说明和 examples 还不够，甚至可能让 3B 模型的 prompt 负担更重。

`skill_v4` 反过来做减法，把 prompt 改成更接近旧版的最小说明，准确率回升到 0.33，但仍明显低于 baseline 0.58。它让模型更常输出 `<tool_call>`，但 28 行 structured tool call 中只有 1 个完整有效 JSON 调用，说明问题仍主要在模型格式跟随能力，而不是工具执行链路。

`skill_v5` 增加了很短的 Bad/Good 格式纠偏，`<tool_call>` 出现次数上升到 53 行，有效 JSON tool call 也从 1 个增加到 4 个，但准确率降到 0.11。主要原因是模型开始照抄 prompt 里的 “Tool-call format adapter” 文本，很多回答既没有最终 `<answer>`，也没有可执行工具调用。

`skill_legacy` 改用 SKILL.md 驱动的旧标签 prompt：模型仍看到 `<python_code>...</python_code>`，但环境内部通过 `SkillSpec.legacy_calls` 转成统一 `ToolCall`，再走 registry / dispatcher。它的准确率回升到 0.48，比最初 skill 版高 10 个百分点，比 `skill_v5` 高 37 个百分点，但仍低于 Task A baseline 0.58，B6 还没有通过。

`skill_legacy_aligned` 在 `skill_legacy` 的基础上做最小 prompt 对齐：去掉 `python_code` legacy prompt 里的内联 `Example: <python_code>print(1 + 1)</python_code>`，并让 SKILL.md 自动生成的工具顺序保持 `python_code -> local_rag`。这版准确率达到 0.62，高于旧 baseline 0.58，因此固定 100 题回归通过。行为上也更接近原始 legacy：answer 数从 73 回升到 89，assistant 中 `<python_code>` 从 21 降到 14。

`skill_hermes` 参考 vLLM/Qwen Hermes-style tool use：prompt 由 SKILL.md 生成 OpenAI/Hermes-like function schema，parser 接受 `<tool_calls>[...]</tool_calls>` 和 OpenAI-like `function.arguments` 字符串。它的准确率是 0.44，比最初 structured `skill=0.38` 高 6 个百分点，但低于 `skill_legacy=0.48`。这说明“靠近 Qwen/Hermes 格式”有帮助，但在当前 AlphaApollo rollout 环境里，小模型仍更吃旧 `<python_code>` 标签。

`skill_hermes_boxed` 在 `skill_hermes` 基础上只强化最终答案格式：要求 `<answer>` 里面必须包含 `\boxed{...}`，例如 `<answer>\boxed{...}</answer>`。它让 answer 中带 `\boxed{...}` 的比例明显上升，也让完整有效 tool call 从 3 个增加到 6 个；但最终正确率仍是 0.44。通俗地说，这个改动修了一部分“交卷格式”，但没有解决整体答题正确率和工具使用稳定性。

### 下一步建议

下一步可以把 `skill_legacy_aligned` 作为 Task B 主线结果，同时保留 Hermes / structured 作为探索分支。为了让结论更稳，可以继续做两件事：

```text
1. 记录为什么 skill_legacy_aligned 比 skill_legacy 提升：answer 数增加，最后一步多余 python_code 减少。
2. 视服务器时间决定是否再跑全量 MATH-500，或者保持 MiniProject 要求的固定种子 100 题证据。
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

## 8. 7B 回归尝试

### 目标

在 3B 固定 100 题回归通过后，尝试用 `Qwen2.5-7B-Instruct` 跑同样的对比：

```text
Task A 风格: legacy
Task B 风格: skill_legacy_aligned
```

### 当前机器

```text
GPU: NVIDIA GeForce RTX 4090
显存: 24564 MiB
模型: /root/AlphaApollo-TaskB/models/Qwen2.5-7B-Instruct
```

### 已准备脚本

```text
docs/task-b/artifacts/regression-100/run_math500_100_7b_regression.sh
docs/task-b/artifacts/regression-100/run_math500_100_7b_hf_regression.sh
```

### 运行结果

vLLM backend：

```text
输出后缀: legacy_7b
服务器日志: /tmp/run_math500_100_7b_legacy.log
结果: CUDA OOM
原因: vLLM 加载 7B 模型时显存已接近满载，只剩约 115 MiB。
```

HF rollout fallback：

```text
输出后缀: legacy_7b_hf
服务器日志: /tmp/run_math500_100_7b_hf_legacy.log
结果: CUDA OOM
原因: FSDP 初始化时还需要约 14.19 GiB，但当时只剩约 8.58 GiB。
```

### 结论

这次不是代码逻辑或模型文件问题，而是计算平台不够。单张 24GB 4090 在当前 AlphaApollo/verl 评估链路下无法承载 7B 回归。

后续如果要正式跑 7B 对比，建议使用：

```text
最低建议: 1 x A100 40GB
更稳建议: 1 x A6000 48GB / L40S 48GB
```
