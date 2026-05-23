# Task B 回归失败样本分析

> 这份文档记录 MATH-500 固定 100 题回归后，如何查看数据样本，以及这次旧 Function Call baseline 与新 Skill prompt 的差异来自哪里。

## 1. 文件在哪里

服务器上的输入数据：

```text
/root/AlphaApollo-TaskB/data/task-b-regression-100/custom_data/test.parquet
```

服务器上的三份输出：

```text
/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_legacy.json
/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill.json
/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill_v2.json
```

这里的 `.json` 实际是 JSONL：一行是一个样本，不是一个完整 JSON 数组。

## 2. 输入 parquet 里有什么

输入数据有 100 行，列名是：

```text
data_source
prompt
ability
reward_model
extra_info
metadata
env_kwargs
```

最重要的是：

```text
extra_info.question      原始题目
extra_info.ground_truth 标准答案
extra_info.index        在 MATH-500 原始 test split 中的 index
metadata.subject        题目类型
metadata.level          难度等级
```

通俗理解：`parquet` 就像一个更适合机器读取的 Excel 表。我们不直接用 Excel 打开，而是用 `pandas.read_parquet(...)` 读取。

## 3. 输出 JSONL 里看什么

每一行输出里最重要的是：

```text
history  完整对话历史，包含 prompt、模型输出、工具返回等
rewards  环境给这条样本的得分
```

判断对错时，我使用：

```text
只要 rewards 里任意一个值 > 0，就认为这题最终答对。
```

原因是 multi-turn 环境里，reward 可能按 step 存成嵌套 list，例如：

```text
[[0, 1.0]]
```

这表示前一步可能只是工具调用或中间过程，后一步得到最终正确答案。

## 4. 总体结果

| 版本 | 正确数 | 准确率 | answer 行数 | structured tool call 行数 | 完整有效 tool call 行数 |
|---|---:|---:|---:|---:|---:|
| legacy | 58 / 100 | 0.58 | 71 | 0 | 0 |
| skill | 38 / 100 | 0.38 | 84 | 12 | 2 |
| skill_v2 | 32 / 100 | 0.32 | 64 | 15 | 0 |
| skill_v3 | 28 / 100 | 0.28 | 63 | 14 | 0 |
| skill_v4 | 33 / 100 | 0.33 | 51 | 28 | 1 |

说明：

```text
legacy 使用的是旧 <python_code>...</python_code> 标签。
skill / skill_v2 使用的是新 <tool_call>{...}</tool_call> 协议。
```

最关键的数字是：

```text
skill 全 100 题里，只有 2 行产生了完整有效的 structured tool call。
```

这说明新 Skill 系统虽然能解析和执行 `<tool_call>`，但模型在当前 prompt 下没有稳定学会这个格式。

补充：`skill_v3` 增加了“调用工具后停止等待 `<tool_response>`”和更多 MATH 风格 `python_code` examples，但准确率降到 0.28，完整有效 structured tool call 仍为 0。这说明继续堆长说明不是可靠方向。

补充：`skill_v4` 将 prompt 改短，试图贴近旧版 tool-call 说明，准确率回升到 0.33。它让 `<tool_call>` 出现次数增加到 28 行，但完整有效 JSON 调用只有 1 个，所以仍没有达到 B6 要求。

## 4.1 Prompt 精简程度对比

为了确认几次实验到底是“加长说明”还是“压缩说明”，我用同一道题：

```text
Evaluate $(1+2i)6-3i$.
```

在不同 commit 下渲染无历史首轮 prompt，并统计字符数、行数和格式提示数量。

| 版本 | commit | prompt 字符数 | prompt 行数 | 相对 legacy 长度 | `<tool_call>` 出现次数 | examples 数 | 实验准确率 |
|---|---|---:|---:|---:|---:|---:|---:|
| legacy | `2fe16cb` | 818 | 9 | 1.00x | 0 | 0 | 0.58 |
| skill | `2fe16cb` | 1575 | 28 | 1.93x | 5 | 1 | 0.38 |
| skill_v2 | `57c6d7a` | 1814 | 29 | 2.22x | 5 | 1 | 0.32 |
| skill_v3 | `39f2a9e` | 2494 | 33 | 3.05x | 8 | 4 | 0.28 |
| skill_v4 | `0188438` | 1157 | 14 | 1.41x | 3 | 1 | 0.33 |

通俗解释：

```text
legacy 是最短的旧说明。
skill 初版为了说明 JSON tool_call，几乎变成 legacy 的 2 倍。
skill_v2 又加了“更偏向先用工具”的话，所以更长。
skill_v3 加了调用后停止、等待 tool_response、更多 examples，是最重的版本。
skill_v4 做减法，只保留最小 structured 格式和一个 example。
```

从结果看，prompt 不是越详细越好。`skill_v3` 最长，但准确率最低；`skill_v4` 明显压缩后准确率回升到 0.33，但仍然没有达到 legacy 的 0.58。

这说明当前主要问题不是“说明不够多”，而是：

```text
模型没有稳定学会新格式：
<tool_call>{"name":"python_code","arguments":{"code":"..."}}</tool_call>
```

后续如果继续改 prompt，更合理的方向不是继续堆说明，而是让格式更贴近模型已经会的旧习惯，或者提供少量高质量 few-shot 轨迹。

## 4.2 模型输出习惯溯源

为了判断下一版 prompt 应该怎么写，我把 `skill` 到 `skill_v4` 的 JSONL 输出重新分类，重点看模型到底喜欢输出什么格式。

| 版本 | 无 `<tool_call>` | 有 `<answer>` | 无动作 | 有旧 `<python_code>` | `<tool_call>` 未闭合 | 非 JSON / 文本式 tool call | invalid JSON | 有效 JSON tool call |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| skill | 88 | 84 | 8 | 0 | 7 | 2 | 1 | 2 |
| skill_v2 | 85 | 64 | 18 | 4 | 14 | 1 | 0 | 0 |
| skill_v3 | 86 | 63 | 22 | 3 | 11 | 1 | 2 | 0 |
| skill_v4 | 72 | 51 | 17 | 8 | 5 | 10 | 12 | 1 |

几个典型坏格式：

```text
<tool_call> name: python_code
arguments: {"code": "..."}
```

```text
<tool_call><tool_call>{"name":"python_code","arguments":{"code":"..."}}</tool_call>
```

```text
<tool_call>python_code
{"name":"python_code","arguments":{"code":"..."}}
```

```text
<tool_call>...</tool_call>
```

```text
<tool_call>{"name":"python_code","arguments":{"code":"..."
```

通俗解释：

```text
模型不是完全不知道“可以用工具”。
它的问题是：经常把 tool call 写成自己熟悉的自然语言 / YAML / 半截 JSON / 双重标签。
```

这说明下一版 prompt 应该不是继续解释“什么是 tool call”，而是更明确地适配模型已经暴露出的坏习惯：

```text
1. 不要写 name: python_code / arguments: ... 这种 YAML 风格。
2. 不要写 <tool_call>python_code。
3. 不要写 <tool_call>...</tool_call> 占位符。
4. 不要套两个 <tool_call>。
5. 如果使用工具，只输出一行完整 JSON。
```

但是这些规则不能写成长篇说明，否则又会回到 `skill_v3` 的问题。更合理的是给一个短的 few-shot 对照：

```text
Bad:  <tool_call>python_code {"code":"print(1+1)"}</tool_call>
Good: <tool_call>{"name":"python_code","arguments":{"code":"print(1+1)"}}</tool_call>
```

换句话说，下一版可以叫 `skill_v5_adapter_prompt`：不是增加更多概念，而是针对模型真实犯过的格式错误做最小纠偏。

## 5. legacy vs skill 对比

| 类型 | 数量 |
|---|---:|
| legacy 对，skill 也对 | 28 |
| legacy 对，skill 错 | 30 |
| legacy 错，skill 对 | 10 |
| legacy 错，skill 也错 | 32 |

最值得分析的是：

```text
legacy 对，skill 错：30 题
```

因为这些题说明：同一个模型、同一个数据子集，旧 prompt 能做对，但新 prompt 后变错。

## 6. 30 个退步样本的错误类型

在 `legacy 对，skill 错` 的 30 题中，`skill` 的错误类型是：

| 错误类型 | 数量 | 通俗解释 |
|---|---:|---|
| direct_answer_wrong | 26 | 模型没有真正调用工具，直接给了最终答案，但答案错了 |
| incomplete_tool_call_tag | 2 | 模型想调用 `<tool_call>`，但标签没闭合或格式不完整 |
| no_answer_no_tool_call | 2 | 模型既没有最终答案，也没有可执行工具调用 |

这个结果很重要：

```text
主要退步不是 dispatcher 执行失败，而是模型在新 prompt 下更倾向于直接答题，且直接答错。
```

## 7. 退步样本的题型分布

`legacy 对，skill 错` 的 30 题中：

| subject | 数量 |
|---|---:|
| Algebra | 13 |
| Geometry | 4 |
| Counting & Probability | 3 |
| Intermediate Algebra | 3 |
| Prealgebra | 3 |
| Precalculus | 3 |
| Number Theory | 1 |

按难度：

| level | 数量 |
|---|---:|
| 1 | 2 |
| 2 | 3 |
| 3 | 10 |
| 4 | 9 |
| 5 | 6 |

可以看到，退步主要集中在 level 3-5 的题。这类题更容易从工具校验中受益；如果新 prompt 没有稳定触发工具，准确率就会下降。

## 8. 典型样本

### 样本 1：模型知道答案，但工具调用格式坏了

样本：

```text
row: 2
MATH-500 原始 index: 20
subject: Algebra
level: 3
题目: Evaluate $(1+2i)6-3i$.
标准答案: 6+9i
```

legacy 输出了最终答案：

```text
<answer>\(\boxed{6 + 9i}\)</answer>
```

skill 输出中其实已经推到了正确结果：

```text
6 + 12i - 3i = 6 + 9i
```

但最后写成了不完整工具调用：

```text
<tool_call> name: python_code arguments: {"code": "..."}
```

问题有两个：

```text
1. 没有闭合 </tool_call>
2. 标签内部不是一个 JSON object
```

所以环境没法执行这个工具调用，最后 reward 是 0。

### 样本 2：没有用工具，组合计数算错

样本：

```text
row: 4
MATH-500 原始 index: 32
subject: Counting & Probability
level: 4
题目: 8 人圆桌，Pierre、Rosa、Thomas 三人必须坐一起，问多少种坐法
标准答案: 720
```

skill 错误答案：

```text
\boxed{240}
```

原因是模型把三个人内部排列算成了 `2!`，但正确应该是 `3!`。

正确思路：

```text
三个人看成一个整体 block。
block + 其他 5 人 = 6 个对象围成圆桌。
圆排列: (6-1)! = 5!
block 内部排列: 3!
总数: 5! * 3! = 720
```

这类错误说明：新 prompt 下模型直接答题，缺少工具检查或自检。

### 样本 3：概率题重复计数

样本：

```text
row: 15
MATH-500 原始 index: 75
subject: Counting & Probability
level: 4
题目: 两个骰子乘积是 5 的倍数的概率
标准答案: 11/36
```

skill 错误答案：

```text
\boxed{\frac{1}{3}}
```

错误原因：

```text
模型算了 6 + 6 = 12 个情况，
但 (5,5) 被重复算了一次。
```

正确做法：

```text
至少一个骰子是 5。
总情况: 36
反面: 两个骰子都不是 5，有 5 * 5 = 25 种
正面: 36 - 25 = 11 种
概率: 11/36
```

这也是直接推理错误，不是 tool runtime 错。

## 9. 当前结论

这次 B6 回归失败的主因可以概括为：

```text
新 Skill runtime 跑通了；
但新 structured prompt 没有让模型稳定输出可执行 tool call；
模型更多时候直接答题，因此在需要计算/校验的题上准确率下降。
```

所以不要把下一步重点放在 dispatcher 或 registry 重写上。更应该做：

```text
1. prompt 行为对齐：让新 prompt 更像旧 prompt 那样鼓励工具调用。
2. 格式约束：减少不完整 `<tool_call>` 和非 JSON 内容。
3. few-shot 示例：加入“调用工具 -> 看到 tool_response -> 再给 answer”的完整二轮示例。
4. 小样本快速验证：先用这 30 个退步样本做 targeted regression，再跑完整 100 题。
```

## 10. 查看某个样本的命令

在服务器运行：

```bash
cd /root/AlphaApollo-TaskB
PY=/root/miniconda3/envs/alphaapollo/bin/python
```

查看输入题目：

```bash
$PY - <<'PY'
import pandas as pd

df = pd.read_parquet("/root/AlphaApollo-TaskB/data/task-b-regression-100/custom_data/test.parquet")
i = 2
row = df.iloc[i]

print("row:", i)
print("question:", row["extra_info"]["question"])
print("ground_truth:", row["extra_info"]["ground_truth"])
print("metadata:", row["metadata"])
PY
```

对比 legacy 和 skill 的模型输出：

```bash
$PY - <<'PY'
import json
from pathlib import Path

root = Path("/root/AlphaApollo-TaskB/data/task-b-regression-100")
i = 2

def load(name):
    path = root / f"qwen25_3b_vllm_math500_100_{name}.json"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

def show_assistant(row):
    hist = row.get("history") or []
    text = str(hist[0][0]) if hist and isinstance(hist[0], list) and hist[0] else str(hist)
    parts = text.split("assistant\n")[1:]
    turns = [p.split("\nuser\n")[0].strip() for p in parts]
    return "\n\n--- assistant turn ---\n\n".join(turns)

for name in ["legacy", "skill"]:
    row = load(name)[i]
    print("\n===", name, "===")
    print("rewards:", row.get("rewards"))
    print(show_assistant(row))
PY
```

看懂这两个输出，你就能自己判断：

```text
旧版为什么对？
新版为什么错？
错在数学推理、答案格式，还是 tool_call 格式？
```
