# Phase 4: 迁移 Env Tool 执行路径与内置 Skill - Context

**Gathered:** 2026-05-22
**Status:** Ready for planning

<domain>
## Phase Boundary

本阶段负责把前面已经完成的 skill registry、structured parser、argument validator 和 dispatcher 接入 environment side，让环境能够真正执行：

```xml
<tool_call>
{"name":"python_code","arguments":{"code":"print(1 + 1)"}}
</tool_call>
```

并返回：

```xml
<tool_response>...</tool_response>
```

本阶段的核心是“运行时迁移”，不是继续新增抽象。

本阶段包含：

- 在 env 侧支持 structured `<tool_call>`。
- 保留旧 `<python_code>` / `<local_rag>` 标签兼容路径。
- 让 `python_code` / `local_rag` 的 skill entrypoint 保持旧 `text_result` + `score` 语义。
- 将 dispatcher 结果包装成 `<tool_response>`。
- 将 `env.skills` 和旧 `enable_python_code` / `enable_local_rag` 的兼容策略接入运行时。
- 先以 `informal_math_training` 为主线接入，再评估 `informal_math_evolving` 是否同步。

本阶段不包含：

- 不做 prompt 自动生成；prompt 留到 Phase 5。
- 不跑 MATH-500 全量回归；小样例和局部测试先行。
- 不新增 bonus skill / MCP。

</domain>

<decisions>
## Implementation Decisions

### 接入范围

- **D-01:** Phase 4 的主接入目标是 `informal_math_training`，因为 Task B 的当前配置主线是 `rl_informal_math_tool.yaml -> env.env_name=informal_math_training`。
- **D-02:** `informal_math_evolving` 也有相似的旧工具路径，但先不和 training 同时大改；本阶段 context 记录它的差异，后续可同步迁移。
- **D-03:** 如果实现时发现可以抽出 shared helper，优先提取小的 env-side helper，避免 training/evolving 各写一套完全重复逻辑。

### 旧格式兼容

- **D-04:** 过渡期必须保留旧标签：
  - `<python_code>...</python_code>`
  - `<local_rag>...</local_rag>`
  - `<informalmath_verify>...</informalmath_verify>`
- **D-05:** 新 `<tool_call>` 路径应优先支持，但不能让旧 prompt 或旧 trajectory 立刻失效。
- **D-06:** 旧标签可以在 env 内部被转换成 `ToolCall`，再走 dispatcher；但转换逻辑要小而清楚。

### 内置 skill entrypoint 兼容

- **D-07:** 当前 `SKILL.md` 中的 entrypoint 指向底层函数，只适合作为元数据占位；Phase 4 需要确认或新增 wrapper，以保持旧 `InformalMathToolGroup` 的返回语义。
- **D-08:** `python_code` 的返回必须继续包含：
  - `text_result`
  - `score`
  - disabled / empty code / timeout / stderr 等结构化反馈
- **D-09:** `local_rag` 的返回必须继续包含：
  - `text_result`
  - `score`
  - disabled / 缺 repo_name 或 query / RAG 服务错误等结构化反馈
- **D-10:** 优先复用 `InformalMathToolGroup` 的现有逻辑，避免直接调用底层函数破坏旧行为。

### Dispatcher 与 env 边界

- **D-11:** dispatcher 继续保持通用，不直接知道 env 的 `question`、`ground_truth`、`data_source`。
- **D-12:** env 负责：
  - 解析当前 action 是否为 answer / report / tool call
  - 调用 dispatcher 或旧兼容桥
  - 包装 `<tool_response>`
  - 写入 chat history
  - 生成 metadata
- **D-13:** dispatcher 错误也要作为 `<tool_response>` 回给模型，而不是抛异常打断 rollout。

### env.skills 运行时接入

- **D-14:** Phase 4 需要让 env 构造时真正使用 `resolve_enabled_skill_names(...)`。
- **D-15:** 如果 `env.skills` 不存在，继续从旧 `enable_python_code` / `enable_local_rag` 推导，保持旧配置可用。
- **D-16:** 如果某个 enabled skill 不存在，应尽早形成清晰错误，不能训练到工具调用时才静默失败。

### the agent's Discretion

- 具体是否创建 `alphaapollo/core/environments/informal_math_training/skill_bridge.py` 或通用 helper，由实现时决定。
- 可以先只写小样例测试，不急着跑 MATH-500。
- 可以暂时不迁移 `informalmath_verify` 为 `SKILL.md`，因为 Task B 主线要求是 `python_code` 和 `local_rag`；但旧 verifier 标签不能被破坏。

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Planning

- `.planning/PROJECT.md` — Task B 总目标、兼容性约束和学习记录要求。
- `.planning/REQUIREMENTS.md` — COMPAT-01 到 COMPAT-04，以及 REG-04/REG-05/CALL-05/CALL-06 的剩余运行时要求。
- `.planning/ROADMAP.md` — Phase 4 scope 和 success criteria。
- `.planning/STATE.md` — 当前阶段状态和风险记录。

### Skill Infrastructure

- `alphaapollo/core/skills/call_parser.py` — structured `<tool_call>` parser。
- `alphaapollo/core/skills/validation.py` — arguments schema validator。
- `alphaapollo/core/skills/dispatcher.py` — generic dispatcher。
- `alphaapollo/core/skills/registry.py` — skill registry 和 enabled skill helper。
- `alphaapollo/core/skills/builtin/python_code/SKILL.md` — 当前 python_code skill metadata。
- `alphaapollo/core/skills/builtin/local_rag/SKILL.md` — 当前 local_rag skill metadata。

### Current Env Paths

- `alphaapollo/core/environments/informal_math_training/env.py` — Phase 4 主迁移目标；当前包含旧标签解析和 `if tool_name == ...` 执行分支。
- `alphaapollo/core/environments/informal_math_training/projection.py` — 旧 projection 规则；需要决定是否识别 `<tool_call>`。
- `alphaapollo/core/environments/informal_math_evolving/env.py` — 相似旧路径；用户当前打开，需记录差异并评估同步方案。
- `alphaapollo/core/environments/informal_math_evolving/projection.py` — evolving 旧 projection。
- `alphaapollo/core/environments/env_manager.py` — prompt 构建和 env 创建位置，`env.skills` 运行时接入可能涉及这里。
- `alphaapollo/core/tools/manager.py` — 旧 `InformalMathToolGroup` 的真实行为，保持兼容时必须对照。

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `InformalMathToolGroup.python_code(...)` 已经处理 disabled、空代码、timeout/失败、`text_result` 和 `score`。
- `InformalMathToolGroup.local_rag(...)` 已经处理 disabled、缺参数、RAG 配置和失败格式。
- `BaseTextEnv._execute_tool(...)` 和 env 自己的 `_execute_tool(...)` 已经能把旧 tool group 输出包装成 `<tool_response>`。

### Established Patterns

- training env 当前在 `_parse_action(...)` 中解析旧标签，`step(...)` 中硬编码 `if tool_name == ...`。
- evolving env 当前也在 `_parse_action(...)` 中解析旧标签，但 termination 逻辑和 local_rag JSON fallback 与 training 不同。
- env_manager 的 prompt 构建仍然使用 `enable_python_code` / `enable_local_rag`，Phase 5 才做 prompt 自动生成。

### Integration Points

- Phase 4 可以先让 env 能执行 `<tool_call>`，即使 prompt 还没自动生成。
- Phase 5 再让 prompt 主动告诉模型输出 `<tool_call>`。
- Phase 6 再做 MATH-500 回归。

</code_context>

<specifics>
## Specific Ideas

- 用户当前打开的是 `informal_math_evolving/env.py`，说明这条路径不能完全忽略。
- 但 mini-project 当前 config 主线是 `informal_math_training`，先接 training 更稳。
- Phase 4 的第一步应该是写 plan，而不是直接改 env。

</specifics>

<deferred>
## Deferred Ideas

- Prompt 自动生成留到 Phase 5。
- MATH-500 baseline / skill 版本回归留到 Phase 6。
- Bonus 新 skill / MCP 留到 Task D。

</deferred>

---

*Phase: 4-Env Tool Path Migration*
*Context gathered: 2026-05-22*
