# Requirements: AlphaApollo Task B Skill Refactor

**Defined:** 2026-05-22
**Core Value:** 在不破坏 MATH-500 agentic reasoning 回归指标的前提下，让 AlphaApollo 的工具系统从“写死标签 + if 分支”变成“可插拔 Skill + 通用 dispatcher”。

## v1 Requirements

### Skill 规范与解析

- [x] **SKILL-01**: 每个 skill 必须是一个目录，并包含一个 `SKILL.md`。
- [x] **SKILL-02**: `SKILL.md` frontmatter 必须至少声明 `name`、`description`、参数 schema、调用入口和 examples。
- [x] **SKILL-03**: parser 必须能解析 YAML frontmatter，并把合法内容转换为内部 `SkillSpec`。
- [x] **SKILL-04**: parser 必须在缺字段或格式错误时返回结构化错误，而不是抛出未处理异常。
- [x] **SKILL-05**: 仓库必须提供中文 `SKILL.md` 编写说明，能指导他人新增 skill。

### Registry 与配置

- [x] **REG-01**: Skill loader 必须能扫描配置指定的 skill 目录。
- [x] **REG-02**: Registry 必须能按 `name` 注册和查找 skill。
- [x] **REG-03**: 重名 skill 必须返回清晰错误或拒绝注册，不能静默覆盖。
- [x] **REG-04**: 启用工具应由声明式配置控制，例如 `env.skills=[python_code, local_rag]`。
- [x] **REG-05**: 初期必须兼容旧的 `enable_python_code` 与 `enable_local_rag` 配置，降低回归风险。

> Phase 4 已将 `env.skills` / 旧开关兼容接入 `informal_math_training` 运行时；prompt 自动生成仍留到 Phase 5。

### 结构化调用与 Dispatcher

- [x] **CALL-01**: 模型侧工具调用必须支持统一结构化格式，例如 `<tool_call>{"name":"...","arguments":{...}}</tool_call>`。
- [x] **CALL-02**: parser 必须能识别无效 JSON、缺少 `name`、缺少 `arguments`、unknown skill 等错误。
- [x] **CALL-03**: 参数校验必须按 `SKILL.md` schema 检查 required 字段与基础类型。
- [x] **CALL-04**: 通用 dispatcher 必须通过 registry 路由 skill，不得包含 `if name == "python_code"` 这类具体工具硬编码。
- [x] **CALL-05**: dispatcher 必须把成功和失败结果都包装为结构化反馈，并最终进入 `<tool_response>`。
- [x] **CALL-06**: skill 执行异常、超时、stderr 和非零退出码不能导致 rollout 崩溃。

> Phase 4 已让 `informal_math_training` 通过 `dispatch_tool_call(..., executor=...)` 执行 runtime ToolGroup，并将成功、参数错误和工具禁用反馈包进 `<tool_response>`。`python_code` 的 timeout / stderr / 非零退出码继续由旧 `InformalMathToolGroup` 处理。

### Prompt 自动生成

- [ ] **PROMPT-01**: 工具说明必须能从 registry 中的 `name`、`description`、schema 和 examples 自动生成。
- [ ] **PROMPT-02**: 新增或移除 skill 后，prompt 工具说明应自动更新，不需要手写每个工具说明。
- [ ] **PROMPT-03**: prompt 必须明确告诉模型使用统一 `<tool_call>` 格式。

### 内置 Skill 迁移与回归

- [x] **COMPAT-01**: 现有 `python_code` 必须迁移为 `SKILL.md` skill。
- [x] **COMPAT-02**: 现有 `local_rag` 必须迁移为 `SKILL.md` skill。
- [x] **COMPAT-03**: `python_code` 迁移前后的成功、失败、超时和禁用反馈必须保持语义一致。
- [x] **COMPAT-04**: `local_rag` 迁移前后的成功、失败、禁用和参数错误反馈必须保持语义一致。
- [ ] **COMPAT-05**: 在 MATH-500 上完成 Task A baseline 与 Task B skill 版本回归对比，指标误差不超过 3%。
- [ ] **COMPAT-06**: 至少保存一个包含结构化 function-call 与 `<tool_response>` 的 trajectory 样例。

### 文档、学习与提交

- [ ] **DOC-01**: `docs/task-b/learning-log.md` 必须记录每个阶段的目标、改动和未理解问题。
- [ ] **DOC-02**: README 必须说明重构前后 tool call 流程对比和设计理由。
- [ ] **DOC-03**: README 或 `docs/task-b/experiments.md` 必须包含 Task A baseline 与 Task B 回归结果。
- [ ] **DOC-04**: Git 历史必须包含多次有意义 commit，而不是一次性提交。

## v2 Requirements

### Bonus / Task D

- **BONUS-01**: 新增一个非内置 skill，只通过新增目录接入，不改核心代码。
- **BONUS-02**: 展示至少一个调用新 skill 的 MATH-500 trajectory。
- **BONUS-03**: 可选接入一个 MCP server 的工具，走同一套 dispatcher。

## Out of Scope

| Feature | Reason |
|---------|--------|
| 完整 MCP 接入 | 属于 Task D bonus，先保证 Task B 核心可交付 |
| 大规模重写 trainer | 风险高且不属于 Task B 核心目标 |
| 迁移所有未来工具 | v1 只承诺 `python_code` 与 `local_rag` |
| 公共 GitHub 仓库 | mini-project 要求私有 GitHub 仓库 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SKILL-01 | Phase 1 | Complete |
| SKILL-02 | Phase 1 | Complete |
| SKILL-03 | Phase 1 | Complete |
| SKILL-04 | Phase 1 | Complete |
| SKILL-05 | Phase 1 | Complete |
| REG-01 | Phase 2 | Complete |
| REG-02 | Phase 2 | Complete |
| REG-03 | Phase 2 | Complete |
| REG-04 | Phase 2/4 | Complete |
| REG-05 | Phase 2/4 | Complete |
| CALL-01 | Phase 3 | Complete |
| CALL-02 | Phase 3 | Complete |
| CALL-03 | Phase 3 | Complete |
| CALL-04 | Phase 3 | Complete |
| CALL-05 | Phase 3/4 | Complete |
| CALL-06 | Phase 3/4 | Complete |
| COMPAT-01 | Phase 4 | Complete |
| COMPAT-02 | Phase 4 | Complete |
| COMPAT-03 | Phase 4 | Complete |
| COMPAT-04 | Phase 4 | Complete |
| PROMPT-01 | Phase 5 | Pending |
| PROMPT-02 | Phase 5 | Pending |
| PROMPT-03 | Phase 5 | Pending |
| COMPAT-05 | Phase 6 | Pending |
| COMPAT-06 | Phase 6 | Pending |
| DOC-01 | Phase 6 | Pending |
| DOC-02 | Phase 6 | Pending |
| DOC-03 | Phase 6 | Pending |
| DOC-04 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 29 total
- Mapped to phases: 29
- Complete: 20
- Unmapped: 0

---
*Requirements defined: 2026-05-22*
*Last updated: 2026-05-22 after Phase 4 runtime dispatcher alignment*
