# Phase 6: 回归、Trajectory 样例与 README - Context

**Gathered:** 2026-05-22
**Status:** Ready for planning

<domain>
## Phase Boundary

本阶段负责 Task B6 和 Task C 的交付整理：

- 保存至少一个 structured `<tool_call>` + `<tool_response>` trajectory 样例。
- 整理 Task A baseline / Task B skill 版本回归计划和实验记录。
- 更新 README，让别人能理解改动并知道如何复现。
- 检查 Git 提交记录是否是多次有意义 commit。

本阶段不继续改核心工具链，除非发现文档/回归需要的小 bug。

</domain>

<decisions>
## Implementation Decisions

- **D-01:** 先保存 smoke trajectory，满足 COMPAT-06 的最小证据。
- **D-02:** MATH-500 全量或 ≥100 题抽样回归需要模型服务和较长运行时间，本阶段先写清楚命令、记录当前未运行状态，等待用户确认资源后执行。
- **D-03:** README 只新增 Task B 专区，不重写原项目 README 全部内容。
- **D-04:** 所有 Task B 相关说明继续使用中文。

</decisions>

<canonical_refs>
## Canonical References

- `MiniProject_AlphaApollo_FunctionCall_to_Skill.md` — Task B6 / Task C 交付要求。
- `.planning/REQUIREMENTS.md` — COMPAT-05 / COMPAT-06 / DOC-01~DOC-04。
- `docs/task-b/phase-1-skill-md-spec.md` 到 `docs/task-b/phase-5-prompt.md` — 已完成阶段说明。
- `examples/configs/rl_informal_math_tool.yaml` — 当前 Task B 主线训练配置。
- `README.md` — 需要新增 Task B 专区。

</canonical_refs>

<code_context>
## Existing Evidence

已经用本地 `alphaapollo` 环境生成 smoke trajectory：

```text
prompt 自动生成 <tool_call> 示例
assistant 输出 structured <tool_call>
env 返回 <tool_response>
metadata.tool_call_format = structured
```

该样例会保存到：

```text
docs/task-b/trajectories/structured-python-code-smoke.md
```

</code_context>

<deferred>
## Deferred / Needs User Resources

- Task A baseline MATH-500 指标。
- Task B skill 版本 MATH-500 指标。
- 若要真实跑 ≥100 题或全量 500 题，需要确认模型、GPU、RAG 服务和运行时间。

</deferred>

---

*Phase: 6-Regression Docs*
*Context gathered: 2026-05-22*
