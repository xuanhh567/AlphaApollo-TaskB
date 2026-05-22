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

### Change 004: 开始 Phase 1，设计 SKILL.md 规范

- 日期：2026-05-22
- 改动：新增 `docs/task-b/design.md`、`.planning/phases/01-skill-md-spec/CONTEXT.md`、`.planning/phases/01-skill-md-spec/01-01-PLAN.md`
- 我理解的目的：先把 Skill 的“说明书格式”讲清楚，只设计 `SKILL.md` 字段和 parser 目标，不急着写实现代码。
- 当前理解：
  - `name` 是 registry 和模型调用使用的唯一工具名。
  - `description` 会进入 prompt，帮助模型判断什么时候使用工具。
  - `parameters` 是未来参数校验和 prompt 自动生成的依据。
  - `entrypoint` 是未来 dispatcher 真正执行 skill 的入口地址。
  - `examples` 是给模型和新人看的调用示例。
- 还不懂的问题：
  - Phase 1 中是否需要支持 `enum` 这类更细 schema。
  - `entrypoint.type` 除了 `python_function`，是否要现在就设计 `script`。
  - examples 是否要强制包含完整 `<tool_call>`，还是只写 arguments 即可。

### Change 005: 写出 parser 实现计划

- 日期：2026-05-22
- 改动：在 `docs/task-b/design.md` 中新增 “Parser 实现计划”，并补充 `.planning/phases/01-skill-md-spec/01-01-PLAN.md` 的 Wave 3。
- 我理解的目的：在写代码前先明确 parser 的边界、数据结构、错误格式、实现步骤和最小测试。
- 当前理解：
  - `schema.py` 放数据结构，不读文件。
  - `loader.py` 负责读取 `SKILL.md`、解析 frontmatter、校验字段、返回 `SkillLoadResult`。
  - parser 只负责把 `SKILL.md` 变成 `SkillSpec` 或结构化错误，不负责执行工具。
  - 测试应该断言错误 `code` 和 `field`，不要依赖完整错误文本。
- 还不懂的问题：
  - 是否应该现在就引入 pytest，还是先用脚本验证。
  - YAML 依赖应该用当前环境已有的 `yaml` / `PyYAML`，还是避免新增依赖。
  - `SkillLoadResult` 是否应该支持多个错误一起返回，还是遇到第一个错误就停止。

### Change 006: 新增 Skill 元数据数据结构

- 日期：2026-05-22
- 改动：新增 `alphaapollo/core/skills/schema.py` 和 `alphaapollo/core/skills/__init__.py`
- 我理解的目的：先定义 parser 成功或失败后要交给后续模块的“标准交接单”，还不读取 `SKILL.md`，也不执行工具。
- 新增的数据结构：
  - `SkillParameter`：描述一个参数，如 `code`、`repo_name`。
  - `SkillEntrypoint`：描述执行入口，如 `python_function` + `module:function`。
  - `SkillExample`：描述一个示例参数 payload，用于文档和 prompt。
  - `SkillSpec`：一个完整合法 skill 的内部表示。
  - `SkillLoadError`：一个结构化解析错误。
  - `SkillLoadResult`：loader 的统一返回包装，包含 `ok/spec/errors`。
- 验证：
  - `python -m py_compile alphaapollo/core/skills/schema.py alphaapollo/core/skills/__init__.py` 通过。
  - 直接导入 `alphaapollo.core.skills` 时，当前 shell 环境缺少 `omegaconf`，会被仓库顶层 `alphaapollo/__init__.py` 提前拦住；这不是本次新增文件语法问题。
  - 使用 `importlib` 绕开顶层包导入后，可以成功构造 `SkillSpec` 和 `SkillLoadResult.success(...)`。
- 还不懂的问题：
  - 是否应该调整仓库顶层 `alphaapollo/__init__.py`，避免导入轻量模块时强依赖 workflow 依赖。
  - `SkillLoadResult.failure(...)` 是否应该允许返回多个错误，后续 parser 如何收集多个错误。

### Change 007: 新增 SKILL.md loader

- 日期：2026-05-22
- 改动：新增 `alphaapollo/core/skills/loader.py`
- 我理解的目的：实现 Phase 1 的核心 parser，把 `SKILL.md` 读取为 `SkillSpec`，或在格式错误时返回结构化 `SkillLoadError`。
- loader 当前做的事情：
  - `load_skill_from_dir(...)`：从 skill 目录读取 `SKILL.md`。
  - `load_skill_file(...)`：读取单个文件。
  - `_extract_frontmatter(...)`：提取 `---` 中间的 YAML frontmatter。
  - `_parse_yaml(...)`：用 `yaml.safe_load` 解析 frontmatter。
  - `_build_skill_spec(...)`：校验字段并构造 `SkillSpec`。
- 当前支持的校验：
  - 必填顶层字段：`name`、`description`、`parameters`、`entrypoint`、`examples`。
  - skill name 只允许小写字母、数字、下划线，并且以小写字母开头。
  - 参数类型支持：`string`、`integer`、`number`、`boolean`、`object`、`array`。
  - `entrypoint.type` 当前只支持 `python_function`。
  - `entrypoint.path` 必须像 `module.path:function_name`。
  - `examples` 每项必须有 `arguments`，且必须是 object。
- 验证：
  - `python -m py_compile alphaapollo/core/skills/schema.py alphaapollo/core/skills/loader.py alphaapollo/core/skills/__init__.py` 通过。
  - 临时样例验证通过：
    - 合法 `python_code` 返回 `ok=True`。
    - 缺 `name` 返回 `missing_required_field/name`。
    - `parameters` 类型错返回 `invalid_field_type/parameters`。
    - `entrypoint.path` 格式错返回 `invalid_entrypoint_path/entrypoint.path`。
    - example 缺 `arguments` 返回 `missing_required_field/examples[0].arguments`。
- 还不懂的问题：
  - 是否需要正式加入 pytest 测试文件，而不是只用临时脚本验证。
  - `loader.py` 是否应该一次收集所有错误，还是保持当前部分错误会提前返回。

### Change 008: 新增 Skill loader 测试

- 日期：2026-05-22
- 改动：新增 `tests/test_skill_loader.py`，并轻量调整 `alphaapollo/__init__.py` 与 `alphaapollo/core/__init__.py` 的导入行为。
- 我理解的目的：把临时验证固化成可重复测试，保护 `loader.py` 后续不被改坏。
- 测试覆盖：
  - 合法 `SKILL.md` 能得到 `SkillSpec`。
  - 缺少 `name` 返回结构化错误。
  - `parameters` 不是 list 返回结构化错误。
  - `entrypoint.path` 不符合 `module:function` 返回结构化错误。
  - example 缺少 `arguments` 返回结构化错误。
  - 缺少 frontmatter 返回结构化错误。
- 导入相关改动：
  - `alphaapollo/__init__.py` 改为懒加载 workflows，避免导入轻量子模块时立刻需要 `omegaconf`。
  - `alphaapollo/core/__init__.py` 增加 `ALPHAAPOLLO_SKIP_VERL_ALIAS=1` 测试开关，默认行为不变；测试中使用该开关避免拉起 verl/pandas 等重依赖。
- 验证：
  - `python tests/test_skill_loader.py` 通过。
  - `python -m py_compile alphaapollo/__init__.py alphaapollo/core/__init__.py alphaapollo/core/skills/schema.py alphaapollo/core/skills/loader.py tests/test_skill_loader.py` 通过。
- 还不懂的问题：
  - 后续是否要安装 pytest 并把 `python tests/test_skill_loader.py` 换成标准 `pytest tests/test_skill_loader.py`。
  - 懒加载 workflows 是否会影响某些依赖 `from alphaapollo import rl` 的旧代码路径，需要后续回归确认。

### Change 009: Phase 1 收尾

- 日期：2026-05-22
- 改动：更新 `.planning/PROJECT.md`、`.planning/REQUIREMENTS.md`、`.planning/ROADMAP.md`、`.planning/STATE.md` 和 Phase 1 PLAN 状态。
- 我理解的目的：把 B1 从计划状态正式标记为完成，并把下一步焦点切换到 Phase 2：registry 与启用配置。
- Phase 1 已完成内容：
  - `SKILL.md` 字段规范设计。
  - `SkillSpec` / `SkillParameter` 等内部数据结构。
  - `loader.py` 解析 frontmatter、YAML 和字段校验。
  - 结构化错误返回。
  - `tests/test_skill_loader.py` 基础测试。
- 下一步：
  - 先设计 registry 的职责，再写 `registry.py`。
  - 创建内置 skill 目录和 `python_code` / `local_rag` 的 `SKILL.md`。

### Change 010: 拆分 Task B 阶段文档

- 日期：2026-05-22
- 改动：把原来的 `docs/task-b/design.md` 拆成总览文档和 `docs/task-b/phase-1-skill-md-spec.md`。
- 我理解的目的：Task B 会越来越大，如果所有解释都写在一个文件里，新手很容易迷路；按阶段拆分后，每个文档只回答当前阶段的问题。
- 当前文档分工：
  - `README.md`：告诉我从哪里开始看。
  - `design.md`：只画 Task B 的总地图。
  - `phase-1-skill-md-spec.md`：详细解释 Phase 1 的 `SKILL.md` 和 parser。
  - `learning-log.md`：记录每天的学习过程和改动。
  - 后续 Phase 2 开始后，再新增 `phase-2-registry.md`。

### Change 011: 开始 Phase 2 registry 设计

- 日期：2026-05-22
- 改动：新增 `.planning/phases/02-skill-registry/02-CONTEXT.md`、`.planning/phases/02-skill-registry/02-DISCUSSION-LOG.md` 和 `docs/task-b/phase-2-registry.md`。
- 我理解的目的：在写 registry 代码前，先明确它的职责、边界、错误策略和配置兼容方式。
- 已确定的 Phase 2 决策：
  - Phase 2 做 `Registry + 配置`，不提前接入 `env.py`。
  - 扫描多个 skill 时采用“收集错误继续”的策略。
  - Phase 2 现在创建 `python_code` / `local_rag` 的 `SKILL.md`，但暂时不执行。
  - 新配置 `env.skills` 优先；没有新配置时，从旧的 `enable_python_code` / `enable_local_rag` 推导。
- 还不懂的问题：
  - registry 返回结果是否应该复用 `SkillLoadResult`，还是新增 `SkillRegistryResult`。
  - 配置推导函数应该放在 `registry.py` 里，还是单独放在 `config.py`。
  - 内置 skill 的 `entrypoint.path` 应该直接指向底层函数，还是先指向 `InformalMathToolGroup` 方法。

### Change 012: 写出 Phase 2 实现计划

- 日期：2026-05-22
- 改动：新增 `.planning/phases/02-skill-registry/02-01-PLAN.md`。
- 我理解的目的：把 Phase 2 的想法变成可执行 wave，后续写代码时按计划推进，不把 registry、配置、内置 skill 和测试混在一起。
- 当前计划拆分：
  - Wave 1：设计 registry 数据结构。
  - Wave 2：实现注册、查询和目录扫描。
  - Wave 3：创建内置 `python_code` / `local_rag` 的 `SKILL.md`。
  - Wave 4：实现 `env.skills` 和旧配置兼容。
  - Wave 5：写 registry 测试。
  - Wave 6：更新中文文档和学习记录。
- 当前理解：
  - loader 负责“读懂单个 SKILL.md”。
  - registry 负责“管理多个 SkillSpec”。
  - dispatcher 负责“执行某个 SkillSpec”，所以不是 Phase 2 的内容。
  - `env.skills` 是更通用的启用工具方式，旧的 `enable_python_code` 只是兼容入口。

### Change 013: 实现 Phase 2 registry 基础能力

- 日期：2026-05-22
- 改动：
  - 新增 `alphaapollo/core/skills/registry.py`
  - 新增 `alphaapollo/core/skills/builtin/python_code/SKILL.md`
  - 新增 `alphaapollo/core/skills/builtin/local_rag/SKILL.md`
  - 新增 `tests/test_skill_registry.py`
  - 更新 `alphaapollo/core/skills/__init__.py`
- 我理解的目的：让系统能从“读一个 skill”前进到“管理多个 skill”，并能按配置选择启用哪些 skill。
- 当前理解：
  - `SkillRegistry` 内部保存 `dict[str, SkillSpec]`。
  - `register(spec)` 负责防止重名 skill 静默覆盖。
  - `load_skill_registry_from_dirs(...)` 负责扫描多个目录，并收集错误继续。
  - `get_builtin_skill_dirs()` 负责发现内置 skill 目录。
  - `resolve_enabled_skill_names(...)` 负责把 `env.skills` 或旧配置转换成 skill name 列表。
- 验证：
  - `python tests/test_skill_loader.py` 通过。
  - `python tests/test_skill_registry.py` 通过。
  - `python -m py_compile alphaapollo/core/skills/schema.py alphaapollo/core/skills/loader.py alphaapollo/core/skills/registry.py tests/test_skill_loader.py tests/test_skill_registry.py` 通过。
- 还不懂的问题：
  - 后续 dispatcher 是否应该使用 `registry.require(name)` 抛错，还是用 `registry.get(name)` 自己构造结构化错误。
  - `entrypoint.path` 现在指向底层函数，Phase 4 迁移时是否需要 wrapper 来保持旧 `InformalMathToolGroup` 的返回格式。

### Change 014: 开始 Phase 3 结构化 tool call 设计

- 日期：2026-05-22
- 改动：
  - 新增 `.planning/phases/03-structured-tool-call/03-CONTEXT.md`
  - 新增 `.planning/phases/03-structured-tool-call/03-DISCUSSION-LOG.md`
  - 新增 `docs/task-b/phase-3-tool-call.md`
- 我理解的目的：在写 parser 和 dispatcher 前，先明确 `<tool_call>` 的格式、参数校验边界和 dispatcher 的职责。
- 当前理解：
  - `call_parser` 负责把模型文本变成 `ToolCall`。
  - 参数校验使用 `SkillSpec.parameters`，不重新发明一套 schema。
  - dispatcher 通过 registry 找 skill，不能硬编码具体工具名。
  - Phase 3 先独立测试，不接 `env.py`。
- 当前保守默认：
  - 一个 action 只允许一个 `<tool_call>`。
  - JSON 必须包含 `name` 和 `arguments`。
  - 旧 `<python_code>` / `<local_rag>` 标签兼容留到 Phase 4。

### Change 015: 修正 Phase 2 完成状态，避免走偏

- 日期：2026-05-22
- 改动：把 Phase 2 从“完全完成”修正为“registry 基础模块完成，运行时接入待完成”。
- 我理解的目的：原始 Task B2 不只是要有 registry 代码，还要求训练启动时由声明式 `env.skills` 驱动。我们目前只完成了 registry 和配置解析 helper，还没接到 `env.py` / `env_manager.py`。
- 当前准确进度：
  - 已完成：`registry.py`、内置 `SKILL.md`、registry 测试、配置解析 helper。
  - 未完成：运行时真正使用 `env.skills`，以及旧 `enable_python_code` / `enable_local_rag` 的 env 兼容切换。
- 重要风险：
  - 当前内置 `SKILL.md` 的 `entrypoint.path` 指向底层函数，但旧工具返回语义来自 `InformalMathToolGroup` 包装；Phase 4 需要 wrapper 或兼容入口来保持 `text_result` + `score` 行为。

### Change 016: 写出 Phase 3 实现计划

- 日期：2026-05-22
- 改动：新增 `.planning/phases/03-structured-tool-call/03-01-PLAN.md`。
- 我理解的目的：把结构化 tool call 从概念拆成可执行步骤，避免一上来就改 `env.py`。
- 当前计划拆分：
  - Wave 1：设计 `ToolCall`、`ToolError`、`ToolResult`。
  - Wave 2：实现 `<tool_call>` parser。
  - Wave 3：按 `SkillSpec.parameters` 做参数校验。
  - Wave 4：实现 dispatcher 和 `python_function` entrypoint。
  - Wave 5：写 parser / dispatcher 测试。
  - Wave 6：更新中文文档。
- 当前理解：
  - parser 只判断模型输出格式。
  - 参数校验判断 `arguments` 是否符合 skill schema。
  - dispatcher 才负责执行。
  - Phase 3 的测试使用 fake entrypoint，不依赖真实 RAG 或 Python 工具执行。

### Change 017: 实现结构化 tool call parser

- 日期：2026-05-22
- 改动：
  - 新增 `alphaapollo/core/skills/call_parser.py`
  - 新增 `tests/test_tool_call_parser.py`
  - 更新 `alphaapollo/core/skills/__init__.py`
- 我理解的目的：先让系统能看懂模型输出的统一 `<tool_call>{...}</tool_call>`，并在格式错误时返回结构化 `ToolError`。
- 当前理解：
  - `ToolCall` 表示模型想调用哪个工具以及传了哪些参数。
  - `ToolError` 表示解析、校验或执行阶段的结构化错误。
  - `parse_tool_call(...)` 只做文本解析和 JSON 结构检查，不执行工具。
- 验证：
  - `python tests/test_tool_call_parser.py` 通过。
  - `python tests/test_skill_loader.py` 通过。
  - `python tests/test_skill_registry.py` 通过。
  - `python -m py_compile alphaapollo/core/skills/call_parser.py tests/test_tool_call_parser.py alphaapollo/core/skills/__init__.py` 通过。
- 还不懂的问题：
  - 参数校验 helper 应该放在 `dispatcher.py` 里，还是单独拆成 `validation.py`。
  - `ToolError` 最终包装进 `<tool_response>` 时应该用 JSON 格式还是纯文本格式。

### Change 018: 实现 Skill 参数校验

- 日期：2026-05-22
- 改动：
  - 新增 `alphaapollo/core/skills/validation.py`
  - 新增 `tests/test_skill_argument_validation.py`
  - 更新 `alphaapollo/core/skills/__init__.py`
- 我理解的目的：在 dispatcher 执行工具之前，先检查模型传给工具的 arguments 是否符合 `SKILL.md` 里声明的参数规则。
- 当前理解：
  - `validate_arguments(spec, arguments)` 输入一个 `SkillSpec` 和一份模型参数。
  - 它会返回补好默认值的 `normalized_arguments`，以及结构化 `ToolError` 列表。
  - 如果有错误，后续 dispatcher 不应该执行工具。
  - `integer` / `number` 要特别排除 `bool`，因为 Python 里 `bool` 是 `int` 的子类。
- 额外规则：
  - 如果模型传了 schema 没声明的参数，返回 `unexpected_argument`，避免执行时才出现 unexpected keyword argument。
- 验证：
  - `python tests/test_skill_argument_validation.py` 通过。
  - `python tests/test_tool_call_parser.py` 通过。
  - `python tests/test_skill_loader.py` 通过。
  - `python tests/test_skill_registry.py` 通过。
  - `python -m py_compile alphaapollo/core/skills/call_parser.py alphaapollo/core/skills/validation.py alphaapollo/core/skills/__init__.py tests/test_tool_call_parser.py tests/test_skill_argument_validation.py` 通过。
- 还不懂的问题：
  - `None` 作为默认值时，当前 `SkillParameter.default=None` 无法区分“没写 default”和“默认值就是 null”，后续如果需要支持 null default，可能要调整 schema。

### Change 019: 实现独立 dispatcher

- 日期：2026-05-22
- 改动：
  - 新增 `alphaapollo/core/skills/dispatcher.py`
  - 新增 `tests/test_skill_dispatcher.py`
  - 新增 `tests/skill_dispatcher_fixtures.py`
  - 更新 `alphaapollo/core/skills/__init__.py`
- 我理解的目的：让系统能从 `ToolCall` 通过 registry 找到对应 skill，校验参数，然后执行 `python_function` entrypoint。
- 当前理解：
  - `dispatch_tool_call(call, registry)` 是 Phase 3 的核心入口。
  - 它不硬编码 `python_code` 或 `local_rag`。
  - 它先查 registry，再调用 `validate_arguments`，最后动态 import `entrypoint.path`。
  - 工具异常会变成 `ToolResult(ok=False, error=ToolError(...))`，不会直接让调用方崩溃。
- 当前限制：
  - 还没有接入 `env.py`。
  - 还没有实现超时隔离。
  - 真实 `python_code` / `local_rag` 的旧返回语义还要 Phase 4 wrapper 处理。
- 验证：
  - `python tests/test_skill_dispatcher.py` 通过。
  - `python tests/test_skill_argument_validation.py` 通过。
  - `python tests/test_tool_call_parser.py` 通过。
  - `python tests/test_skill_registry.py` 通过。
  - `python tests/test_skill_loader.py` 通过。
  - `python -m py_compile ...` 通过。

### Change 020: 开始 Phase 4 env 接入设计

- 日期：2026-05-22
- 改动：
  - 新增 `.planning/phases/04-env-tool-path/04-CONTEXT.md`
  - 新增 `.planning/phases/04-env-tool-path/04-DISCUSSION-LOG.md`
  - 新增 `docs/task-b/phase-4-env-integration.md`
- 我理解的目的：在改 `env.py` 之前，先明确 structured dispatcher 怎么接回 environment side，并避免破坏旧工具行为。
- 当前理解：
  - Phase 4 先接 `informal_math_training`，因为它是当前 Task B 配置主线。
  - `informal_math_evolving` 也有类似旧路径，需要记录并后续评估同步。
  - 旧 `<python_code>` / `<local_rag>` 标签不能直接删。
  - `python_code` / `local_rag` 的 skill entrypoint 需要 wrapper 或复用 `InformalMathToolGroup`，保持旧 `text_result` + `score`。
- 还不懂的问题：
  - wrapper 应该放在 `alphaapollo/core/skills/builtin/...`，还是放在 env bridge 里。
  - `informalmath_verify` 是否也应该在后续迁移成 skill，还是只保留旧路径。

### Change 021: 创建 Phase 4 实现计划

- 日期：2026-05-22
- 改动：
  - 新增 `.planning/phases/04-env-tool-path/04-01-PLAN.md`
  - 更新 `.planning/STATE.md`
  - 更新 `.planning/ROADMAP.md`
  - 更新 `docs/task-b/design.md`
- 我理解的目的：在改 `env.py` 前，先把 structured `<tool_call>` 怎么接入真实训练环境拆成小步骤。
- 当前理解：
  - Phase 4 不是继续造新模块，而是把前面做好的 parser / registry / validator / dispatcher 接到 environment side。
  - 这一步最重要的是兼容旧行为，不能为了新格式直接删掉旧 `<python_code>` / `<local_rag>`。
  - `InformalMathToolGroup` 仍然重要，因为它保存了旧工具的真实返回格式、score、timeout、RAG 配置等。
  - dispatcher 应该保持通用；env 负责 chat history、done、reward、metadata 和 `<tool_response>` 包装。
- 下一步：
  - 先实现一个小的 env-side bridge，再改 `informal_math_training/env.py`。

## 7. 下一步

下一步进入 Phase 4 实现，不急着改两套 env，先从最小桥接层开始：

```text
目标：让 informal_math_training/env.py 能识别 structured <tool_call>，
并继续兼容旧 <python_code> / <local_rag>。
```

完成 training env 小样例后，再决定是否同步 informal_math_evolving。
