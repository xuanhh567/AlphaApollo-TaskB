# Phase 4: 迁移 Env Tool 执行路径与内置 Skill - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-22
**Phase:** 4-Env Tool Path Migration
**Areas discussed:** 接入范围, 旧格式兼容, 内置 skill entrypoint 兼容, env.skills 运行时接入

---

## 接入范围

| Option | Description | Selected |
|--------|-------------|----------|
| 先接 training | 当前 Task B 配置主线使用 `informal_math_training`，风险最低。 | ✓ |
| training/evolving 同时接 | 覆盖更完整，但容易一次改太多。 | |
| 只做 shared helper | 抽象漂亮，但没有端到端 env 验证。 | |

**Choice:** 先接 `informal_math_training`，记录 evolving 差异，后续同步。

---

## 旧格式兼容

| Option | Description | Selected |
|--------|-------------|----------|
| 保留旧标签并新增 `<tool_call>` | 最稳，旧 prompt 和 trajectory 不会马上失效。 | ✓ |
| 直接替换旧标签 | 代码更干净，但回归风险高。 | |
| 只支持旧标签 | 没有完成 Task B 的结构化调用升级。 | |

**Choice:** 过渡期双轨兼容。

---

## 内置 skill entrypoint 兼容

| Option | Description | Selected |
|--------|-------------|----------|
| 复用 / 包装 `InformalMathToolGroup` | 最容易保持旧 `text_result` + `score` 语义。 | ✓ |
| 直接调用底层函数 | 更通用，但容易破坏旧行为。 | |

**Choice:** 优先保持旧行为，不为了“纯粹 skill”牺牲回归。

---

## env.skills 运行时接入

| Option | Description | Selected |
|--------|-------------|----------|
| Phase 4 接入 env 构造 | 补齐 B2 runtime gap。 | ✓ |
| 留到 prompt 阶段 | 会继续让 B2 处于不完整状态。 | |

**Choice:** Phase 4 接入运行时配置。

---

## Deferred Ideas

- Prompt 自动生成留到 Phase 5。
- MATH-500 回归留到 Phase 6。
