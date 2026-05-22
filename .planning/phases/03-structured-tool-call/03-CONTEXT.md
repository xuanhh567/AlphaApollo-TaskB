# Phase 3: B3 - 结构化 Tool Call、参数校验与 Dispatcher - Context

**Gathered:** 2026-05-22
**Status:** Ready for planning

<domain>
## Phase Boundary

本阶段负责把模型输出的统一结构化工具调用：

```xml
<tool_call>
{"name":"python_code","arguments":{"code":"print(1 + 1)"}}
</tool_call>
```

解析成内部对象，并根据 Phase 2 registry 中的 `SkillSpec` 做检查，最后通过通用 dispatcher 执行 skill。

本阶段包含：

- 解析 `<tool_call>{...}</tool_call>`。
- 检查 JSON 是否合法。
- 检查是否包含 `name` 和 `arguments`。
- 检查 `name` 是否存在于 registry。
- 按 `SkillSpec.parameters` 检查 required 参数和基础类型。
- 设计 `ToolCall`、`ToolResult`、`ToolError` 这类结构。
- 实现通用 dispatcher，支持 `python_function` entrypoint。

本阶段不包含：

- 不改造 `env.py` 的旧工具执行路径。
- 不替换 `projection.py`。
- 不做 prompt 自动生成。
- 不跑 MATH-500。

</domain>

<decisions>
## Implementation Decisions

### Tool Call 格式

- **D-01:** Phase 3 统一支持一个结构化标签：`<tool_call>{...}</tool_call>`。
- **D-02:** JSON 最小结构固定为：

```json
{"name": "skill_name", "arguments": {}}
```

- **D-03:** `name` 必须是非空字符串。
- **D-04:** `arguments` 必须是 object / dict。
- **D-05:** 每个模型输出中先只允许一个完整 `<tool_call>`。多个 `<tool_call>` 视为非法，保持和旧 projection 中“多个工具标签不合法”的训练约束一致。

### 参数校验

- **D-06:** 参数校验直接使用 `SkillSpec.parameters`，不重新定义一套 schema。
- **D-07:** Phase 3 先支持 Phase 1 已定义的基础类型：
  - `string`
  - `integer`
  - `number`
  - `boolean`
  - `object`
  - `array`
- **D-08:** 缺少 required 参数时返回结构化错误，不执行工具。
- **D-09:** 参数类型错误时返回结构化错误，不执行工具。
- **D-10:** 可选参数如果有 `default`，dispatcher 执行前可以补默认值。

### Dispatcher 执行边界

- **D-11:** dispatcher 通过 registry 查找 skill，不允许出现 `if name == "python_code"` 这种具体工具名硬编码。
- **D-12:** Phase 3 支持 `entrypoint.type = python_function`。
- **D-13:** dispatcher 可以通过 `importlib` 动态导入 `entrypoint.path` 指向的函数。
- **D-14:** dispatcher 暂时作为独立模块测试，不接入 `env.py`；`env.py` 迁移留到 Phase 4。

### 结果和错误

- **D-15:** 设计统一 `ToolResult`，用于表示执行成功或工具函数自身返回。
- **D-16:** 设计统一 `ToolError`，用于表示解析错误、unknown skill、参数错误、导入错误、执行异常等。
- **D-17:** 成功和失败都要能转换成 `<tool_response>...</tool_response>` 所需内容，但真正接入 env 的包装留到 Phase 4。

### the agent's Discretion

- `ToolCall`、`ToolResult`、`ToolError` 的具体字段名可由实现者决定，但必须便于测试断言和中文解释。
- dispatcher 测试可以使用测试内临时函数或小型 fake entrypoint，避免单元测试真的执行 `python_code` 或访问 RAG 服务。

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Planning

- `.planning/PROJECT.md` — Task B 总目标、兼容性约束和阶段边界。
- `.planning/REQUIREMENTS.md` — CALL-01 到 CALL-06 的验收要求。
- `.planning/ROADMAP.md` — Phase 3 scope 和 success criteria。
- `.planning/STATE.md` — 当前项目状态和工作约定。

### Existing Skill Foundation

- `alphaapollo/core/skills/schema.py` — `SkillSpec`、`SkillParameter` 等参数校验依据。
- `alphaapollo/core/skills/loader.py` — `SKILL.md` 解析入口。
- `alphaapollo/core/skills/registry.py` — registry 查询和内置 skill 加载。
- `alphaapollo/core/skills/builtin/python_code/SKILL.md` — `python_code` 的参数 schema。
- `alphaapollo/core/skills/builtin/local_rag/SKILL.md` — `local_rag` 的参数 schema。
- `tests/test_skill_loader.py` — 轻量测试风格。
- `tests/test_skill_registry.py` — registry 测试风格。

### Old Tool Call Path

- `alphaapollo/core/environments/informal_math_training/projection.py` — 旧标签解析规则，尤其是多个工具标签判 invalid。
- `alphaapollo/core/environments/informal_math_training/env.py` — 旧工具执行分支，Phase 4 会迁移这里。
- `alphaapollo/core/tools/core.py` — 旧 `ToolGroup` 执行模型。
- `alphaapollo/core/tools/manager.py` — 当前 `python_code` / `local_rag` 返回格式。

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `SkillSpec.parameters`：直接作为参数校验来源。
- `SkillRegistry.get(name)`：dispatcher 用它判断 unknown skill。
- `SkillRegistry.require(name)`：可用于内部强制查询，但用户输入路径建议返回结构化 `ToolError`。

### Established Patterns

- 旧 projection 中多个工具标签会标记 invalid，因此新 `<tool_call>` parser 也先保持单工具调用约束。
- 旧 `env.py` 中 `local_rag` 需要 JSON 参数，Phase 3 的统一 JSON 调用可以更早发现 `arguments` 格式错误。
- 旧工具返回通常包含 `text_result` 和 `score`，Phase 3 的 `ToolResult` 要考虑兼容这些字段。

### Integration Points

- Phase 3 的 parser 和 dispatcher 后续会被 Phase 4 的 `env.py` 使用。
- Phase 5 prompt 自动生成会告诉模型按照 Phase 3 的 `<tool_call>` 格式输出。
- Phase 6 回归会检查结构化调用没有破坏旧工具语义。

</code_context>

<specifics>
## Specific Ideas

- 当前采用保守默认：一个 action 只允许一个 `<tool_call>`，避免训练时多工具并发带来的复杂度。
- JSON 格式只接受 `name` 和 `arguments` 的核心协议，不把旧 `<python_code>` / `<local_rag>` 兼容逻辑混进 Phase 3。
- 单元测试不应依赖真实 RAG 服务。

</specifics>

<deferred>
## Deferred Ideas

- 旧标签到新 `<tool_call>` 的兼容桥接留到 Phase 4。
- Prompt 自动告诉模型如何写 `<tool_call>` 留到 Phase 5。
- 多 tool call / parallel tool calls 暂不做，可作为未来扩展。

</deferred>

---

*Phase: 3-B3 结构化 Tool Call、参数校验与 Dispatcher*
*Context gathered: 2026-05-22*
