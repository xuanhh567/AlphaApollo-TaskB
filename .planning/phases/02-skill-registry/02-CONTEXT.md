# Phase 2: B2 - Skill Loader、Registry 与启用配置 - Context

**Gathered:** 2026-05-22
**Status:** Ready for planning

<domain>
## Phase Boundary

本阶段只负责把 Phase 1 已经能解析出来的 `SkillSpec` 组织成一个可查询、可过滤、可诊断的 registry。

换句话说，Phase 1 是“读懂一本工具说明书”，Phase 2 是“管理一整个工具目录”。

本阶段包含：

- 扫描配置指定的 skill 目录。
- 注册合法的 `SkillSpec`。
- 支持按 skill name 查询和列出 skill。
- 创建内置 `python_code` / `local_rag` 的 `SKILL.md` 初版。
- 设计并实现 `env.skills` 启用配置。
- 保留旧配置 `enable_python_code` / `enable_local_rag` 到新配置的兼容转换。

本阶段不包含：

- 不解析模型输出的 `<tool_call>`。
- 不实现 dispatcher。
- 不真正执行 skill 的 `entrypoint`。
- 不改造 `env.py` 的工具执行路径。

</domain>

<decisions>
## Implementation Decisions

### Phase 2 范围

- **D-01:** Phase 2 采用 `Registry + 配置` 范围，而不是只做 registry，也不提前接入 `env.py`。
- **D-02:** 本阶段可以新增 `alphaapollo/core/skills/registry.py`、`alphaapollo/core/skills/builtin/`、内置 `SKILL.md` 和 registry 测试。
- **D-03:** `env.py` 执行路径留到后续 Phase 4，避免一次性把 parser、registry、dispatcher、env 迁移混在一起。

### Registry 错误策略

- **D-04:** 扫描多个 skill 目录时，如果某个 `SKILL.md` 写错，registry 应该收集错误并继续扫描其他目录。
- **D-05:** 合法 skill 可以继续注册；坏 skill 的错误通过结构化结果返回，便于一次看到所有问题。
- **D-06:** 不允许静默跳过坏 skill，因为这会让配置问题在训练时才暴露。

### 内置 Skill 创建时机

- **D-07:** Phase 2 现在就创建 `python_code` 和 `local_rag` 的 `SKILL.md`。
- **D-08:** 这两个内置 skill 在 Phase 2 只用于 registry 加载、启用过滤和 prompt 元信息准备，暂时不执行。
- **D-09:** `python_code` / `local_rag` 的真实执行迁移留到 Phase 4，保持当前环境执行逻辑不被提前扰动。

### 配置兼容策略

- **D-10:** 新配置建议使用 `env.skills=[python_code, local_rag]` 表达启用工具列表。
- **D-11:** 初期必须兼容旧配置：
  - `env.informal_math.enable_python_code=true` 推导出 `python_code` 启用。
  - `env.informal_math.enable_local_rag=true` 推导出 `local_rag` 启用。
- **D-12:** 如果新旧配置同时存在，优先使用显式的新配置 `env.skills`，因为它更清晰、更可扩展。

### the agent's Discretion

- registry 的具体类名、结果包装名、测试组织方式可由实现者决定，但必须保持新手可解释。
- 可以复用 Phase 1 的 `SkillLoadError`，也可以新增 registry 专用错误类型；如果新增，文档必须解释它和 loader 错误的区别。

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Planning

- `.planning/PROJECT.md` — Task B 总目标、约束和阶段边界。
- `.planning/REQUIREMENTS.md` — REG-01 到 REG-05 的验收要求。
- `.planning/ROADMAP.md` — Phase 2 的 scope 和 success criteria。
- `.planning/STATE.md` — 当前项目状态、工作约定和已知风险。

### Phase 1 Design and Implementation

- `docs/task-b/phase-1-skill-md-spec.md` — `SKILL.md` 字段规范、parser 设计和自测问题。
- `alphaapollo/core/skills/schema.py` — `SkillSpec`、`SkillParameter`、`SkillLoadError` 等内部契约。
- `alphaapollo/core/skills/loader.py` — 已实现的 `load_skill_from_dir` / `load_skill_file`。
- `tests/test_skill_loader.py` — Phase 1 loader 的测试风格和轻量导入方式。

### Existing Tool System

- `examples/configs/rl_informal_math_tool.yaml` — 旧工具启用配置位置，包括 `enable_python_code` 和 `enable_local_rag`。
- `alphaapollo/core/tools/manager.py` — 当前 `python_code` / `local_rag` 工具函数和参数语义。
- `alphaapollo/core/environments/informal_math_training/env.py` — 旧工具执行路径；Phase 2 不改执行路径，但需要理解后续连接点。

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `alphaapollo/core/skills/loader.py`：Phase 2 registry 应该复用 `load_skill_from_dir(...)`，不要重新解析 YAML。
- `alphaapollo/core/skills/schema.py`：registry 的核心值应该是 `SkillSpec`，不要让后续模块直接依赖原始 dict。
- `tests/test_skill_loader.py`：可复用轻量测试方式，设置 `ALPHAAPOLLO_SKIP_VERL_ALIAS=1` 避免训练依赖影响单元测试。

### Established Patterns

- 当前配置通过 Hydra/OmegaConf override 写入，例如 `env.informal_math.enable_python_code=true`。
- 当前工具系统中 `python_code` 和 `local_rag` 的参数语义已经在 `InformalMathToolGroup` 中存在，`SKILL.md` 应贴近旧语义。
- 当前 env 执行路径仍然硬编码 `if tool_name == "python_code"`，Phase 2 只准备 registry，不提前替换这部分。

### Integration Points

- Phase 2 新增的 registry 后续会被 Phase 3 dispatcher 和 Phase 5 prompt renderer 使用。
- Phase 4 才会把 registry/dispatcher 接入 `informal_math_training/env.py`。
- 新配置 `env.skills` 未来会影响 prompt 生成和可调用工具列表。

</code_context>

<specifics>
## Specific Ideas

- 用户明确选择 `1A 2A 3A`：
  - Phase 2 做 `Registry + 配置`。
  - 错误策略采用“收集错误继续”。
  - Phase 2 现在创建 `python_code` / `local_rag` 的 `SKILL.md`。
- 文档必须使用中文，并保持新手能解释。
- Phase 2 不急着写 `env.py`，先把 registry 的职责讲清楚。

</specifics>

<deferred>
## Deferred Ideas

- dispatcher 执行 `entrypoint` 留到 Phase 3。
- `env.py` 执行路径迁移留到 Phase 4。
- prompt 自动生成留到 Phase 5。
- MATH-500 回归留到 Phase 6。

</deferred>

---

*Phase: 2-B2 Skill Loader、Registry 与启用配置*
*Context gathered: 2026-05-22*
