# AlphaApollo Task B Skill Refactor

## What This Is

这是一个基于 AlphaApollo 主干的研究实习 mini-project，目标是把当前硬编码的 tool call 流程升级为目录化、自描述、可动态发现的 `SKILL.md` Skill 系统，并让模型使用结构化 function-call 协议调用工具。

项目使用现有 AlphaApollo 代码为基础，重点改造 environment side 的工具解析、注册、路由、执行和 prompt 生成逻辑，同时保持现有 `python_code` 与 `local_rag` 行为兼容。

## Core Value

在不破坏 MATH-500 agentic reasoning 回归指标的前提下，让 AlphaApollo 的工具系统从“写死标签 + if 分支”变成“可插拔 Skill + 通用 dispatcher”。

## Requirements

### Validated

(None yet — 先完成 Task A/B 回归后再移动到这里)

### Active

- [x] 完成 B1：设计并实现 `SKILL.md` 规范、frontmatter 解析器、字段校验和中文编写说明。
- [ ] 完成 B2：实现 Skill loader 与 registry，支持扫描 skill 目录并按配置启用 skill。
- [ ] 完成 B3：实现结构化 `<tool_call>{...}</tool_call>` 协议、参数 schema 校验和通用 dispatcher。
- [ ] 完成 B4：从 registry 自动生成工具 prompt 说明，降低 prompt 与具体工具的耦合。
- [ ] 完成 B6：将 `python_code` 和 `local_rag` 迁移为 `SKILL.md` skill，并完成 MATH-500 回归验证。
- [ ] 完成 Task C 所需文档和 Git 提交记录：清晰 commit、README、实验日志、问题记录。
- [ ] 保留学习记录，确保每个核心模块都能用自己的话解释。

### Out of Scope

- MCP 接入 — 属于 Task D bonus，只有 Task B/C 稳定后再考虑。
- 新增复杂外部工具 — Task B 的主线是迁移现有 `python_code` 与 `local_rag`，不先扩展工具面。
- 重写 PPO/GRPO trainer — Task B 主要改 environment side tool system，不改训练算法主体。
- 完全复制 OpenClaw 架构 — 本项目只借鉴 skill 插件化思想，避免大规模外部架构迁移。

## Context

- 当前 AlphaApollo 通过文本标签调用工具，例如 `<python_code>...</python_code>` 和 `<local_rag>...</local_rag>`。
- 旧流程依赖 `projection.py` 正则解析、`env.py` 中的硬编码 if/elif 分支，以及 `manager.py` 中的工具函数。
- Task B 要求每个工具变为一个目录，核心是带 YAML frontmatter 的 `SKILL.md`，包含 name、description、参数 schema、调用入口和 examples。
- 新模型侧调用应使用结构化 JSON，例如 `<tool_call>{"name":"python_code","arguments":{"code":"print(1+1)"}}</tool_call>`。
- 重要评估基准是 MATH-500，Task B 回归指标相对 Task A baseline 误差不得超过 3%。
- 用户是相关技术新手，因此所有项目文档、设计说明和学习记录均使用中文，并优先保证可解释性。

## Constraints

- **兼容性**: `python_code` 与 `local_rag` 迁移后行为不能明显变化 — 否则 B6 回归失败会影响 B1-B3 得分。
- **扩展性**: 核心 dispatcher 不得硬编码具体工具名 — 新增工具应主要通过新增 skill 目录完成。
- **错误处理**: 解析失败、参数校验失败、执行异常、超时、stderr 和非零退出码都必须返回结构化错误，不让 rollout 崩溃。
- **可学习性**: 每个阶段必须配套中文学习记录和自测问题 — 避免只会运行 AI 生成代码但无法解释实现。
- **时间**: 建议完成时间 7 天 — 阶段拆分需要保持小步快跑。
- **Git**: 需要多次有意义 commit — 不做一次性大提交。

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 所有 GSD 与 Task B 文档使用中文 | 用户刚接触这些技术，中文文档更利于理解和面试复盘 | — Pending |
| 先做 B1 parser，再做 registry/dispatcher | 先把 skill 数据结构定稳，避免后续执行层返工 | — Pending |
| 初期保留旧配置兼容路径 | 降低回归风险，方便逐步迁移 `enable_python_code`/`enable_local_rag` | ✓ Good |
| Phase 2 只加载内置 skill 元数据，不执行工具 | 避免提前扰动 `env.py`，把执行迁移留到 dispatcher/env 阶段 | ✓ Good |
| B2 拆成 registry 模块和运行时接入两步 | 当前已完成 registry 基础能力；真正让训练流程使用 `env.skills` 需要在 Phase 4 接入 env | ✓ Good |
| Task B 主要改 environment side，不碰 trainer 主体 | mini-project 明确关注 tool call 到 skill；trainer 改动风险高 | — Pending |
| Phase 1 先只实现 SKILL.md loader，不接 registry/env | 降低风险，先建立稳定内部契约和测试 | ✓ Good |

---
*Last updated: 2026-05-22 after Phase 2 scope correction*
