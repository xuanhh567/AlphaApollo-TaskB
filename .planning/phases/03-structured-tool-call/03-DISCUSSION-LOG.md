# Phase 3: B3 - 结构化 Tool Call、参数校验与 Dispatcher - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-22
**Phase:** 3-B3 结构化 Tool Call、参数校验与 Dispatcher
**Areas discussed:** Tool Call 格式, 参数校验, Dispatcher 执行边界

---

## Tool Call 格式

| Option | Description | Selected |
|--------|-------------|----------|
| 单个 `<tool_call>` | 每个 action 只允许一个完整结构化调用，贴近旧 projection 的约束。 | ✓ |
| 多个 `<tool_call>` | 支持一次输出多个工具调用，能力更强但 rollout 和 reward 归因更复杂。 | |
| 混合旧标签 | 在 parser 中同时处理 `<python_code>` / `<local_rag>`，兼容快但职责混乱。 | |

**Choice:** 使用保守默认：单个 `<tool_call>`。
**Notes:** 旧标签兼容留到 Phase 4，避免 Phase 3 parser 职责过重。

---

## 参数校验

| Option | Description | Selected |
|--------|-------------|----------|
| 使用 `SkillSpec.parameters` | 复用 Phase 1 的内部契约，避免重复 schema。 | ✓ |
| 新增独立 JSON Schema | 更标准但复杂度较高，和当前 SkillSpec 重叠。 | |
| 不校验参数 | 实现最快，但会把错误推迟到工具执行时才暴露。 | |

**Choice:** 使用 `SkillSpec.parameters`。
**Notes:** Phase 3 先支持基础类型和 required/default，复杂嵌套 schema 后续再扩展。

---

## Dispatcher 执行边界

| Option | Description | Selected |
|--------|-------------|----------|
| 独立 dispatcher 模块 | 先独立测试 parser/validator/dispatcher，不接 `env.py`。 | ✓ |
| 直接接入 env.py | 更快看到端到端效果，但风险和理解成本更高。 | |
| 只写 parser 不写 dispatcher | 更简单，但不能覆盖 CALL-04 到 CALL-06。 | |

**Choice:** 独立 dispatcher 模块。
**Notes:** `env.py` 迁移留到 Phase 4。

---

## the agent's Discretion

- `ToolCall`、`ToolResult`、`ToolError` 的字段可在 plan 和实现中细化。
- dispatcher 测试应使用 fake entrypoint，避免依赖真实 Python 执行或 RAG 服务。

## Deferred Ideas

- 多工具调用、旧标签兼容、prompt 自动生成、MATH-500 回归均不属于 Phase 3 context 的立即范围。
