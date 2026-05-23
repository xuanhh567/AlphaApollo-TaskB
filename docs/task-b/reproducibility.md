# Task B 复现与实验管理

这份文档回答两个问题：

```text
1. 现在这些测试以后能不能复现？
2. 后续继续做实验时，应该怎么管理，才不会越跑越乱？
```

## 1. 当前能复现到什么程度

当前 Task B 的 3B 回归实验是可以复现的，因为关键条件已经固定：

| 项目 | 当前记录 |
|---|---|
| 代码仓库 | `https://github.com/xuanhh567/AlphaApollo-TaskB.git` |
| 主要服务器 | 美国 RTX 4090 实验机 |
| 远端项目路径 | `/root/AlphaApollo-TaskB` |
| Python 环境 | `/root/miniconda3/envs/alphaapollo/bin/python` |
| 3B 模型路径 | `/root/AlphaApollo-TaskB/models/Qwen2.5-3B-Instruct` |
| 数据子集 | MATH-500 固定 100 题，`random.Random(0)` 抽样 |
| 输入数据 | `/root/AlphaApollo-TaskB/data/task-b-regression-100/custom_data/test.parquet` |
| 结果 artifacts | `docs/task-b/artifacts/regression-100/` |

通俗理解：我们已经把“考卷是哪 100 题、用哪个模型、用哪个代码版本、输出结果是什么”记录下来了。

## 2. 还不能完全复现的部分

有些东西不应该直接提交到 GitHub，所以不是“只 clone 仓库就能跑”：

| 不提交的内容 | 原因 |
|---|---|
| 模型文件 `models/` | 文件太大 |
| parquet 输入输出 | 原仓库 `.gitignore` 忽略 `data/` 和 `*.parquet` |
| conda 环境目录 | 文件太多、机器相关 |
| 服务器密码 | 敏感信息，绝对不要进仓库 |
| `/tmp/*.log` 原始日志 | 可以很长，适合保存在服务器，只把关键结论写进文档 |

所以更准确地说：

```text
实验结论可复查，实验脚本可复用；
但完整重跑需要同类服务器、同类 conda 环境、同样的模型和数据文件。
```

## 3. 每次实验必须记录什么

以后每跑一次实验，都按这个清单记录：

| 字段 | 例子 | 为什么重要 |
|---|---|---|
| experiment_id | `qwen25_3b_vllm_math500_100_skill_v4` | 唯一名字，避免结果混在一起 |
| git commit | `0188438` | 知道当时跑的是哪版代码 |
| model_path | `models/Qwen2.5-3B-Instruct` | 模型不同，结果不能直接比较 |
| backend | `vllm` / `hf` | 后端不同，采样和显存行为可能不同 |
| data_path | `data/task-b-regression-100/custom_data/test.parquet` | 数据不同，结果不能比较 |
| sample_indices | 固定 100 个 index | 确认每次考的是同一张卷子 |
| prompt_format | `legacy` / `skill` | Task A 和 Task B 的核心区别 |
| decoding | `temperature=0, top_k=-1, top_p=1` | 采样参数不同，结果会变 |
| output_json | 输出 JSONL 路径 | 后续复查 trajectory |
| result | `avg@1/pass@1 = 0.33` | 最终指标 |
| conclusion | `B6 未通过` | 一句话结论 |

## 4. 文件命名规则

以后建议统一使用这种命名：

```text
{model_family}_{model_size}_{backend}_{dataset}_{n}_{format}_{variant}.json
```

例子：

```text
qwen25_3b_vllm_math500_100_legacy.json
qwen25_3b_vllm_math500_100_skill_v4.json
qwen25_7b_vllm_math500_5_skill_sanity.json
```

通俗理解：文件名本身就应该说明“谁跑的、跑了多少题、跑的是哪个版本”。

## 5. 推荐目录结构

服务器上：

```text
/root/AlphaApollo-TaskB/
  models/
    Qwen2.5-3B-Instruct/
    Qwen2.5-7B-Instruct/
  data/
    task-b-regression-100/
      custom_data/test.parquet
      qwen25_3b_vllm_math500_100_legacy.json
      qwen25_3b_vllm_math500_100_skill_v4.json
  /tmp/
    run_math500_100_skill_v4.log
```

GitHub 仓库里：

```text
docs/task-b/
  experiments.md
  regression-analysis.md
  server-environment.md
  reproducibility.md
  artifacts/regression-100/
    README.md
    run_*.sh
    *.json
```

## 6. 推荐工作流

### 本机负责

```text
1. 写代码
2. 写中文文档
3. 跑单元测试
4. git commit
5. git push
```

### 服务器负责

```text
1. git pull --ff-only origin main
2. 检查模型和数据
3. 跑真实模型实验
4. 生成 JSONL / parquet
5. 把关键 JSONL 和脚本同步回本机
```

### 本机收尾

```text
1. 把服务器结果放入 docs/task-b/artifacts/
2. 更新 experiments.md
3. 更新 regression-analysis.md
4. 更新 learning-log.md
5. git commit + git push
```

## 7. 复现 3B 固定 100 题回归

在服务器上：

```bash
cd /root/AlphaApollo-TaskB
git pull --ff-only origin main
```

运行 legacy baseline：

```bash
bash docs/task-b/artifacts/regression-100/run_math500_100_regression.sh legacy
```

运行最小 skill prompt v4：

```bash
bash docs/task-b/artifacts/regression-100/run_math500_100_skill_v4.sh skill
```

注意：脚本里使用 vLLM，所以 `top_k` 必须是：

```text
rollout.top_k=-1
```

## 8. 当前 3B 结果

| 版本 | 正确率 | 结论 |
|---|---:|---|
| legacy | 0.58 | Task A baseline |
| skill | 0.38 | 未通过 B6 |
| skill_v2 | 0.32 | 未通过 B6 |
| skill_v3 | 0.28 | 未通过 B6 |
| skill_v4 | 0.33 | 未通过 B6 |

Task B 的通过条件不是超过论文结果，而是：

```text
同一个模型、同一批题、同一套参数下，
Skill 版相对 Task A baseline 不得明显回退。
```

当前最好的 Skill 版仍然低于 baseline，所以 B6 还没有通过。

## 9. 7B 测试记录

已经在美国 RTX 4090 服务器下载：

```text
/root/AlphaApollo-TaskB/models/Qwen2.5-7B-Instruct
```

下载来源：

```text
ModelScope: Qwen/Qwen2.5-7B-Instruct
```

尝试结果：

| 后端 | 数据 | 结果 | 原因 |
|---|---|---|---|
| vLLM | 5 题 sanity | OOM | 7B + vLLM 推理副本在单张 4090 24GB 上显存不够 |
| HF rollout | 5 题 sanity | OOM | FSDP 单卡 flatten 7B 参数时需要额外显存 |

当前结论：

```text
7B 可能改善格式跟随能力，但这台单张 4090 服务器暂时跑不稳。
如果要认真测 7B，建议换 48GB/80GB 显存，或者使用多卡配置。
```

## 10. 以后怎么判断一个实验是否可信

一个实验可信，至少要满足：

```text
1. 有固定 git commit。
2. 有固定数据子集。
3. 有固定模型路径和模型来源。
4. 有保存的运行脚本。
5. 有保存的 JSONL 输出。
6. 有文档记录最终指标和结论。
7. 可以解释为什么这个实验能和另一个实验比较。
```

不能这样比较：

```text
7B skill vs 3B legacy
```

应该这样比较：

```text
3B legacy vs 3B skill
7B legacy vs 7B skill
```

核心原则：只改变一个变量。比如比较 Skill 是否退步时，模型、数据、采样参数都应该保持一致。
