# Phase 5: Prompt 自动生成 - Context

**Gathered:** 2026-05-22
**Status:** Ready for planning

<domain>
## Phase Boundary

本阶段负责完成 Task B4：让 prompt 里的工具说明由 registry 中的 `SKILL.md` 元信息自动生成。

当前旧 prompt 的问题是：

```text
工具说明写死在 alphaapollo/core/environments/prompts/informal_math_training.py
```

例如：

```text
1) <python_code>...</python_code>
2) <local_rag>...</local_rag>
```

这和 Task B 的目标冲突：

```text
新增 / 移除 skill 时，不应该再手改 prompt 文本。
```

本阶段要做：

- 从 `SkillSpec` 生成工具说明。
- prompt 明确要求模型使用统一 `<tool_call>{...}</tool_call>` 格式。
- examples 来自 `SKILL.md` 的 `examples` 字段。
- `informal_math_training` 的 prompt 构建接入自动生成工具说明。
- 保留 answer 格式和 history 格式，不改 rollout / reward。

本阶段不做：

- 不迁移 `informal_math_evolving`。
- 不跑 MATH-500 全量回归。
- 不新增 bonus skill。
- 不改 `env.py` 工具执行链路。

</domain>

<decisions>
## Implementation Decisions

### Prompt 格式

- **D-01:** 新 prompt 统一告诉模型使用 `<tool_call>{...}</tool_call>` 调用工具。
- **D-02:** 每次只能输出一个 tool call 或一个 answer，不能同时输出多个动作。
- **D-03:** answer 仍然使用 `<answer>...</answer>`，不要在 Phase 5 改 reward/answer 逻辑。
- **D-04:** 工具 JSON 最小结构保持 Phase 3 格式：

```json
{"name": "python_code", "arguments": {"code": "print(1 + 1)"}}
```

### Prompt 来源

- **D-05:** 工具说明必须来自 `SkillSpec.name`、`description`、`parameters`、`examples`。
- **D-06:** prompt renderer 不应该读取原始 YAML dict；它应该只依赖 `SkillSpec`。
- **D-07:** enabled skill 列表继续使用 Phase 2/4 的 `resolve_enabled_skill_names(...)`。

### 兼容与风险

- **D-08:** 旧标签兼容留在 env bridge 中，prompt 可以优先教新 `<tool_call>`。
- **D-09:** 如果没有启用任何 skill，prompt 应该退回 no-tool prompt，只允许 `<answer>`。
- **D-10:** 如果 prompt 自动生成出现问题，必须能通过小测试发现，不等训练时才发现。

</decisions>

<canonical_refs>
## Canonical References

### Requirements

- `MiniProject_AlphaApollo_FunctionCall_to_Skill.md` — B4 prompt 自动生成要求。
- `.planning/REQUIREMENTS.md` — PROMPT-01 / PROMPT-02 / PROMPT-03。
- `.planning/ROADMAP.md` — Phase 5 scope。

### Existing Prompt Path

- `alphaapollo/core/environments/prompts/informal_math_training.py` — 当前手写 prompt。
- `alphaapollo/core/environments/env_manager.py` — `build_text_obs(...)` 调用 `get_policy_training_prompt(...)` 的位置。

### Skill Metadata

- `alphaapollo/core/skills/schema.py` — `SkillSpec` / `SkillParameter` / `SkillExample`。
- `alphaapollo/core/skills/registry.py` — built-in skill 加载与 enabled skill 解析。
- `alphaapollo/core/skills/builtin/python_code/SKILL.md` — python_code prompt 信息来源。
- `alphaapollo/core/skills/builtin/local_rag/SKILL.md` — local_rag prompt 信息来源。

### Runtime Path Already Completed

- `alphaapollo/core/skills/dispatcher.py` — structured dispatcher。
- `alphaapollo/core/environments/informal_math_training/skill_bridge.py` — 新旧 tool call bridge。
- `alphaapollo/core/environments/informal_math_training/env.py` — structured tool call runtime。

</canonical_refs>

<code_context>
## Existing Code Insights

当前 `get_policy_training_prompt(...)` 根据两个 bool 分支返回不同模板：

```text
enable_python_code
enable_local_rag
```

这会导致：

```text
工具越多，模板分支越多；
每个工具说明都要手写；
examples 也要手写；
新增 skill 仍然要改 prompt 核心代码。
```

Phase 5 应该把工具说明抽成类似：

```python
render_tool_instructions(specs: list[SkillSpec]) -> str
```

再把它插入基础 prompt 模板。

</code_context>

<specifics>
## Specific Ideas

推荐新增：

```text
alphaapollo/core/skills/prompt.py
tests/test_skill_prompt_renderer.py
docs/task-b/phase-5-prompt.md
```

推荐函数：

```python
render_tool_call_schema(spec: SkillSpec) -> dict
render_skill_prompt_block(specs: list[SkillSpec]) -> str
```

训练 prompt 可以变成：

```text
You may call exactly one tool using:
<tool_call>{"name":"...","arguments":{...}}</tool_call>

Available tools:
{tool_instructions}

Or answer using:
<answer>...</answer>
```

</specifics>

<deferred>
## Deferred Ideas

- `informal_math_evolving` prompt 同步留到后续。
- Prompt A/B 指标回归留到 Phase 6。
- 新增 bonus skill 留到 Task D。

</deferred>

---

*Phase: 5-Prompt Auto Generation*
*Context gathered: 2026-05-22*
