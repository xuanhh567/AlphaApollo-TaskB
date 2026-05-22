# Phase 1 Context: B1 - SKILL.md 规范与解析器

## 背景

Task B 要把 AlphaApollo 的工具系统从硬编码文本标签调用升级为目录化、自描述、可动态发现的 Skill 系统。Phase 1 只负责 B1：设计 `SKILL.md` 规范，并实现 parser 前的设计准备。

## 当前旧系统

旧调用链大致为：

```text
模型输出 <python_code>...</python_code>
-> projection.py 正则抽取标签
-> env.py 根据 tool_name 写 if/elif
-> manager.py 调用具体工具函数
-> <tool_response> 返回模型
```

旧系统的问题：

- 工具名写死在多个文件里。
- 参数格式由标签体自由文本承担，校验弱。
- prompt 工具说明手写，新增工具时容易漏改。
- 新工具需要改 parser、router、prompt 和配置。

## Phase 1 目标

Phase 1 只做“工具说明书”的设计：

```text
定义每个 skill 目录必须有什么
定义 SKILL.md frontmatter 字段
定义 parser 应返回什么
定义错误如何结构化表达
写中文说明，保证用户能理解
```

## 不在本阶段做的事

- 不接入 `env.py`
- 不实现 dispatcher
- 不执行 Python function
- 不迁移 prompt
- 不跑 MATH-500 回归

## 已确定的设计方向

每个 skill 是一个目录：

```text
alphaapollo/core/skills/builtin/<skill_name>/
  SKILL.md
```

`SKILL.md` 使用 YAML frontmatter，至少包含：

- `name`
- `description`
- `parameters`
- `entrypoint`
- `timeout`
- `examples`

## 关键学习目标

用户需要能解释：

- Skill 为什么不是普通函数。
- frontmatter 是什么。
- schema 为什么能减少模型调用错误。
- parser 为什么应该返回结构化错误。
- B1 与 B2/B3 的边界是什么。

## 参考文件

- `MiniProject_AlphaApollo_FunctionCall_to_Skill.md`
- `docs/task-b/design.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `alphaapollo/core/environments/informal_math_training/env.py`
- `alphaapollo/core/environments/informal_math_training/projection.py`
- `alphaapollo/core/tools/manager.py`
