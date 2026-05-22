# Phase 2: B2 - Skill Loader、Registry 与启用配置 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-22
**Phase:** 2-B2 Skill Loader、Registry 与启用配置
**Areas discussed:** Phase 2 范围, Registry 错误策略, 内置 Skill 创建时机

---

## Phase 2 范围

| Option | Description | Selected |
|--------|-------------|----------|
| Registry + 配置 | 完成 registry、内置 skill 目录、`env.skills` 设计和旧配置兼容策略。 | ✓ |
| 只做 Registry | 先只实现注册表，不碰配置兼容，风险更低但 Phase 2 交付偏薄。 | |
| 接入 env | 同时改 `env.py` 接入执行路径，进度更快但容易让新手暂时讲不清。 | |

**User's choice:** `1A`
**Notes:** 选择推荐路线，Phase 2 保持完整但不提前触碰执行路径。

---

## Registry 错误策略

| Option | Description | Selected |
|--------|-------------|----------|
| 收集错误继续 | 合法 skill 仍可注册，错误统一返回，适合调试多个 skill。 | ✓ |
| 立刻失败 | 发现一个错误就停止，简单但不利于一次看到所有问题。 | |
| 静默跳过 | 流程最顺，但容易隐藏配置问题，不建议。 | |

**User's choice:** `2A`
**Notes:** registry 应该帮助用户诊断问题，而不是隐藏坏 `SKILL.md`。

---

## 内置 Skill 创建时机

| Option | Description | Selected |
|--------|-------------|----------|
| 现在创建 | registry 可以用真实内置 skill 测试，但暂时不执行它们。 | ✓ |
| Phase 4 创建 | Phase 2 更抽象，但测试会缺少真实业务样例。 | |
| 只建 python_code | 先做最简单工具，`local_rag` 留到后面，理解成本更低。 | |

**User's choice:** `3A`
**Notes:** `python_code` 和 `local_rag` 的 `SKILL.md` 现在创建；真实执行迁移留到 Phase 4。

---

## the agent's Discretion

- registry 的内部类名和结果包装可以在计划阶段确定。
- registry 可以复用 Phase 1 的 `SkillLoadError`，也可以新增 registry 错误类型，但要保持文档可解释。

## Deferred Ideas

- `<tool_call>` parser、dispatcher、prompt 自动生成、env 迁移和 MATH-500 回归都不属于 Phase 2。
