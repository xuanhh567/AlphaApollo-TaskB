# Phase 5：Prompt 自动生成设计

> 当前文档解释 Task B4：为什么 prompt 也要从 `SKILL.md` 自动生成，以及下一步准备怎么做。

## 1. 现在的问题

现在 `informal_math_training` 的 prompt 里，工具说明还是手写的。

大概是这样：

```text
1) <python_code>...</python_code>
2) <local_rag>...</local_rag>
```

这会带来一个问题：

```text
即使工具已经有 SKILL.md，
prompt 还是不知道自动读取它；
新增工具时，仍然要手动改 prompt。
```

这和 Task B 的目标不完全一致。

## 2. Phase 5 要做什么

Phase 5 要把 prompt 变成：

```text
SkillRegistry
-> SkillSpec 列表
-> prompt renderer
-> 模型看到的工具说明
```

通俗说：

```text
SKILL.md 是工具说明书；
prompt renderer 是把说明书翻译给模型看的老师。
```

## 3. 新 prompt 应该教模型什么

新 prompt 应该明确告诉模型：

```xml
<tool_call>{"name":"python_code","arguments":{"code":"print(1 + 1)"}}</tool_call>
```

而不是继续主推：

```xml
<python_code>print(1 + 1)</python_code>
```

旧标签仍然由 env bridge 兼容，但新 prompt 应该鼓励结构化调用。

## 4. prompt renderer 从哪里取信息

它应该只依赖 `SkillSpec`：

```text
SkillSpec.name
SkillSpec.description
SkillSpec.parameters
SkillSpec.examples
```

不要依赖原始 YAML dict。

原因和前面一样：

```text
SkillSpec 是更稳定的内部契约；
后续 registry / dispatcher / prompt 都应该围绕 SkillSpec 工作。
```

## 5. 预期效果

完成后：

```text
新增 skill 目录
-> registry 扫描到它
-> prompt 自动出现这个工具说明
-> dispatcher 能按 name 路由
```

这样才真正接近 Task B 里说的：

```text
新增 / 移除 skill 时，prompt 自动更新，与手写零耦合。
```

## 6. 下一步实现

准备新增：

```text
alphaapollo/core/skills/prompt.py
tests/test_skill_prompt_renderer.py
```

然后修改：

```text
alphaapollo/core/environments/prompts/informal_math_training.py
alphaapollo/core/environments/env_manager.py
```

先从小测试开始，不直接跑训练。
