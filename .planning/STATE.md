# State: AlphaApollo Task B Skill Refactor

**Last Updated:** 2026-05-22
**Current Focus:** Phase 4 - Env tool path migration in progress

## Project Reference

See: `.planning/PROJECT.md`

**Core value:** 在不破坏 MATH-500 agentic reasoning 回归指标的前提下，让 AlphaApollo 的工具系统从“写死标签 + if 分支”变成“可插拔 Skill + 通用 dispatcher”。

## Current Status

- GSD 标准规划目录已初始化。
- 因当前环境缺少 `gsd-sdk` 命令，使用 Codex inline fallback 创建 `.planning/` 文档。
- 用户要求所有相关文档使用中文。
- 已创建个人学习记录目录：`docs/task-b/`
- GitHub 私有仓库已创建：`xuanhh567/AlphaApollo-TaskB`
- Phase 1 已完成：`SKILL.md` 规范、`SkillSpec` 数据结构、loader/parser、结构化错误和基础测试均已实现。
- Phase 2 context 已记录：决定采用 `Registry + 配置` 范围、扫描错误收集策略，并在 Phase 2 创建 `python_code` / `local_rag` 的 `SKILL.md`。
- Phase 2 registry 基础模块已完成：registry、内置 skill metadata、启用配置解析 helper 和 registry 测试均已实现。
- Phase 2 尚未完全满足运行时要求：`env.skills` 还没有接入 env 创建流程；旧 `enable_python_code` / `enable_local_rag` 的运行时兼容需要 Phase 4 处理。
- Phase 3 context 已记录：采用统一 `<tool_call>` JSON 结构、单 tool call 约束、`SkillSpec.parameters` 参数校验和独立 dispatcher 测试边界。
- Phase 3 plan 已创建：`.planning/phases/03-structured-tool-call/03-01-PLAN.md`。
- Phase 3 独立模块已完成：`call_parser.py`、`validation.py`、`dispatcher.py` 和对应测试已实现。尚未接入 `env.py`。
- Phase 4 context 已记录：先迁移 `informal_math_training`，保留旧标签兼容，记录 `informal_math_evolving` 相似路径并后续评估同步。
- Phase 4 plan 已创建：`.planning/phases/04-env-tool-path/04-01-PLAN.md`。下一步开始实现 env bridge / runtime 接入。
- Phase 4 第一小步已实现：`informal_math_training/skill_bridge.py` 支持 structured `<tool_call>` 与旧标签桥接，training env 已能执行 structured `python_code`。

## Important Local Context

- 当前 Git remote:
  - `origin`: `https://github.com/xuanhh567/AlphaApollo-TaskB.git`
  - `upstream`: `https://github.com/tmlr-group/AlphaApollo.git`
- 当前未提交内容包括：
  - `.planning/`
  - `.codex/skills/learning-opportunities/resources/orientation.md`
  - `MiniProject_AlphaApollo_FunctionCall_to_Skill.md`
  - `docs/task-b/`

## Working Agreements

- 每个阶段先讲清楚需求，再写代码。
- 每次 AI 写代码前，要说明会改哪些文件、为什么改、如何验证。
- 每个阶段完成后，在 `docs/task-b/learning-log.md` 追加 change record。
- 保持小步 commit，不做一次性大提交。
- 优先让用户能解释代码，而不是只追求速度。

## Next Action

开始 Phase 4 实现：

1. 验证 structured / legacy `local_rag` 路径。
2. 补齐 `local_rag` 相关小样例测试。
3. 评估是否同步 `informal_math_evolving`。
4. 再进入 Phase 5 prompt 自动生成。

## Scope Correction Notes

- 不要把“registry 模块可用”说成“B2 运行时完全完成”。
- 当前 `python_code` / `local_rag` 的 `SKILL.md` entrypoint 只是元数据占位；Phase 4 需要确认 wrapper 或入口函数能保持旧 `text_result` + `score` 语义。

## Risks

- 用户刚接触 RL/tool/skill 体系，过快实现会导致面试时讲不清。
- 直接替换 env 工具路径风险较高，需要先做兼容桥接。
- MATH-500 全量回归耗时较长，阶段内需要先用小样例和子集验证。
- `local_rag` 依赖外部服务，回归时可能受服务状态影响。

---
*State initialized: 2026-05-22*
*Last updated: 2026-05-22 after Phase 1 completion*
