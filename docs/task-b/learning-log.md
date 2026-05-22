# Task B Learning Log: Function Call to Skill

> 这是一份给实现者看的学习与实现记录。目标不是写得漂亮，而是确保每一块 AI 辅助生成的代码你都能解释清楚。

## 0. 我现在要完成什么

Task B 的目标是把 AlphaApollo 当前的工具调用方式从：

```text
模型输出 <python_code>...</python_code>
-> projection.py 用正则解析
-> env.py 用 if/elif 路由具体工具
-> manager.py 执行工具函数
-> <tool_response> 返回模型
```

升级为：

```text
每个工具是一个 skill 目录，里面有 SKILL.md
-> 启动时扫描并注册 skill
-> 模型输出统一结构化 <tool_call>{...}</tool_call>
-> dispatcher 根据 registry 路由执行
-> <tool_response> 返回模型
```

一句话：**把硬编码工具系统改成可发现、可校验、可扩展的 Skill 系统。**

## 1. AI 协作规则

每次让 AI 写代码前，先要求它说明：

1. 这次要改哪些文件。
2. 每个文件承担什么职责。
3. 这次改动如何保持旧行为不坏。
4. 改完后用什么最小测试验证。

每次 AI 写完代码后，我必须能回答：

1. 新增的入口函数在哪里？
2. 调用链从模型输出到工具执行怎么走？
3. 如果输入格式错了，错误在哪里被捕获？
4. 如果面试官问“为什么这样设计”，我怎么解释？

如果答不上来，先不要继续写下一块。

## 2. 关键词小词典

**Skill**：一个工具插件目录，不只是一个 Python 函数。核心文件是 `SKILL.md`，里面声明工具名字、描述、参数 schema、入口和示例。

**Frontmatter**：Markdown 文件开头的 YAML 区块，通常长这样：

```yaml
---
name: python_code
description: Execute Python code.
---
```

**Schema**：参数规则。比如 `code` 必须存在，并且类型必须是 `string`。

**Registry**：注册表，像一本工具字典。通过 skill name 找到对应的 SkillSpec。

**Dispatcher**：通用执行器。它不关心具体工具名，只根据 registry 找到 skill，然后执行入口。

**Structured tool call**：结构化工具调用。目标格式类似：

```xml
<tool_call>
{"name": "python_code", "arguments": {"code": "print(1 + 1)"}}
</tool_call>
```

**Backward compatibility**：向后兼容。迁移成 skill 后，原来的 `python_code` 和 `local_rag` 行为不能明显变坏。

## 3. Task B 拆解

### B1. SKILL.md 规范设计与解析

我要完成：

- 设计 skill 目录结构。
- 设计 `SKILL.md` frontmatter 字段。
- 实现 parser，能读取 YAML frontmatter。
- 实现字段校验，缺字段时返回结构化错误。
- 写一份 `SKILL.md` 编写说明。

暂定输出文件：

```text
alphaapollo/core/skills/schema.py
alphaapollo/core/skills/loader.py
docs/skills.md
```

### B2. Skill 加载器与注册表

我要完成：

- 扫描 skill 目录。
- 加载所有合法 `SKILL.md`。
- 注册到 registry。
- 用 `env.skills=[python_code, local_rag]` 这类配置控制启用工具。

暂定输出文件：

```text
alphaapollo/core/skills/registry.py
alphaapollo/core/skills/builtin/python_code/SKILL.md
alphaapollo/core/skills/builtin/local_rag/SKILL.md
```

### B3. 结构化调用协议与通用 Dispatcher

我要完成：

- 解析统一 `<tool_call>{...}</tool_call>`。
- 校验 JSON 里是否有 `name` 和 `arguments`。
- 按 `SKILL.md` 参数 schema 校验 arguments。
- 用 dispatcher 执行对应 skill。
- 工具异常、超时、stderr、非零退出码都要返回结构化错误，不让环境崩溃。

暂定输出文件：

```text
alphaapollo/core/skills/call_parser.py
alphaapollo/core/skills/dispatcher.py
```

### B4. Prompt 自动生成

我要完成：

- 从 registry 的 skill 元信息生成工具说明。
- prompt 不再手写每个工具的说明。
- 新增 / 移除 skill 时，prompt 自动变化。

可能涉及：

```text
alphaapollo/core/environments/prompts/informal_math_training.py
alphaapollo/core/environments/env_manager.py
```

### B6. 向后兼容与回归

我要完成：

- 迁移 `python_code` 和 `local_rag`。
- 小样例验证两个工具行为不变。
- MATH-500 子集回归，和 Task A baseline 对比，指标误差不超过 3%。

## 4. 当前已理解的旧调用链

旧链路：

```text
rollout_loop.py
  text_actions = tokenizer.batch_decode(...)
  envs.step(text_actions)

env_manager.py
  actions, valids = projection_f(text_actions)
  self.envs.step(actions, text_actions)

projection.py
  从模型输出中抽取 <python_code> / <local_rag> / <answer>
  标记 action 是否 valid

env.py
  _parse_action(...)
  if tool_name == "python_code": ...
  elif tool_name == "local_rag": ...
  包装 <tool_response>

manager.py
  InformalMathToolGroup.python_code(...)
  InformalMathToolGroup.local_rag(...)
```

我要改的是中间的“解析与路由工具”部分，不是 PPO trainer 本身。

## 5. 每一步完成后的自测问题

### B1 自测

- 如果 `SKILL.md` 缺少 `name`，parser 返回什么？
- 如果参数 schema 写错，错误信息长什么样？
- `SkillSpec` 里有哪些字段？每个字段后面谁会用？

### B2 自测

- registry 是在哪里创建的？
- 它扫描哪个目录？
- 如果两个 skill 重名怎么办？
- 如果配置启用了不存在的 skill，系统怎么反馈？

### B3 自测

- `<tool_call>` 里的 JSON 坏了，会在哪里报错？
- 参数缺失时，错误会不会回灌给模型？
- dispatcher 里有没有 `if name == "python_code"` 这种硬编码？
- 工具执行超时会不会让 rollout 崩溃？

### B4 自测

- prompt 工具说明来自哪里？
- 新增一个 skill 后，需要改 prompt 模板吗？
- 模型看到的调用格式示例是什么？

### B6 自测

- `python_code` 迁移前后输出格式是否一致？
- `local_rag` 没启用或服务不可用时，错误反馈是否清楚？
- MATH-500 回归指标是否在 3% 以内？

## 6. 改动记录模板

每完成一个小改动，在这里追加记录。

### Change 001: 初始化学习记录

- 日期：2026-05-22
- 改动：新增 Task B 学习记录，当前路径为 `docs/task-b/learning-log.md`
- 我理解的目的：把 Task B 的技术目标、实施步骤和自测问题记录下来，避免只会运行 AI 写出的代码但讲不清楚。
- 还不懂的问题：
  - `SKILL.md` schema 具体字段怎么设计最合适。
  - dispatcher 如何同时支持 Python function 和脚本入口。
  - 新结构如何最小侵入地接进当前 `env.py`。

### Change 002: 建立 Task B 文档目录

- 日期：2026-05-22
- 改动：新增 `docs/task-b/README.md`，并把学习记录移动到 `docs/task-b/learning-log.md`
- 我理解的目的：把 Task B 相关的个人文档集中存放，后续可以分开记录设计、实验、面试复习和学习日志。
- 还不懂的问题：
  - 代码实现文档和最终 README 应该如何分工。
  - 实验结果应该记录到 `experiments.md` 还是主 README。

### Change 003: 初始化 GSD 项目规划

- 日期：2026-05-22
- 改动：新增 `.planning/config.json`、`.planning/PROJECT.md`、`.planning/REQUIREMENTS.md`、`.planning/ROADMAP.md`、`.planning/STATE.md`
- 我理解的目的：用 GSD 的方式把 Task B 从“大而模糊的重构”拆成 6 个可执行阶段，并把每个阶段映射到可检查 requirements。
- 重要说明：当前环境没有 `gsd-sdk` 命令，所以这次是按 GSD 文档结构手工初始化，而不是由 GSD SDK 自动生成。
- 还不懂的问题：
  - Phase 1 的 `SkillSpec` 字段最终怎么定。
  - `env.skills` 如何最小侵入地接入现有 config。
  - 回归实验的 baseline 应该先跑全量还是先跑子集。

## 7. 下一步

下一步先做 Phase 1 / B1，不写复杂执行逻辑，只设计和解析 `SKILL.md`：

```text
目标：能读一个 skill 的 SKILL.md，并得到 SkillSpec 或结构化错误。
```

完成 B1 后，再进入 registry 和 dispatcher。
