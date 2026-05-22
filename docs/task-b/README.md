# Task B 文档目录

这个目录用于存放 Task B 的个人学习记录、分阶段设计、实现笔记和实验记录。

## 推荐阅读顺序

1. `learning-log.md`：边学边写的主记录，记录每一步为什么改、改了什么、是否真的理解。
2. `design.md`：Task B 总体设计地图，只看大关系，不陷入细节。
3. `phase-1-skill-md-spec.md`：Phase 1 详细文档，解释 `SKILL.md` 规范和 parser。
4. 后续每开始一个阶段，再新增对应 phase 文档。

## 当前文档状态

| 文件 | 用途 |
|---|---|
| `README.md` | 当前目录入口 |
| `learning-log.md` | 学习记录和每次改动记录 |
| `design.md` | Task B 总体设计地图 |
| `phase-1-skill-md-spec.md` | Phase 1：`SKILL.md` 规范和 parser |
| `phase-2-registry.md` | Phase 2：registry、启用配置和内置 skill 设计 |
| `phase-3-tool-call.md` | Phase 3：结构化 `<tool_call>`、参数校验和 dispatcher 设计 |
| `phase-4-env-integration.md` | Phase 4：把 dispatcher 接入 env，并保持旧工具行为兼容 |
| `phase-5-prompt.md` | Phase 5：从 registry / `SKILL.md` 自动生成 prompt 工具说明 |
| `experiments.md` | Task B 实验记录、smoke trajectory 和 MATH-500 回归状态 |
| `trajectories/structured-python-code-smoke.md` | 结构化 `<tool_call>` 到 `<tool_response>` 的最小样例 |

## 写文档的原则

- 不把所有内容集中到一个超大的 Markdown 文件里。
- 每个 phase 文档只解释当前阶段要解决的问题。
- 学习日志记录“我今天理解了什么”，phase 文档记录“这个阶段最终怎么设计”。
- 每开始一个新 phase，先创建对应阶段文档，再写代码。
