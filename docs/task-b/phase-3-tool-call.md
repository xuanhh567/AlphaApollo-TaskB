# Phase 3：结构化 Tool Call 与 Dispatcher 设计说明

> 当前文档只设计 Phase 3 / B3。目标是让你理解：模型输出怎么从文本变成一个可执行工具调用，以及为什么要先解析和校验，再执行。

## 1. Phase 3 要解决什么

前两阶段已经完成：

```text
Phase 1: 读懂一个 SKILL.md -> SkillSpec
Phase 2: 管理多个 SkillSpec -> SkillRegistry
```

Phase 3 要解决：

```text
模型输出 <tool_call>{...}</tool_call>
-> 解析成 ToolCall
-> 查 registry 确认工具存在
-> 按 SkillSpec.parameters 校验 arguments
-> dispatcher 执行 entrypoint
-> 得到 ToolResult 或 ToolError
```

新手版：

```text
call_parser = 看懂模型想调用什么
validator = 检查模型传参对不对
dispatcher = 真正去执行这个工具
```

## 2. 新工具调用格式

Phase 3 统一支持：

```xml
<tool_call>
{"name":"python_code","arguments":{"code":"print(1 + 1)"}}
</tool_call>
```

JSON 里最少需要两个字段：

| 字段 | 类型 | 含义 |
|---|---|---|
| `name` | string | 要调用哪个 skill |
| `arguments` | object | 传给 skill 的参数 |

比如 `local_rag`：

```xml
<tool_call>
{"name":"local_rag","arguments":{"repo_name":"sympy","query":"solve polynomial equations","top_k":3}}
</tool_call>
```

## 3. 为什么不用旧标签

旧格式是：

```xml
<python_code>print(1 + 1)</python_code>
```

或者：

```xml
<local_rag>{"repo_name":"sympy","query":"..."}</local_rag>
```

问题是：

```text
每新增一个工具，就要新增一个标签；
每个标签的参数格式都可能不一样；
env.py 容易继续出现 if tool_name == ...
```

新格式的好处：

```text
所有工具都走同一个 <tool_call>；
工具名放在 JSON 的 name 字段；
参数都放在 arguments 字段；
dispatcher 可以通过 registry 通用路由。
```

## 4. Phase 3 的边界

Phase 3 做：

- 解析 `<tool_call>`。
- 检查 JSON。
- 检查 `name` / `arguments`。
- 检查 unknown skill。
- 按 `SkillSpec.parameters` 检查 required 和基础类型。
- 设计 `ToolCall`、`ToolResult`、`ToolError`。
- 实现通用 dispatcher，支持 `python_function` entrypoint。

Phase 3 不做：

- 不替换 `env.py` 旧执行路径。
- 不处理旧 `<python_code>` / `<local_rag>` 兼容桥接。
- 不生成 prompt。
- 不跑 MATH-500。

## 5. Parser 应该检查什么

Parser 负责的是“格式是否像一个工具调用”。

它应该识别这些错误：

| 情况 | 错误 |
|---|---|
| 没有 `<tool_call>` | `missing_tool_call` |
| 只有开标签没有闭标签 | `invalid_tool_call_tag` |
| 出现多个 `<tool_call>` | `multiple_tool_calls` |
| 标签中不是合法 JSON | `invalid_json` |
| JSON 不是 object | `invalid_tool_call_payload` |
| 缺少 `name` | `missing_tool_name` |
| 缺少 `arguments` | `missing_arguments` |
| `arguments` 不是 object | `invalid_arguments_type` |

Parser 成功后，返回类似：

```python
ToolCall(
    name="python_code",
    arguments={"code": "print(1 + 1)"},
)
```

## 6. 参数校验应该检查什么

参数校验负责的是：

```text
模型传的 arguments 是否符合 SKILL.md 里声明的 parameters。
```

例如 `python_code` 的 schema 是：

```yaml
parameters:
  - name: code
    type: string
    required: true
```

如果模型输出：

```json
{"name":"python_code","arguments":{}}
```

就应该返回：

```text
missing_required_argument: code
```

如果模型输出：

```json
{"name":"python_code","arguments":{"code": 123}}
```

就应该返回：

```text
invalid_argument_type: code should be string
```

## 7. Dispatcher 做什么

Dispatcher 的职责是：

```text
ToolCall + Registry
-> 找到 SkillSpec
-> 校验 arguments
-> 根据 entrypoint 执行
-> 返回 ToolResult 或 ToolError
```

它不应该写：

```python
if name == "python_code":
    ...
elif name == "local_rag":
    ...
```

而应该是：

```text
spec = registry.get(tool_call.name)
entrypoint = spec.entrypoint
execute(entrypoint, tool_call.arguments)
```

## 8. 为什么 Phase 3 先不接 env.py

因为 `env.py` 现在还承担很多事情：

- 维护对话历史。
- 判断 done。
- 计算 reward。
- 包装 `<tool_response>`。
- 处理旧工具标签。

如果 Phase 3 直接改 `env.py`，你会同时面对：

```text
解析问题
参数校验问题
工具执行问题
环境状态问题
回归兼容问题
```

所以 Phase 3 先独立测试 parser 和 dispatcher。

等它们稳定后，Phase 4 再接入 `env.py`。

## 9. Phase 3 自测问题

写完 Phase 3 后，你应该能回答：

1. `ToolCall` 是从哪里来的？
2. `ToolCall.name` 怎么变成真正的工具？
3. unknown skill 应该在哪里被发现？
4. required 参数缺失时，为什么不能继续执行工具？
5. dispatcher 为什么不能硬编码 `python_code`？
6. Phase 3 和 Phase 4 的边界是什么？

## 10. 已实现：`call_parser.py`

当前已经新增：

```text
alphaapollo/core/skills/call_parser.py
tests/test_tool_call_parser.py
```

`call_parser.py` 现在提供：

```python
ToolCall
ToolError
parse_tool_call(text)
```

它只负责第一步：

```text
模型文本 -> ToolCall 或 ToolError
```

它不做：

- 不查 registry。
- 不校验参数 schema。
- 不执行工具。
- 不处理旧 `<python_code>` / `<local_rag>` 标签。

当前能识别的错误包括：

```text
missing_tool_call
invalid_tool_call_tag
multiple_tool_calls
invalid_json
invalid_tool_call_payload
missing_tool_name
invalid_tool_name
missing_arguments
invalid_arguments_type
```

验证命令：

```bash
python tests/test_tool_call_parser.py
python tests/test_skill_loader.py
python tests/test_skill_registry.py
python -m py_compile alphaapollo/core/skills/call_parser.py tests/test_tool_call_parser.py alphaapollo/core/skills/__init__.py
```

## 11. 已实现：参数校验 `validation.py`

当前新增：

```text
alphaapollo/core/skills/validation.py
tests/test_skill_argument_validation.py
```

`validation.py` 提供：

```python
validate_arguments(spec, arguments)
```

它做的事情是：

```text
SkillSpec.parameters + ToolCall.arguments
-> normalized_arguments
-> errors
```

也就是：

- 检查 required 参数是否缺失。
- 检查参数类型是否符合 `SKILL.md`。
- 给有 default 的可选参数补默认值。
- 检查模型是否传了 schema 里没有的多余参数。

基础类型对应关系：

| Skill 类型 | Python 类型 |
|---|---|
| `string` | `str` |
| `integer` | `int`，但不能是 `bool` |
| `number` | `int` / `float`，但不能是 `bool` |
| `boolean` | `bool` |
| `object` | `dict` |
| `array` | `list` |

新增错误：

```text
missing_required_argument
invalid_argument_type
unexpected_argument
```

为什么检查多余参数：

```text
如果模型传了 schema 里没有的参数，
后面直接执行 Python 函数时可能出现 unexpected keyword argument；
提前返回 ToolError 更容易让模型修正调用。
```

验证命令：

```bash
python tests/test_skill_argument_validation.py
python tests/test_tool_call_parser.py
python tests/test_skill_loader.py
python tests/test_skill_registry.py
python -m py_compile alphaapollo/core/skills/call_parser.py alphaapollo/core/skills/validation.py alphaapollo/core/skills/__init__.py tests/test_tool_call_parser.py tests/test_skill_argument_validation.py
```
