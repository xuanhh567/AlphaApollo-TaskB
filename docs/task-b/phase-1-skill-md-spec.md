# Task B 设计说明：SKILL.md 规范

> 当前文档只设计 Phase 1 / B1，不写实现代码。目标是让你先理解“为什么需要这些字段”，再进入 parser 实现。

## 1. 先用一句话理解 Skill

在 Task B 里，一个 **Skill** 不是一个普通 Python 函数，而是一个“工具插件文件夹”。

它至少长这样：

```text
alphaapollo/core/skills/builtin/python_code/
  SKILL.md
```

以后可以带脚本或资源：

```text
alphaapollo/core/skills/builtin/python_code/
  SKILL.md
  run.py
  resources/
```

`SKILL.md` 的作用是告诉框架：

```text
这个工具叫什么
能做什么
需要哪些参数
怎么执行
模型应该怎么调用
```

这就像给每个工具发一张“身份证 + 使用说明书”。

## 2. 为什么不能只保留 Python 函数

现在 AlphaApollo 的工具更像这样：

```text
代码里知道有 python_code
代码里知道有 local_rag
env.py 里用 if/elif 判断工具名
prompt 里手写工具说明
```

问题是：新增一个工具时，要同时改很多地方。

Skill 化之后，目标变成：

```text
新增一个工具目录
写一个 SKILL.md
registry 自动发现
prompt 自动生成说明
dispatcher 自动路由执行
```

核心收益是：**新增工具时尽量不改框架核心代码**。

## 3. SKILL.md 文件结构

建议 `SKILL.md` 使用 Markdown + YAML frontmatter。

frontmatter 是文件开头 `---` 和 `---` 中间的 YAML：

```markdown
---
name: python_code
description: Execute Python code for math reasoning.
parameters:
  - name: code
    type: string
    required: true
    description: Python code to execute.
entrypoint:
  type: python_function
  path: alphaapollo.core.tools.python_code:execute_python_code
timeout: 30
examples:
  - name: compute arithmetic
    arguments:
      code: "print(1 + 1)"
---

# Python Code

Run short Python snippets and return stdout/stderr/status.
```

程序只需要解析 frontmatter；正文 Markdown 主要给人看。

## 4. Phase 1 先支持哪些字段

Phase 1 只做规范和解析，不执行工具。字段先保持够用，不追求一次设计到完美。

### 4.1 `name`

示例：

```yaml
name: python_code
```

含义：skill 的唯一名字。

后续谁会用：

- registry 用它做字典 key。
- 模型 tool call 里会写 `"name": "python_code"`。
- dispatcher 用它找到对应 skill。

约束：

- 必填。
- 必须是字符串。
- 建议只允许小写字母、数字、下划线，例如 `python_code`、`local_rag`。

为什么重要：

```text
没有 name，registry 不知道怎么注册它；
name 不稳定，模型调用和 dispatcher 都会找不到工具。
```

### 4.2 `description`

示例：

```yaml
description: Execute Python code for math reasoning.
```

含义：一句话说明 skill 能做什么。

后续谁会用：

- prompt 自动生成时展示给模型。
- 人类开发者看 registry 时快速理解工具。

约束：

- 必填。
- 必须是非空字符串。

为什么重要：

```text
模型需要知道什么时候该用这个工具；
新人也需要知道这个 skill 的用途。
```

### 4.3 `parameters`

示例：

```yaml
parameters:
  - name: code
    type: string
    required: true
    description: Python code to execute.
```

含义：声明这个 skill 接收哪些参数。

后续谁会用：

- schema validator 用它检查模型传参是否正确。
- prompt 自动生成时把参数说明展示给模型。

建议 Phase 1 支持的基础类型：

```text
string
integer
number
boolean
object
array
```

参数字段：

| 字段 | 必填 | 含义 |
|---|---:|---|
| `name` | 是 | 参数名，比如 `code` |
| `type` | 是 | 参数类型，比如 `string` |
| `required` | 是 | 是否必需 |
| `description` | 是 | 参数说明 |
| `default` | 否 | 可选默认值，比如 `top_k: 3` |

为什么重要：

```text
旧版 <local_rag>...</local_rag> 里塞自由文本，json.loads 错了才知道；
新版可以在执行前明确告诉模型：缺 query、top_k 类型错、repo_name 不是 string。
```

### 4.4 `entrypoint`

示例：

```yaml
entrypoint:
  type: python_function
  path: alphaapollo.core.tools.python_code:execute_python_code
```

含义：声明这个 skill 真正怎么执行。

后续谁会用：

- dispatcher 根据 entrypoint 找到执行入口。

Phase 1 只解析，不执行；但字段要先设计好。

建议先支持：

```text
python_function
```

以后可扩展：

```text
script
subprocess
mcp_tool
```

约束：

- `entrypoint.type` 必填。
- `entrypoint.path` 必填。
- `type=python_function` 时，`path` 推荐格式为 `module.path:function_name`。

为什么重要：

```text
Skill 不是只给模型看的说明，它最终还要能被 dispatcher 执行。
entrypoint 就是“执行地址”。
```

### 4.5 `timeout`

示例：

```yaml
timeout: 30
```

含义：这个 skill 最多执行多少秒。

后续谁会用：

- dispatcher 或具体 executor 用它控制执行超时。

约束：

- 可选。
- 如果出现，必须是正整数。
- 如果不写，可以由 dispatcher 使用默认值。

为什么重要：

```text
工具不能无限运行，否则 rollout 会卡死。
python_code 尤其需要 timeout。
```

### 4.6 `examples`

示例：

```yaml
examples:
  - name: compute arithmetic
    arguments:
      code: "print(1 + 1)"
```

含义：给模型和人看的调用示例。

后续谁会用：

- prompt 自动生成时展示 tool_call 示例。
- 文档中帮助新人理解参数怎么填。

约束：

- 必填，至少一个示例。
- 每个 example 至少要有 `arguments`。

为什么重要：

```text
模型只看 schema 有时不够，example 能显著降低格式错误。
```

## 5. 推荐的最小规范

Phase 1 的 `SKILL.md` frontmatter 最小可用格式：

```yaml
---
name: skill_name
description: One sentence description.
parameters:
  - name: arg_name
    type: string
    required: true
    description: What this argument means.
entrypoint:
  type: python_function
  path: package.module:function_name
timeout: 30
examples:
  - name: short example
    arguments:
      arg_name: example value
---
```

## 6. Python Code Skill 示例

```yaml
---
name: python_code
description: Execute Python code for math reasoning and return stdout, stderr, return code, and status.
parameters:
  - name: code
    type: string
    required: true
    description: Python code to execute.
entrypoint:
  type: python_function
  path: alphaapollo.core.tools.python_code:execute_python_code
timeout: 30
examples:
  - name: compute arithmetic
    arguments:
      code: "print(1 + 1)"
---
```

模型未来调用时会变成：

```xml
<tool_call>
{"name":"python_code","arguments":{"code":"print(1 + 1)"}}
</tool_call>
```

## 7. Local RAG Skill 示例

```yaml
---
name: local_rag
description: Retrieve documentation snippets from local math and scientific Python package knowledge bases.
parameters:
  - name: repo_name
    type: string
    required: true
    description: Repository name, such as sympy, scipy, numpy, math, cmath, fractions, or itertools.
  - name: query
    type: string
    required: true
    description: Natural-language retrieval query.
  - name: top_k
    type: integer
    required: false
    default: 3
    description: Number of retrieved chunks per query.
entrypoint:
  type: python_function
  path: alphaapollo.core.tools.rag.local_rag:local_rag_retrieve
timeout: 60
examples:
  - name: query sympy solving
    arguments:
      repo_name: sympy
      query: How to solve polynomial equations with sympy?
      top_k: 3
---
```

模型未来调用时会变成：

```xml
<tool_call>
{"name":"local_rag","arguments":{"repo_name":"sympy","query":"How to solve polynomial equations with sympy?","top_k":3}}
</tool_call>
```

## 8. Parser 应该返回什么

Phase 1 的 parser 不执行工具，只做：

```text
读 SKILL.md
-> 找 frontmatter
-> YAML 解析
-> 字段校验
-> 返回 SkillSpec 或结构化错误
```

建议成功返回：

```python
SkillLoadResult(
    ok=True,
    spec=SkillSpec(...),
    errors=[],
)
```

失败返回：

```python
SkillLoadResult(
    ok=False,
    spec=None,
    errors=[
        SkillLoadError(
            code="missing_required_field",
            message="Missing required field: name",
            path="SKILL.md",
            field="name",
        )
    ],
)
```

为什么不用直接 `raise Exception`：

```text
启动时扫描很多 skills，如果一个坏了，最好能告诉用户哪个坏、哪里坏；
不要让整个系统只留下一个很难读的 traceback。
```

## 9. 新手理解版：这些字段像什么

可以把 `SKILL.md` 想成一张工具登记表：

| 字段 | 类比 |
|---|---|
| `name` | 工具身份证号码 |
| `description` | 工具一句话介绍 |
| `parameters` | 使用工具前要填的表单 |
| `entrypoint` | 真正去哪里执行 |
| `timeout` | 最多等多久 |
| `examples` | 给模型看的范例答案 |

## 10. Phase 1 不做什么

Phase 1 暂时不做：

- 不接入 `env.py`
- 不执行工具
- 不改 prompt
- 不跑 MATH-500
- 不迁移 `python_code` / `local_rag` 的真实调用路径

这样做是为了把基础打稳：先确认“工具说明书”能被正确读懂。

## 11. 自测问题

读完这份设计后，你应该能回答：

1. 为什么 `name` 是必填？
2. `parameters` 后面会给谁用？
3. `entrypoint` 和 `examples` 有什么区别？
4. 为什么 parser 出错时不应该直接崩溃？
5. `python_code` 和 `local_rag` 的 `SKILL.md` 最大区别在哪里？

## 12. Parser 实现计划

这一节只规划 parser 怎么写，不直接实现。

Parser 的职责是：

```text
输入：某个 skill 目录里的 SKILL.md
输出：SkillSpec 或结构化错误
```

它不负责：

- 不执行工具
- 不创建 registry
- 不生成 prompt
- 不校验模型的 tool_call arguments

这些是后续 Phase 2 / Phase 3 / Phase 5 的事情。

### 12.1 要新增的文件

Phase 1 建议新增：

```text
alphaapollo/core/skills/__init__.py
alphaapollo/core/skills/schema.py
alphaapollo/core/skills/loader.py
```

如果要加最小测试，可以新增：

```text
tests/test_skill_loader.py
```

如果这个仓库当前没有标准 tests 目录，也可以先用：

```text
alphaapollo/core/skills/examples/
```

或临时脚本验证，但正式交付最好有 pytest 测试。

### 12.2 `schema.py` 负责什么

`schema.py` 只放“数据结构”，不读文件。

建议先用 `dataclass`，因为它简单、容易解释。

建议结构：

```python
SkillParameter
SkillEntrypoint
SkillExample
SkillSpec
SkillLoadError
SkillLoadResult
```

每个类的意义：

| 类名 | 作用 |
|---|---|
| `SkillParameter` | 描述一个参数，例如 `code`、`repo_name`、`query` |
| `SkillEntrypoint` | 描述工具执行入口，例如 `python_function` + `module:function` |
| `SkillExample` | 描述一个示例调用，主要保存 `arguments` |
| `SkillSpec` | 一个完整 skill 的解析结果 |
| `SkillLoadError` | 一个结构化错误 |
| `SkillLoadResult` | parser 的总返回结果，包含 `ok/spec/errors` |

为什么先定义这些：

```text
loader.py 读出来的是 dict；
后续 registry/dispatcher/prompt 不应该直接依赖原始 dict；
SkillSpec 是更稳定的内部契约。
```

### 12.3 `loader.py` 负责什么

`loader.py` 负责把 `SKILL.md` 变成 `SkillLoadResult`。

建议暴露一个主函数：

```python
load_skill_from_dir(skill_dir: Path | str) -> SkillLoadResult
```

未来 registry 可以这样用：

```python
result = load_skill_from_dir(path)
if result.ok:
    registry.register(result.spec)
else:
    log errors
```

也可以有一个辅助函数：

```python
load_skill_file(skill_file: Path | str) -> SkillLoadResult
```

这样测试时可以直接传某个 `SKILL.md` 文件。

### 12.4 Parser 的步骤

建议 `load_skill_file(...)` 按 6 步写。

#### Step 1: 检查文件是否存在

输入是：

```text
.../python_code/SKILL.md
```

如果文件不存在，返回：

```text
ok=False
error code = skill_file_not_found
```

不要抛未处理异常。

#### Step 2: 提取 YAML frontmatter

合法文件应该以 `---` 开始，并有第二个 `---` 结束 frontmatter。

例如：

```markdown
---
name: python_code
description: Execute Python code.
---

# Python Code
```

如果没有 frontmatter，返回：

```text
error code = missing_frontmatter
```

如果只有开头 `---`，没有结束 `---`，返回：

```text
error code = unterminated_frontmatter
```

#### Step 3: YAML 解析

把 frontmatter 字符串交给 YAML parser。

如果 YAML 语法错误，返回：

```text
error code = invalid_yaml
```

注意：这一步只是把 YAML 变成 Python dict，还没有判断字段对不对。

#### Step 4: 顶层字段校验

至少检查：

```text
name
description
parameters
entrypoint
examples
```

`timeout` 可以可选。

常见错误：

| 错误 | code |
|---|---|
| 缺少 `name` | `missing_required_field` |
| `name` 不是字符串 | `invalid_field_type` |
| `parameters` 不是 list | `invalid_field_type` |
| `entrypoint` 不是 dict | `invalid_field_type` |
| `examples` 是空列表 | `invalid_field_value` |

#### Step 5: 嵌套字段校验

校验 `parameters` 里的每一项：

```text
name: string
type: string
required: boolean
description: string
default: optional
```

校验 `entrypoint`：

```text
type: string
path: string
```

Phase 1 先只允许：

```text
entrypoint.type = python_function
```

并检查 path 像不像：

```text
module.path:function_name
```

也就是里面要有一个冒号 `:`。

校验 `examples`：

```text
每个 example 必须有 arguments
arguments 必须是 dict/object
```

#### Step 6: 构造 `SkillSpec`

所有校验通过后，把原始 dict 转成：

```text
SkillSpec
```

并把 `source_path` 记录进去，方便后续报错和调试。

### 12.5 错误结构设计

建议错误长这样：

```python
SkillLoadError(
    code="missing_required_field",
    message="Missing required field: name",
    path="/.../SKILL.md",
    field="name",
)
```

为什么要有 `code`：

```text
测试可以稳定断言 code；
message 可以以后改成中文或英文；
程序逻辑不应该依赖一整段 message 文本。
```

为什么要有 `field`：

```text
用户可以快速知道是 name 错了，还是 parameters 错了。
```

### 12.6 最小测试用例

Phase 1 至少准备 5 个 case。

#### Case 1: 合法 python_code

输入：合法 `SKILL.md`

期望：

```text
ok=True
spec.name == "python_code"
spec.parameters[0].name == "code"
```

#### Case 2: 缺少 name

输入：没有 `name`

期望：

```text
ok=False
errors[0].code == "missing_required_field"
errors[0].field == "name"
```

#### Case 3: parameters 不是 list

错误示例：

```yaml
parameters:
  code:
    type: string
```

期望：

```text
ok=False
error code = invalid_field_type
field = parameters
```

#### Case 4: entrypoint.path 缺少冒号

错误示例：

```yaml
entrypoint:
  type: python_function
  path: alphaapollo.core.tools.python_code.execute_python_code
```

期望：

```text
ok=False
field = entrypoint.path
```

#### Case 5: examples 缺少 arguments

错误示例：

```yaml
examples:
  - name: bad example
```

期望：

```text
ok=False
field = examples[0].arguments
```

### 12.7 先不支持的复杂功能

Phase 1 暂时不支持：

- `enum`
- 嵌套 object schema
- array item schema
- 多 entrypoint
- script/subprocess 执行
- MCP 工具描述
- 自动扫描目录

原因：

```text
B1 的重点是建立稳定、可解释的最小规范；
复杂 schema 和执行方式可以在基础跑通后再加。
```

### 12.8 实现顺序建议

真正写代码时，按这个顺序：

1. 写 `schema.py` dataclass。
2. 写 frontmatter 提取函数。
3. 写 YAML parse 包装。
4. 写顶层字段校验。
5. 写 parameters / entrypoint / examples 校验。
6. 写 dict -> SkillSpec 转换。
7. 写 5 个最小测试。
8. 更新学习日志。

### 12.9 完成后你要能解释

写完 parser 后，你应该能回答：

1. 为什么 `SkillLoadResult` 里要有 `ok`？
2. 为什么错误要有 `code`，不只写 message？
3. 为什么 `SkillSpec` 要记录 `source_path`？
4. 为什么 Phase 1 不直接执行 `entrypoint`？
5. 如果 `parameters` 写成 dict 而不是 list，parser 会怎么返回？
