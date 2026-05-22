# Mini-Project

## 借鉴 **OpenClaw** 工具体系思想，将 **AlphaApollo** 的 **Tool Call** 从 **Function Call** 升级为 **Skill**

_TMLR Group — Research Intern Mini-Project_

| 项目 | 内容 |
|---|---|
| **Framework** | AlphaApollo (https://github.com/tmlr-group/AlphaApollo) |
| 参考 | OpenClaw 的 skills 插件化 / terminal-agent 工具使用思想 |
| **Model** | Qwen2.5-7B-Instruct 或同规模模型 |
| **Benchmark** | MATH-500 (HuggingFaceH4/MATH-500) |
| 建议完成时间 | 7 天 |
| 难度 | ★★★★☆（中高） |

Trustworthy Machine Learning and Reasoning (TMLR) Group  
Hong Kong Baptist University

_Confidential — For Intern Screening Only_

## 重要提示

1. 关于 Vibe Coding：可以使用 AI 辅助编程，但我们会在面试中对核心实现功能进行提问，答不上来会严重扣分。请确保你理解 environment side 的 tool 解析 / 路由 / 执行流程，以及 `rollout_loop.py` 的 prompt 构建逻辑。

2. 基于当前主干开发：AlphaApollo 当前主干通过文本标签调用工具，模型输出 `<python_code>...</python_code>`，环境端字符串解析抓标签、硬编码 if 分支路由、执行后包进 `<tool_response>`。仅有 `<python_code>` 与 `<local_rag>` 两个工具，由 `enable_python_code` / `enable_local_rag` 开关控制。本题所有改动须落在当前主干之上。

3. 核心理念：把工具的调用方式从“脆弱的文本标签解析”升级为“结构化 function-call”，并借鉴 OpenClaw 的 skill 机制，把每个工具组织成目录化、自描述、可动态发现的 **SKILL.md skill**。注意：OpenClaw 的 skill 不是一个 Python 函数，而是一个目录，核心是带 YAML frontmatter 的 `SKILL.md`（声明能力元信息与使用说明）+ 可选脚本 / 资源，框架启动时扫描目录、解析 frontmatter 完成注册。本题要在 AlphaApollo 中复刻这一形态。

## 1 背景介绍

### 1.1 AlphaApollo 当前的 Tool Call 方式

AlphaApollo 的 environment side 工作流程为：

1. hosting tools，工具实现为可调用函数；
2. parsing outputs，用字符串 / 正则解析模型输出中的 tool-specific tags；
3. executing tools，把解析出的调用硬编码路由到对应工具；
4. returning feedback，结果包进 `<tool_response>` 返回模型。

这套“标签 + 正则 + if 分支”的方式有两个痛点：

- 解析脆弱：依赖模型精确吐出标签格式；参数靠在标签体里塞自由文本，缺少结构与类型约束，容易解析失败。

- 扩展性差：新增工具要同时改 parser、router 的 if 分支、手写 prompt 说明、加 `enable_xxx` 开关，散点修改、核心代码硬编码。

### 1.2 参考：OpenClaw 的 Skills 插件化

OpenClaw 是一个开源 terminal-agent / 个人 AI 助手框架，其工具体系中每个工具是独立、自描述的 skill，带元信息（功能、输入输出 schema、使用示例），可动态注册、发现和加载，而非硬编码在框架里。新增能力只需新增一个 skill 插件，框架核心不变；prompt 中的工具说明可由元信息自动生成。

本题不要求复制 OpenClaw 的架构，而是借鉴这一思想，重构 AlphaApollo 的 tool call 层。

### 1.3 MATH-500 Benchmark

MATH-500 是从 MATH 数据集中抽取的 500 道竞赛数学题，覆盖代数、数论、几何、概率等，难度分布平滑，ground truth 公开可用，是 AlphaApollo 主干已支持的数据源之一。相比 AIME（仅 30 题），MATH-500 在统计上更稳定，更适合做“指标不回退”的回归验证。

提示：MATH-500 全量 500 题跑 tool-integrated rollout 耗时较长。回归对比时可在固定随机种子下抽样 ≥100 题进行；最终指标全量跑一次报告即可。

## 2 任务描述

本 Mini-Project 分为三个递进式任务 + 一个附加题：「跑通 → 升级为 Skill → 文档」。基础分共 100 分，附加题最多 +20 分。

### Task A: 环境搭建与跑通（25 分）

目标：理解 AlphaApollo 的代码结构与当前 tool call 流程，在纯文本模型上跑通 evaluation。

- Clone AlphaApollo，完成环境配置，启动 inference backend、computation tool、retrieval tool。

- 选择已支持的模型（如 Qwen2.5-7B-Instruct），在 MATH-500 上运行 tool-integrated agentic reasoning evaluation。

- 验证结果与论文 / 第三方可查指标对齐（误差 ≤3%）。

### Task B: 从 Function Call 到 Skill（50 分）

目标：借鉴 OpenClaw 的 skill 机制，把 AlphaApollo 的工具从“硬编码标签 + if 分支”重构为目录化、自描述、可动态发现的 **SKILL.md skill**，并把模型侧的调用方式升级为结构化 function-call。

说明：OpenClaw 的 skill 不是一个 Python 函数，而是一个目录，核心是带 YAML frontmatter 的 `SKILL.md`（声明能力的元信息与使用说明）+ 可选的脚本 / 资源；框架在启动时扫描目录、解析 frontmatter 完成注册。本题要在 AlphaApollo 中复刻这一形态。

#### B1. SKILL.md 规范设计与解析（14 分）

- 设计一套 skill 目录规范：每个 skill 是一个文件夹，含一个 `SKILL.md`，其 YAML frontmatter 至少声明 name、description、参数 schema（名称 / 类型 / 是否必需）、调用入口（脚本路径或函数名）、使用 examples。

- 实现 frontmatter 解析器：YAML 解析 + 字段校验，缺字段 / 格式错时返回结构化错误而非崩溃。

- 在仓库中提供一份 `SKILL.md` 编写说明，使他人能照着新增 skill。

#### B2. Skill 加载器与注册表（14 分）

- 启动时扫描 skill 目录、解析每个 `SKILL.md`、注册进 registry；框架核心不得硬编码任何具体工具名。

- 启用配置由声明驱动（如 `--env.skills=[python_code, local_rag]`），取代写死的 `enable_xxx` 开关。

#### B3. 结构化调用协议与通用 Dispatcher（16 分）

- 结构化调用格式 + 解析器：如模型输出 JSON `{"name": ..., "arguments": {...}}`，可包在一个固定标签内，取代在标签体里塞自由文本。

- 入参 schema 校验：按 `SKILL.md` 声明的 schema 校验 arguments，类型 / 必需项不符时返回结构化错误回灌给模型。

- 通用 dispatcher 按 registry 路由到对应 skill 入口并执行，结果包进 `<tool_response>`，全程无任何 `if name == ...` 硬编码分支。

- 执行隔离与错误处理：skill 执行异常 / 超时不崩溃，stderr 与非零退出码作为结构化反馈返回。

#### B4. Prompt 自动生成（6 分）

- system prompt 的工具说明由 registry 中各 skill 的 frontmatter（name + description + schema + examples）自动拼装；新增 / 移除 skill 时 prompt 自动更新，与手写零耦合。

#### B6. 向后兼容与回归（门槛项）

- 将现有 `python_code` 与 `local_rag` 改写为 `SKILL.md` skill，行为不变。

- 在 MATH-500 上回归（可固定种子抽样 ≥100 题），指标相对 Task A 基线不得回退（误差 ≤3%）。

- 本项作为 B1-B3 的前置门槛：若回归不通过，B1-B3 各项最高只给一半分。

### Task C: GitHub 提交记录 & 文档说明（25 分）

- Git 提交记录：私有 GitHub 仓库，多次有意义的 commit（非一次性提交），message 规范（如 `feat: structured function-call parser`、`refactor: skill registry & dispatcher`）。

- `README.md`：
  1. 核心改动点说明（重构前后 tool call 流程对比、为什么这样设计）；
  2. 运行教程（从零复现）；
  3. 复现结果汇总（Task A 基线 + Task B 回归对比）；
  4. 遇到的问题与解决方案。

| 采分项 | 分值 |
|---|---|
| Git 提交记录清晰，多次有意义的 commit | **6** |
| README 核心改动点（重构前后对比）清晰 | **8** |
| README 运行教程完整，别人能复现 | **5** |
| README 复现结果汇总 + 问题记录 | **6** |

### Task D（附加题）: 新增一个 Skill + MCP 接入（+20 分 Bonus）

附加题：本任务为 Bonus 题，不计入基础 100 分。完成后可额外获得最多 20 分加分。适合已顺利完成 Task A-C 且有余力的候选人。

- D1 新增一个 skill（+8）：在新的 `SKILL.md` 体系下，只通过新增一个 skill 目录（一个 `SKILL.md` + 入口脚本，不改框架核心）就接入一个新工具（如 calculator / unit-test runner 等），证明扩展性确实改善了。在 MATH-500 上展示 ≥1 个调用该新 skill 的 trajectory。

- D2 MCP 接入（可选，+12）：对标 OpenClaw 的 mcporter，MCP 是 skill 体系之外的“第二条接入通路”，外部工具不必逐个写成 `SKILL.md`，而是通过一条通用集成层接入。把至少一个 MCP server 的工具接进 AlphaApollo 的同一套 dispatcher，验证跨进程的工具发现与调用，并展示 ≥1 个端到端 trajectory。

## 3 提交物

- GitHub 仓库：包含所有代码、配置文件和 README，含环境搭建步骤、运行命令、依赖说明。

- 实验日志：关键实验的运行日志、模型输出样例（含结构化 function-call 与 `<tool_response>`）、评估结果 JSON、Task A 基线与 Task B 回归对比表。

## 4 参考资料

| 资料 | 链接 |
|---|---|
| AlphaApollo 仓库 | https://github.com/tmlr-group/AlphaApollo |
| AlphaApollo 论文 | https://arxiv.org/abs/2510.06261 |
| AlphaApollo `rollout_loop.py` | https://github.com/tmlr-group/AlphaApollo/blob/main/alphaapollo/core/generation/multi_turn_rollout/rollout_loop.py |
| AlphaApollo 工具文档 | https://github.com/tmlr-group/AlphaApollo/blob/main/docs/core-modules/tools.md |
| MATH-500 数据集 | https://huggingface.co/datasets/HuggingFaceH4/MATH-500 |
| OpenClaw 仓库 | https://github.com/openclaw/openclaw |
