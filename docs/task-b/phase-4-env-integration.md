# Phase 4：Env Tool 执行路径迁移设计

> 当前文档只设计 Phase 4。目标是让你理解：前面做好的 parser / registry / dispatcher，怎么真正接到 AlphaApollo 的 environment side。

## 1. Phase 4 要解决什么

前面已经完成：

```text
SKILL.md -> SkillSpec
SkillSpec -> SkillRegistry
<tool_call> -> ToolCall
ToolCall + registry -> ToolResult
```

但这些还只是独立模块。

Phase 4 要做的是：

```text
env.py 收到模型输出
-> 识别是 answer 还是 tool call
-> 如果是 <tool_call>，交给 dispatcher
-> dispatcher 返回 ToolResult
-> env.py 包成 <tool_response>
-> 加回 chat_history
```

通俗讲：

```text
前面造好了发动机；
Phase 4 要把发动机装回车里。
```

## 2. 为什么不能直接把旧逻辑删掉

旧模型 / 旧 prompt 还可能输出：

```xml
<python_code>print(1 + 1)</python_code>
```

或者：

```xml
<local_rag>{"repo_name":"sympy","query":"..."}</local_rag>
```

如果直接删掉旧标签支持，可能导致：

```text
旧 prompt 失效
旧 trajectory 失效
回归指标突然下降
```

所以 Phase 4 应该先做“双轨兼容”：

```text
新格式 <tool_call> 支持
旧格式 <python_code>/<local_rag> 暂时保留
```

等 Phase 5 prompt 自动生成稳定后，再逐步减少旧格式依赖。

## 3. 先接哪个 env

当前有两套相似环境：

```text
informal_math_training
informal_math_evolving
```

Task B 当前主线配置是：

```yaml
env.env_name=informal_math_training
```

所以 Phase 4 建议：

```text
先接 informal_math_training
再评估 informal_math_evolving 是否同步
```

原因：

```text
training 是当前任务主线；
evolving 也重要，但细节不同；
一次改两套 env 容易把问题混在一起。
```

## 4. 旧工具行为必须保持

这是最容易走偏的地方。

旧 `python_code` 不是单纯执行一个底层函数，它还会处理：

- 是否启用 python code
- 空代码
- timeout
- stdout / stderr
- returncode
- score
- JSON 格式的 `text_result`

旧 `local_rag` 也不是单纯调用底层检索函数，它还会处理：

- 是否启用 local RAG
- repo_name / query 是否存在
- rag_cfg
- RAG 服务错误
- score
- JSON 格式的 `text_result`

所以 Phase 4 不应该简单地说：

```text
entrypoint 指到底层函数就完事
```

更稳的做法是：

```text
用 wrapper 或复用 InformalMathToolGroup，
保持旧 text_result + score 语义。
```

## 5. env 和 dispatcher 的分工

dispatcher 负责：

```text
找到 skill
校验参数
执行 entrypoint
返回 ToolResult
```

env.py 负责：

```text
维护 chat_history
判断 done
计算 reward
包装 <tool_response>
生成 metadata
兼容旧标签
```

不要把 env 的状态塞进 dispatcher。

## 6. Phase 4 的推荐实现顺序

1. 先写 Phase 4 plan。
2. 给 `python_code` / `local_rag` 准备兼容 wrapper。
3. 调整内置 `SKILL.md` 的 `entrypoint.path` 指向 wrapper。
4. 让 `informal_math_training/env.py` 支持 `<tool_call>`。
5. 保留旧标签路径，并尽量转成统一 `ToolCall` 处理。
6. 把 `ToolResult` 包装成 `<tool_response>`。
7. 写小样例测试，验证新旧格式都能跑。
8. 再决定是否同步 `informal_math_evolving`。

## 7. 自测问题

写完 Phase 4 后，你应该能回答：

1. 为什么 Phase 4 不能直接删掉旧标签？
2. 为什么 `python_code` 不能简单直接调用底层 `execute_python_code`？
3. dispatcher 和 env.py 的职责边界是什么？
4. `<tool_call>` 成功执行后，如何变成 `<tool_response>`？
5. `env.skills` 和旧 `enable_python_code` 的运行时关系是什么？
6. `informal_math_training` 和 `informal_math_evolving` 的迁移顺序是什么？
