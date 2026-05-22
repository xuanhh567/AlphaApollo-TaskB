# Roadmap: AlphaApollo Task B Skill Refactor

**Created:** 2026-05-22
**Mode:** Standard phased delivery
**Language:** 中文

## Phase 1: B1 - SKILL.md 规范与解析器

**Goal:** 设计 skill 目录与 `SKILL.md` frontmatter 规范，实现最小 parser、字段校验和中文编写说明。

**Requirements:** SKILL-01, SKILL-02, SKILL-03, SKILL-04, SKILL-05

**Scope:**
- 新增 `alphaapollo/core/skills/schema.py`
- 新增 `alphaapollo/core/skills/loader.py`
- 新增 `docs/task-b/design.md` 或 `docs/skills.md`
- 为 parser 添加小范围单元测试或脚本级验证

**Success Criteria:**
- 能读取一个合法 `SKILL.md` 并生成 `SkillSpec`
- 缺字段、字段类型错误、frontmatter 缺失时返回结构化错误
- 用户能用中文解释 `SkillSpec` 每个字段的用途

**Status:** Complete

**Completed:** 2026-05-22

**Delivered:**
- `alphaapollo/core/skills/schema.py` 定义 Skill 元数据内部契约。
- `alphaapollo/core/skills/loader.py` 解析 `SKILL.md` frontmatter 并返回 `SkillSpec` 或结构化错误。
- `tests/test_skill_loader.py` 覆盖合法 skill 和常见错误格式。
- `docs/task-b/design.md` 用中文解释 `SKILL.md` 规范和 parser 计划。

## Phase 2: B2 - Skill Loader、Registry 与启用配置

**Goal:** 扫描 skill 目录，注册合法 skill，并通过声明式配置决定启用哪些 skill。

**Requirements:** REG-01, REG-02, REG-03, REG-04, REG-05

**Scope:**
- 新增 `alphaapollo/core/skills/registry.py`
- 建立 `alphaapollo/core/skills/builtin/` 目录结构
- 创建 `python_code/SKILL.md` 与 `local_rag/SKILL.md` 初版
- 支持新配置 `env.skills`
- 保留旧配置到新配置的兼容转换

**Success Criteria:**
- registry 能列出启用的 skill
- 重名、缺失、未启用 skill 都有清晰错误
- 不改具体工具代码也能完成注册发现

**Status:** In Progress

**Context:** `.planning/phases/02-skill-registry/02-CONTEXT.md`

## Phase 3: B3 - 结构化 Tool Call、参数校验与 Dispatcher

**Goal:** 支持统一 `<tool_call>{...}</tool_call>` 协议，并通过通用 dispatcher 执行 skill。

**Requirements:** CALL-01, CALL-02, CALL-03, CALL-04, CALL-05, CALL-06

**Scope:**
- 新增 `alphaapollo/core/skills/call_parser.py`
- 新增 `alphaapollo/core/skills/dispatcher.py`
- 实现 JSON 解析、unknown skill、required/type 校验
- 支持 Python function entrypoint
- 设计统一 ToolResult / ToolError 数据结构

**Success Criteria:**
- dispatcher 不包含具体工具名硬编码
- JSON 错、缺参数、类型错、unknown skill 都能返回结构化错误
- 成功结果和失败结果都能被包装进 `<tool_response>`

**Status:** Pending

## Phase 4: 迁移 Env Tool 执行路径与内置 Skill

**Goal:** 把 `env.py` 中硬编码的 `python_code` / `local_rag` 分支迁移到 Skill dispatcher，保持旧行为兼容。

**Requirements:** COMPAT-01, COMPAT-02, COMPAT-03, COMPAT-04

**Scope:**
- 改造 `alphaapollo/core/environments/informal_math_training/projection.py`
- 改造 `alphaapollo/core/environments/informal_math_training/env.py`
- 必要时保留旧标签到新 `<tool_call>` 的兼容桥接
- 对 `python_code` 和 `local_rag` 做小样例验证

**Success Criteria:**
- `<tool_call>{"name":"python_code",...}</tool_call>` 可执行
- `<tool_call>{"name":"local_rag",...}</tool_call>` 可路由
- 旧 prompt/旧标签路径在过渡期不被立即破坏，除非已有等价替代

**Status:** Pending

## Phase 5: B4 - Prompt 自动生成

**Goal:** 从 registry 中 skill 元信息自动生成工具说明，减少 prompt 与具体工具的手写耦合。

**Requirements:** PROMPT-01, PROMPT-02, PROMPT-03

**Scope:**
- 在 skills 模块中提供 prompt rendering helper
- 修改 informal math training prompt 选择逻辑
- 确保 prompt 明确结构化调用格式和 examples

**Success Criteria:**
- 新增/移除 skill 后，prompt 工具说明自动变化
- prompt 中不再手写每个工具的完整 schema 和示例
- 用户能解释 prompt 自动生成与 registry 的关系

**Status:** Pending

## Phase 6: B6/C - 回归、文档与提交整理

**Goal:** 完成 Task A/B 回归对比、保存 trajectory 样例，并整理 README、实验记录和 Git 提交。

**Requirements:** COMPAT-05, COMPAT-06, DOC-01, DOC-02, DOC-03, DOC-04

**Scope:**
- 建立 `docs/task-b/experiments.md`
- 记录 MATH-500 baseline 与 skill 版本结果
- 保存至少一个结构化 tool call trajectory
- 更新根 `README.md` 或新增 Task B 专区
- 检查 commit 粒度与 message

**Success Criteria:**
- Task B 回归指标相对 Task A baseline 误差不超过 3%
- README 能让他人复现环境和实验
- 面试复习文档能回答核心调用链问题

**Status:** Pending

## Future / Bonus: Task D - 新 Skill 与 MCP

**Goal:** 在 Task B/C 稳定后，验证新 Skill 的扩展性，或接入 MCP。

**Requirements:** BONUS-01, BONUS-02, BONUS-03

**Status:** Deferred

---
*Roadmap created: 2026-05-22*
*Last updated: 2026-05-22 after Phase 1 completion*
