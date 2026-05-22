# Phase 2：Skill Registry 设计说明

> 当前文档只设计 Phase 2 / B2。目标是让你先理解 registry 是什么、为什么需要它、它和 loader 有什么区别，然后再写代码。

## 1. 先用一句话理解 Registry

Phase 1 的 loader 解决的是：

```text
读一个 SKILL.md
-> 得到一个 SkillSpec
```

Phase 2 的 registry 解决的是：

```text
读很多 skill 目录
-> 得到很多 SkillSpec
-> 按 name 注册起来
-> 后续可以查询、过滤、生成 prompt、交给 dispatcher
```

新手类比：

```text
loader = 读懂一张工具说明书
registry = 管理一整个工具目录
```

## 2. 为什么不能只有 loader

如果只有 loader，系统只能做到：

```python
result = load_skill_from_dir("python_code")
```

但是真实训练时，框架需要知道：

- 当前有哪些工具可用？
- 哪些工具被配置启用了？
- 模型调用 `python_code` 时，对应哪个 `SkillSpec`？
- 如果用户配置了不存在的工具，应该怎么报错？
- 如果两个 skill 都叫 `python_code`，应该怎么办？

这些都不是单个 loader 的职责，而是 registry 的职责。

## 3. Phase 2 的边界

Phase 2 做：

- 新增 `registry.py`。
- 扫描 skill 目录。
- 注册合法 `SkillSpec`。
- 支持按名字查询 skill。
- 支持列出已注册 skill。
- 创建内置 `python_code` / `local_rag` 的 `SKILL.md`。
- 设计 `env.skills` 新配置。
- 兼容旧配置 `enable_python_code` / `enable_local_rag`。

Phase 2 不做：

- 不解析 `<tool_call>`。
- 不执行 `entrypoint`。
- 不接入 `env.py` 的工具执行路径。
- 不生成最终 prompt。
- 不跑 MATH-500。

这样拆是为了让你先讲清楚：

```text
SkillSpec 是怎么被收集和管理的。
```

## 4. 推荐的 Registry 最小能力

建议 registry 至少支持四类操作。

### 4.1 `register(spec)`

含义：注册一个合法的 `SkillSpec`。

如果 registry 里还没有这个名字：

```text
注册成功
```

如果已经有同名 skill：

```text
返回 duplicate_skill 错误
```

为什么不能静默覆盖：

```text
如果两个目录都声明 name: python_code，
静默覆盖会让用户不知道最后生效的是哪一个。
```

### 4.2 `get(name)`

含义：按名字获取一个 skill。

示例：

```python
registry.get("python_code")
```

后续谁会用：

- dispatcher：模型调用某个工具时，需要通过 name 找到 `SkillSpec`。
- prompt renderer：生成工具说明时，需要读取每个 skill 的元信息。

### 4.3 `list()`

含义：列出当前注册的所有 skill。

示例结果：

```text
python_code
local_rag
```

后续谁会用：

- prompt 自动生成。
- 调试输出。
- 测试确认启用工具是否正确。

### 4.4 `load_from_dirs(paths)`

含义：扫描多个 skill 目录，并把合法 skill 注册进 registry。

示例：

```text
alphaapollo/core/skills/builtin/python_code/
alphaapollo/core/skills/builtin/local_rag/
```

它内部应该复用 Phase 1 的：

```python
load_skill_from_dir(...)
```

不要在 registry 里重新写 YAML 解析逻辑。

## 5. 错误策略：收集错误，继续扫描

本阶段决定采用：

```text
某个 SKILL.md 坏了，不立刻让整个扫描崩溃；
合法 skill 继续注册；
所有错误统一返回。
```

例子：

```text
python_code/SKILL.md 合法 -> 注册成功
local_rag/SKILL.md 缺 name -> 记录错误
calculator/SKILL.md 合法 -> 注册成功
```

最后结果应该能表达：

```text
注册成功：python_code, calculator
错误：local_rag 缺少 name
```

为什么这样更好：

```text
开发时一次能看到多个问题；
不会因为一个坏 skill 阻止所有合法 skill 被检查；
也不会像静默跳过那样隐藏错误。
```

## 6. 新配置：`env.skills`

旧配置是：

```yaml
env.informal_math.enable_python_code=true
env.informal_math.enable_local_rag=false
```

它的问题是：

```text
每新增一个工具，就要新增一个 enable_xxx 配置。
```

Skill 化以后，更自然的配置是：

```yaml
env.skills:
  - python_code
  - local_rag
```

含义：

```text
这次训练只启用这些 skill。
```

后续如果新增 `calculator`，只需要：

```yaml
env.skills:
  - python_code
  - local_rag
  - calculator
```

而不是继续加：

```yaml
enable_calculator=true
```

## 7. 旧配置兼容策略

Phase 2 决定：

```text
如果新配置 env.skills 存在，优先用 env.skills。
如果 env.skills 不存在，就从旧配置推导。
```

推导规则：

| 旧配置 | 推导出的 skill |
|---|---|
| `enable_python_code=true` | `python_code` |
| `enable_local_rag=true` | `local_rag` |

例子：

```yaml
enable_python_code: true
enable_local_rag: false
```

推导结果：

```text
enabled skills = ["python_code"]
```

为什么要兼容：

```text
现有配置文件还在用 enable_python_code / enable_local_rag；
如果直接删除旧配置，训练脚本可能立刻坏掉。
```

## 8. 内置 Skill 目录

Phase 2 建议创建：

```text
alphaapollo/core/skills/builtin/
  python_code/
    SKILL.md
  local_rag/
    SKILL.md
```

注意：

```text
Phase 2 只让 registry 能发现它们；
不在 Phase 2 执行它们。
```

真实执行留到 Phase 3 / Phase 4：

```text
Phase 3: dispatcher 知道怎么执行 entrypoint
Phase 4: env.py 改用 dispatcher
```

## 9. Phase 2 自测问题

写完 Phase 2 后，你应该能回答：

1. loader 和 registry 的区别是什么？
2. 为什么 registry 不能直接保存原始 dict？
3. 如果两个 skill 都叫 `python_code`，应该返回什么错误？
4. 如果配置启用了不存在的 skill，应该在哪里发现？
5. `env.skills` 和旧的 `enable_python_code` 有什么关系？
6. 为什么 Phase 2 先不改 `env.py`？

## 10. 实现前计划

正式写代码前，建议按这个顺序：

1. 定义 registry 的返回结果和错误结构。
2. 实现 `SkillRegistry.register(...)`。
3. 实现 `SkillRegistry.get(...)` 和 `SkillRegistry.list(...)`。
4. 实现扫描目录并调用 `load_skill_from_dir(...)`。
5. 实现 enabled skills 过滤。
6. 实现旧配置到 `env.skills` 的推导函数。
7. 创建内置 `python_code` / `local_rag` 的 `SKILL.md`。
8. 写 registry 测试。
9. 更新学习日志。

## 11. 实际实现内容

Phase 2 实现后，新增了：

```text
alphaapollo/core/skills/registry.py
alphaapollo/core/skills/builtin/python_code/SKILL.md
alphaapollo/core/skills/builtin/local_rag/SKILL.md
tests/test_skill_registry.py
```

### 11.1 `SkillRegistry`

`SkillRegistry` 是一个很薄的注册表，内部核心是：

```text
dict[str, SkillSpec]
```

也就是说：

```text
key = skill name
value = 已经校验过的 SkillSpec
```

它提供：

```python
register(spec)
get(name)
require(name)
names()
specs()
```

其中 `register(spec)` 会检查重名。如果已经有同名 skill，它返回：

```text
duplicate_skill
```

不会静默覆盖。

### 11.2 `SkillRegistryLoadResult`

扫描多个 skill 目录时，返回的是：

```text
SkillRegistryLoadResult
```

它包含：

```text
registry: 注册好的 SkillRegistry
loaded: 成功注册的 skill name 列表
errors: 扫描或注册过程中收集到的错误
```

新手理解：

```text
registry 是结果本体；
loaded 告诉你哪些成功了；
errors 告诉你哪些失败了。
```

### 11.3 `load_skill_registry_from_dirs(...)`

这个函数负责：

```text
多个目录
-> 每个目录调用 load_skill_from_dir(...)
-> 合法的注册进 registry
-> 错误收集起来
```

它没有重新解析 YAML，而是复用 Phase 1 的 loader。

这点很重要：

```text
loader 管解析；
registry 管组织；
两个职责不混在一起。
```

### 11.4 `get_builtin_skill_dirs()`

这个函数扫描：

```text
alphaapollo/core/skills/builtin/*/SKILL.md
```

当前能发现：

```text
python_code
local_rag
```

Phase 2 只发现和加载它们，不执行它们。

### 11.5 `resolve_enabled_skill_names(...)`

这个函数把配置转成启用 skill 名字列表。

优先使用新配置：

```yaml
env:
  skills:
    - local_rag
```

如果新配置不存在，则从旧配置推导：

```yaml
env:
  informal_math:
    enable_python_code: true
    enable_local_rag: false
```

推导结果：

```text
["python_code"]
```

## 12. 验证方式

当前通过了：

```bash
python tests/test_skill_loader.py
python tests/test_skill_registry.py
python -m py_compile alphaapollo/core/skills/schema.py alphaapollo/core/skills/loader.py alphaapollo/core/skills/registry.py tests/test_skill_loader.py tests/test_skill_registry.py
```

测试覆盖：

1. 注册后可以按 name 查询。
2. 同名 skill 返回 `duplicate_skill`。
3. 扫描多个目录时，坏 `SKILL.md` 的错误会被收集，其他合法 skill 继续注册。
4. `enabled_skills` 能过滤只启用的 skill。
5. 配置启用了不存在的 skill 时返回 `unknown_enabled_skill`。
6. 内置 skill 目录能发现并加载 `python_code` 和 `local_rag`。

## 13. 防走偏说明

这里要特别区分两件事：

```text
registry 基础模块完成
```

不等于：

```text
AlphaApollo 训练流程已经完全使用 env.skills
```

当前已经完成的是：

- 能扫描 skill 目录。
- 能注册和查询 `SkillSpec`。
- 能解析 `env.skills` 或旧配置，得到启用 skill 名字列表。
- 能发现内置 `python_code` / `local_rag` 的 `SKILL.md`。

但还没有完成的是：

- `env_manager.py` / `env.py` 启动时真正使用 `env.skills`。
- 旧的 `enable_python_code` / `enable_local_rag` 在运行时完全切换到新 registry。
- `python_code` / `local_rag` 的 skill entrypoint 保证返回和旧工具一样的 `text_result` + `score`。

所以更准确的说法是：

```text
Phase 2 registry module complete；
runtime integration pending。
```

运行时接入会在 Phase 4 处理。
