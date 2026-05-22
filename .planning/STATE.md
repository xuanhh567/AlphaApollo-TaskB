# State: AlphaApollo Task B Skill Refactor

**Last Updated:** 2026-05-22
**Current Focus:** Phase 1 - B1 SKILL.md 规范与解析器

## Project Reference

See: `.planning/PROJECT.md`

**Core value:** 在不破坏 MATH-500 agentic reasoning 回归指标的前提下，让 AlphaApollo 的工具系统从“写死标签 + if 分支”变成“可插拔 Skill + 通用 dispatcher”。

## Current Status

- GSD 标准规划目录已初始化。
- 因当前环境缺少 `gsd-sdk` 命令，使用 Codex inline fallback 创建 `.planning/` 文档。
- 用户要求所有相关文档使用中文。
- 已创建个人学习记录目录：`docs/task-b/`
- GitHub 私有仓库已创建：`xuanhh567/AlphaApollo-TaskB`

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

开始 Phase 1：

1. 讨论并确定 `SKILL.md` frontmatter 字段。
2. 设计 `SkillSpec` / `SkillParameter` 数据结构。
3. 实现最小 parser，先只做到“读文件 + 校验 + 返回结构化结果”。
4. 写中文 skill 编写说明。

## Risks

- 用户刚接触 RL/tool/skill 体系，过快实现会导致面试时讲不清。
- 直接替换 env 工具路径风险较高，需要先做兼容桥接。
- MATH-500 全量回归耗时较长，阶段内需要先用小样例和子集验证。
- `local_rag` 依赖外部服务，回归时可能受服务状态影响。

---
*State initialized: 2026-05-22*
