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

### Change 022: 实现 training env 的 structured tool bridge

- 日期：2026-05-22
- 改动：
  - 新增 `alphaapollo/core/environments/informal_math_training/skill_bridge.py`
  - 修改 `alphaapollo/core/environments/informal_math_training/env.py`
  - 修改 `alphaapollo/core/skills/registry.py`
  - 新增 `tests/test_informal_math_skill_bridge.py`
  - 更新 `tests/test_skill_registry.py`
- 我理解的目的：让 `informal_math_training` 先支持 structured `<tool_call>`，同时继续支持旧 `<python_code>`。
- 当前理解：
  - `skill_bridge.py` 把新 `<tool_call>` 和旧 `<python_code>/<local_rag>` 都转换成统一的 `ToolCall`。
  - bridge 用 `SkillRegistry` 找到 skill，用 `validate_arguments` 校验参数。
  - 真正执行工具时，仍复用 `InformalMathToolGroup`，这样旧的 `text_result`、`score`、timeout 和 RAG 配置不会丢。
  - structured 参数错误会变成 `<tool_response>`，不会让 rollout 崩溃。
- 已验证：
  - `python tests/test_informal_math_skill_bridge.py` 通过。
  - `python tests/test_skill_dispatcher.py` 通过。
  - `python tests/test_skill_argument_validation.py` 通过。
  - `python tests/test_tool_call_parser.py` 通过。
  - `python tests/test_skill_registry.py` 通过。
  - `python tests/test_skill_loader.py` 通过。
  - 用 `/Users/wangjiaxuan/miniforge3/envs/alphaapollo/bin/python` 做 smoke test，structured `python_code` 和 legacy `<python_code>` 都能返回 `<tool_response>`。
- 下一步：
  - 验证 structured / legacy `local_rag` 路径。
  - 再决定是否把相同 bridge 同步到 `informal_math_evolving`。

### Change 023: 验证 local_rag 新旧路径

- 日期：2026-05-22
- 改动：
  - 更新 `alphaapollo/core/environments/informal_math_training/env.py`
  - 更新 `tests/test_informal_math_skill_bridge.py`
  - 更新 `docs/task-b/phase-4-env-integration.md`
  - 更新 `.planning/STATE.md`
  - 更新 `.planning/phases/04-env-tool-path/04-01-PLAN.md`
- 我理解的目的：确认 `local_rag` 也能通过 structured `<tool_call>` 和旧 `<local_rag>` 两条路径进入同一个 Skill bridge。
- 当前理解：
  - registry 用来认识有哪些内置 skill 和校验参数。
  - 工具是否启用仍由 `InformalMathToolGroup` 的 `enable_local_rag` 控制。
  - 这样 `enable_local_rag=false` 时，模型调用 `local_rag` 会得到旧的 disabled 响应，而不是 `unknown_skill`。
  - 旧 `<local_rag>not json</local_rag>` 继续返回原来的错误文本：`Error: Invalid JSON input for local_rag`。
- 已验证：
  - structured `local_rag` 在 RAG 关闭时返回 `<tool_response>{"result": "Local RAG is not enabled.", "status": "disabled"}</tool_response>`。
  - legacy `<local_rag>` 在 RAG 关闭时返回同样 disabled 响应。
  - legacy `<local_rag>` 非法 JSON 保留旧错误文本。
  - 全部 Phase 1-4 相关测试通过。
- 下一步：
  - 评估是否要同步 `informal_math_evolving`，或者记录为后续阶段再做。

### Change 024: 让 env bridge 重新走 dispatcher

- 日期：2026-05-22
- 改动：
  - 修改 `alphaapollo/core/skills/dispatcher.py`
  - 修改 `alphaapollo/core/environments/informal_math_training/skill_bridge.py`
  - 修改 `tests/test_skill_dispatcher.py`
  - 更新 `docs/task-b/phase-3-tool-call.md`
  - 更新 `docs/task-b/phase-4-env-integration.md`
- 我理解的目的：让实际 env 运行时更贴合 B3 要求，不让 bridge 自己重复做“查 registry + 校验 + 归一化”。
- 当前理解：
  - `dispatch_tool_call(call, registry)` 默认仍然会导入并执行 `SKILL.md` 的 `entrypoint.path`。
  - `dispatch_tool_call(call, registry, executor=...)` 会先查 registry、校验 arguments，再把 `SkillSpec` 和校验后的参数交给 executor。
  - training env 的 executor 负责调用 `InformalMathToolGroup`，这样旧的 `text_result`、`score`、timeout 和 enable flag 都还能保留。
  - 这样可以解释为：dispatcher 负责通用规则，runtime executor 负责具体环境执行。
- 已验证：
  - structured `python_code` 可以返回成功 `<tool_response>`。
  - legacy `<python_code>` 仍然可以返回成功 `<tool_response>`。
  - structured `local_rag` 在 RAG 关闭时返回 disabled `<tool_response>`。
  - legacy `<local_rag>` 在 RAG 关闭时返回 disabled `<tool_response>`。
  - structured 参数错误仍然返回结构化 `<tool_response>`。
- 下一步：
  - Phase 4 收尾，进入 Phase 5 prompt 自动生成。

### Change 025: Phase 4 主线收尾

- 日期：2026-05-22
- 改动：
  - 更新 `.planning/REQUIREMENTS.md`
  - 更新 `.planning/ROADMAP.md`
  - 更新 `.planning/STATE.md`
  - 更新 `.planning/phases/04-env-tool-path/04-01-PLAN.md`
  - 更新 `docs/task-b/design.md`
  - 更新 `docs/task-b/phase-4-env-integration.md`
- 我理解的目的：把 Phase 4 从“实现中”整理为“training env 主线完成”，并明确 `informal_math_evolving` 暂不同步。
- 当前理解：
  - Task B 的主线是 `informal_math_training`。
  - 这个环境已经支持 structured `<tool_call>` 的 `python_code` / `local_rag`。
  - 旧标签路径继续兼容。
  - runtime 现在通过 dispatcher + executor 组合执行，符合 B3 对 dispatcher 的要求。
  - `informal_math_evolving` 有相似但不同的旧路径，后续可以同步，但不是当前最高优先级。
- 下一步：
  - Phase 5：从 registry / `SKILL.md` 自动生成 prompt 工具说明。

### Change 026: 开始 Phase 5 prompt 自动生成设计

- 日期：2026-05-22
- 改动：
  - 新增 `.planning/phases/05-prompt-auto-generation/05-CONTEXT.md`
  - 新增 `.planning/phases/05-prompt-auto-generation/05-01-PLAN.md`
  - 新增 `docs/task-b/phase-5-prompt.md`
  - 更新 `docs/task-b/README.md`
  - 更新 `docs/task-b/design.md`
- 我理解的目的：进入 Task B4，让 prompt 工具说明从 `SKILL.md` / registry 自动生成，而不是继续手写 `<python_code>` / `<local_rag>`。
- 当前理解：
  - Phase 5 不改工具执行链路。
  - Phase 5 要新增 prompt renderer，把 `SkillSpec` 转成模型能看的工具说明。
  - 新 prompt 应该主推统一 `<tool_call>` 格式。
  - 旧标签兼容仍然留在 env bridge，不作为新 prompt 的主要说明。
- 下一步：
  - 实现 `alphaapollo/core/skills/prompt.py` 和对应测试。

### Change 027: 实现 prompt 自动生成

- 日期：2026-05-22
- 改动：
  - 新增 `alphaapollo/core/skills/prompt.py`
  - 新增 `tests/test_skill_prompt_renderer.py`
  - 修改 `alphaapollo/core/environments/prompts/informal_math_training.py`
  - 修改 `alphaapollo/core/environments/env_manager.py`
  - 更新 `alphaapollo/core/skills/__init__.py`
- 我理解的目的：完成 Task B4，让 training prompt 的工具说明从 `SkillSpec` 自动生成，而不是继续手写 `<python_code>` / `<local_rag>`。
- 当前理解：
  - `render_skill_prompt_block(specs)` 会读取 `SkillSpec.name`、`description`、`parameters`、`examples`。
  - examples 会自动渲染成 `<tool_call>{"name":"...","arguments":{...}}</tool_call>`。
  - `env_manager` 会根据 `env.skills` 或旧开关加载 enabled skill specs，然后传给 `get_policy_training_prompt(..., tool_specs=...)`。
  - 旧 `tool_config` fallback 暂时保留，避免 demo 或旧脚本突然失效。
- 已验证：
  - `python tests/test_skill_prompt_renderer.py` 通过。
  - Phase 1-5 相关测试全部通过。
  - 用 `alphaapollo` 环境生成过实际 prompt，确认包含 `<tool_call>`，不再主推 `<python_code>` / `<local_rag>`。
- 下一步：
  - 进入 Phase 6：保存 trajectory 样例、整理回归和 README。

### Change 028: 开始 Phase 6 并保存 structured trajectory

- 日期：2026-05-22
- 改动：
  - 新增 `.planning/phases/06-regression-docs/06-CONTEXT.md`
  - 新增 `.planning/phases/06-regression-docs/06-01-PLAN.md`
  - 新增 `docs/task-b/experiments.md`
  - 新增 `docs/task-b/trajectories/structured-python-code-smoke.md`
  - 更新 `docs/task-b/README.md`
- 我理解的目的：开始整理交付证据，先保存一条结构化 tool call 的最小 trajectory。
- 当前理解：
  - COMPAT-06 要求至少保存一个包含结构化 function-call 与 `<tool_response>` 的 trajectory。
  - smoke trajectory 不等于 MATH-500 回归，它只证明新调用链能端到端跑通。
  - MATH-500 baseline / skill 版本对比仍需要模型和 GPU 资源，暂时记录为 pending。
- 已验证：
  - prompt 自动生成 `<tool_call>` 示例。
  - assistant action 使用 structured `<tool_call>`。
  - env 返回 `<tool_response>`。
  - metadata 中 `tool_call_format=structured`。
- 下一步：
  - 更新 README Task B 专区，说明重构前后流程、测试命令和当前回归状态。

### Change 029: 4090 服务器 vLLM smoke / sanity 验证

- 日期：2026-05-23
- 改动：
  - 修改 `alphaapollo/core/environments/prompts/informal_math_training.py`
  - 修改 `alphaapollo/core/generation/verl/trainer/main_generation.py`
  - 更新 `docs/task-b/experiments.md`
  - 更新 `docs/task-b/server-environment.md`
- 我理解的目的：把 Task B 从“单元测试通过”推进到“真实模型 + vLLM + env 评分链路跑通”。
- 当前理解：
  - prompt 里原来只说可以 tool call 或 answer，但模型可能只输出 `<think>...</think>` 就停止，相当于想完了但没交卷。
  - 新 prompt 增加了合法答案格式和合法工具格式，重点约束输出协议，不改变数学题本身。
  - vLLM 0.8.5 关闭 top-k 要用 `top_k=-1`，不能用 HF 常见的 `top_k=0`。
  - `main_generation.py` 原来的 `np.transpose` 对 `n_samples=1` 和多步 history/reward 嵌套结构不稳定，所以改为显式 list 转置。
- 已验证：
  - 4090 服务器上 Qwen2.5-3B-Instruct 本地模型可加载。
  - 单题 `1+1` vLLM rollout 得到 `avg@1=1.0000`。
  - MATH-500 前 5 题 strict-format prompt 得到 `avg@1=0.6000`。
  - 本机 `test_skill_prompt_renderer.py`、`test_tool_call_parser.py`、`test_skill_registry.py` 通过。
- 还不懂或待确认的问题：
  - 20 题或 100 题时，错误主要来自模型能力，还是仍有 tool-call 格式问题。
  - 是否需要给模型加“工具调用后必须根据 tool_response 再回答”的更强示例。

### Change 030: 整理服务器迁移与提交流程

- 日期：2026-05-23
- 改动：
  - 检查新服务器连接、GPU、conda 环境、模型文件、Task B 单元测试。
  - 确认新服务器 `/root/AlphaApollo-TaskB` 是从 tarball / 镜像恢复的，没有 `.git` 目录。
  - 准备把本机改动分组提交：Task B 实验主线与运行环境兼容补丁分开记录。
- 我理解的目的：让本机和服务器的职责清楚起来。
- 当前理解：
  - 本机是代码和 git 的主版本。
  - 服务器是运行模型和实验的地方。
  - 实验结果要写回 docs，而不是只留在服务器输出里。
  - 没有 `.git` 的服务器可以运行，但不适合作为代码管理源头。
- 已验证：
  - 新服务器 GPU 是 RTX 4090，CUDA / torch 可用。
  - `alphaapollo` conda 环境存在，关键依赖存在。
  - 模型目录 `models/Qwen2.5-3B-Instruct` 完整。
  - Task B 关键单元测试通过。
- 下一步：
  - 提交当前改动。
  - 将本机代码同步到新服务器。
  - 跑 MATH-500 20 题 sanity test。

### Change 031: 单独记录运行环境兼容补丁

- 日期：2026-05-23
- 改动：
  - 修改 `alphaapollo/core/generation/verl/trainer/fsdp_sft_trainer.py`
  - 修改 `alphaapollo/core/generation/verl/workers/actor/dp_actor.py`
  - 修改 `alphaapollo/core/generation/verl/workers/critic/dp_critic.py`
  - 修改 `alphaapollo/core/generation/verl/workers/fsdp_workers.py`
  - 修改 `alphaapollo/core/generation/verl/workers/rollout/vllm_rollout/vllm_rollout_spmd.py`
- 我理解的目的：让服务器环境缺少某些可选高性能依赖时，代码能给出清晰错误或使用可用 fallback，而不是 import 阶段直接崩溃。
- 当前理解：
  - `flash-attn` 是高性能 attention / padding 相关依赖，但不是所有环境都一定装好。
  - 如果 `use_remove_padding=True`，确实需要 `flash-attn`，所以应该在真正使用时明确报错。
  - 如果没有 `flash-attn`，模型配置可以 fallback 到 `sdpa`，这样基础生成和 smoke test 仍然可跑。
  - vLLM 不同版本的 `WorkerWrapperBase` 模块路径不同，需要兼容旧路径和 v1 路径。
  - `AutoModelForVision2Seq` 在部分 Transformers 版本中不存在，所以导入失败时应回退到 causal LM。
- 已验证：
  - 相关文件 `py_compile` 通过。
  - Task B 关键单元测试通过。
- 注意：
  - 这组补丁服务于运行环境兼容，不是 Task B 的 SkillSpec / dispatcher 主线逻辑。
  - 因此和 Change 029 的实验主线分开提交，方便以后回滚或解释。

### Change 032: 美国 4090 服务器作为推荐实验机

- 日期：2026-05-23
- 改动：
  - 检查美国服务器连接、GPU、CUDA、conda、GitHub 网络和 Hugging Face 网络。
  - 将 `/root/AlphaApollo-TaskB` 整理成真正的 GitHub clone。
  - 保留服务器上的 `models/` 和 `data/` 运行资源。
  - 更新 `docs/task-b/server-environment.md`。
- 我理解的目的：把服务器从“能跑但不方便同步”的状态，整理成“本机 GitHub push、服务器 GitHub pull”的标准协作方式。
- 当前理解：
  - 本机负责写代码和提交版本。
  - GitHub 是本机和服务器之间的代码中转站。
  - 服务器不应该手工改核心代码，主要负责跑 GPU 实验。
  - 模型和实验数据很大，不放进 Git，留在服务器本地。
- 已验证：
  - GitHub `main` 分支可以在美国服务器正常访问。
  - 服务器仓库 HEAD 是 `f36b1f0`。
  - Task B 关键单元测试全部通过。
  - PyTorch CUDA / bfloat16 smoke test 通过。
- 下一步：
  - 在美国服务器跑 MATH-500 20 题 sanity test。
  - 把 20 题结果写入 `docs/task-b/experiments.md`。

### Change 033: 增加新旧 prompt 回归开关

- 日期：2026-05-23
- 改动：
  - 修改 `alphaapollo/core/environments/env_manager.py`
  - 新增配置开关 `env.tool_prompt_format=legacy|skill`
  - 使用 `legacy` 时走旧 `<python_code>...</python_code>` prompt
  - 使用 `skill` 时走新 `<tool_call>{"name": ..., "arguments": ...}</tool_call>` prompt
- 我理解的目的：为了公平比较 Task B 迁移前后效果，要尽量只改变“模型看到的工具格式”，其他模型、数据、rollout 参数都保持一样。
- 当前理解：
  - `legacy` 不是回退代码实现，而是让模型看到旧格式 prompt，方便作为 Task A 风格 baseline。
  - `skill` 是 Task B 的新格式 prompt。
  - 两组都仍然跑同一个 env / vLLM / 模型 / 数据子集。
- 已验证：
  - `python -m py_compile alphaapollo/core/environments/env_manager.py alphaapollo/core/environments/prompts/informal_math_training.py` 通过。
  - Task B 关键单元测试通过。

### Change 034: 完成 MATH-500 固定 100 题回归，但 B6 未通过

- 日期：2026-05-23
- 改动：
  - 在服务器生成 MATH-500 固定 100 题子集。
  - 跑 `legacy` baseline。
  - 跑 `skill` structured prompt。
  - 调整 prompt 后跑 `skill_v2`。
  - 更新 `docs/task-b/experiments.md`。
- 实验结果：
  - `legacy`: `avg@1/pass@1 = 0.58`
  - `skill`: `avg@1/pass@1 = 0.38`
  - `skill_v2`: `avg@1/pass@1 = 0.32`
- 我理解的目的：B6 要求 Task B skill 版本相对 Task A baseline 误差不超过 3%，所以必须真实跑一个至少 100 题的固定子集对比。
- 当前理解：
  - 新 Skill 代码链路能跑通，不代表回归就通过。
  - 这次主要失败点是模型在新 prompt 下行为变了：旧 prompt 有 48 次 legacy tool tag，新 prompt 只有 12 次 structured tool call。
  - `skill_v2` 增强了“优先用工具”的提示，但结果没有改善，说明不能只靠一句提示解决。
  - 现在应该承认 B6 未通过，并做差异分析，而不是继续扩大题量。
- 下一步：
  - 抽取 `legacy` 正确、`skill` 错误的样本。
  - 对比它们的 assistant 输出，找出是没调用工具、工具格式错、还是最终答案错。
  - 再针对性改 prompt 或桥接逻辑。

### Change 035: 分析 100 题回归失败样本

- 日期：2026-05-23
- 改动：
  - 新增 `docs/task-b/regression-analysis.md`
  - 在服务器读取 100 题 parquet 和三份 JSONL 输出。
  - 对比 `legacy` / `skill` / `skill_v2` 的对错和 tool-call 格式。
- 实验发现：
  - `legacy` 对、`skill` 错的样本有 30 题。
  - 这 30 题里，`skill` 有 26 题是直接给了最终答案但答案错。
  - 另有 2 题是不完整 `<tool_call>` 标签，2 题没有最终答案也没有工具调用。
  - `skill` 全 100 题只有 2 行产生了完整有效的 structured tool call。
- 我理解的目的：确认 B6 失败到底是代码链路问题，还是模型在新 prompt 下行为改变。
- 当前理解：
  - registry / dispatcher / env bridge 不是主要失败点。
  - 主要失败点是 prompt 行为：模型没有像旧 `<python_code>` prompt 那样稳定使用工具。
  - 下一步应该做 prompt 对齐和 targeted regression，而不是马上扩大到 500 题。

### Change 036: 对齐 Skill prompt 的工具使用说明

- 日期：2026-05-23
- 改动：
  - 修改 `alphaapollo/core/environments/prompts/informal_math_training.py`
  - 修改 `alphaapollo/core/skills/builtin/python_code/SKILL.md`
  - 修改 `tests/test_skill_prompt_renderer.py`
- 我理解的目的：在不改变工具能力、不改变 reward、不改变数据和模型的前提下，让模型更容易学会 structured skill 调用格式。
- 具体变化：
  - prompt 明确说明：如果选择 tool call，本轮只输出一个完整 `<tool_call>`，然后停止，等待 `<tool_response>`。
  - prompt 明确说明：收到 `<tool_response>` 后，除非确实需要再次调用工具，否则应输出最终 `<answer>`。
  - `python_code/SKILL.md` 增加更贴近 MATH-500 的 examples：复数计算、圆排列计数、精确概率。
- 为什么不违背 B6 对比要求：
  - 没有改 `python_code` 的执行函数。
  - 没有改 `local_rag` 的执行函数。
  - 没有改 env 的 reward / done / history 逻辑。
  - 没有改模型、数据、采样参数或 `max_steps`。
  - 只是在 Skill 自描述和 prompt renderer 结果里更清楚地教模型如何使用同一个工具。
- 已验证：
  - `python tests/test_skill_prompt_renderer.py` 通过。
  - `python tests/test_informal_math_skill_bridge.py` 通过。
  - `python tests/test_skill_dispatcher.py` 通过。
  - `python tests/test_tool_call_parser.py` 通过。
  - `python tests/test_skill_loader.py` 通过。
- 下一步：
  - 作为 `skill_v3` 重新跑固定 100 题回归。
  - 对比 `legacy=0.58`、`skill=0.38`、`skill_v2=0.32`、`skill_v3=?`。

### Change 037: 同步服务器实验 artifacts 到 GitHub

- 日期：2026-05-23
- 改动：
  - 新增 `docs/task-b/artifacts/regression-100/README.md`
  - 同步服务器上的 100 题 JSONL 输出：
    - `qwen25_3b_vllm_math500_100_legacy.json`
    - `qwen25_3b_vllm_math500_100_skill.json`
    - `qwen25_3b_vllm_math500_100_skill_v2.json`
  - 同步分析摘要 `task_b_regression_analysis.json`
  - 同步运行脚本 `run_math500_100_regression.sh` 和 `run_math500_100_skill_v2.sh`
- 我理解的目的：让 GitHub 仓库不仅有文字结论，也有可检查的模型输出、reward 和 history 证据。
- 没有同步的内容：
  - 模型文件。
  - conda 环境。
  - 服务器日志。
  - parquet 文件。
- 为什么不提交 parquet：
  - 原仓库 `.gitignore` 明确忽略 `data/` 和 `*.parquet`。
  - JSONL 输出已经包含题目、答案、history 和 rewards，足够复核 Task B 回归结论。
  - 输入 parquet 可以用固定 seed 和 sample indices 重建。

### Change 038: 跑 skill_v3 100 题回归

- 日期：2026-05-23
- 改动：
  - 在服务器拉取最新 GitHub 代码。
  - 基于同一个 MATH-500 固定 100 题子集运行 `skill_v3`。
  - 同步 `qwen25_3b_vllm_math500_100_skill_v3.json`、`run_math500_100_skill_v3.sh` 和 `task_b_regression_analysis_with_v3.json` 到 artifact 目录。
  - 更新 `docs/task-b/experiments.md` 和 `docs/task-b/artifacts/regression-100/README.md`。
- 实验结果：
  - `legacy`: `avg@1/pass@1 = 0.58`
  - `skill`: `avg@1/pass@1 = 0.38`
  - `skill_v2`: `avg@1/pass@1 = 0.32`
  - `skill_v3`: `avg@1/pass@1 = 0.28`
- 我理解的目的：验证“更明确的 tool-call 停止规则 + 更多 MATH 风格 examples”是否能提高 structured skill 成功率。
- 当前理解：
  - `skill_v3` 没有改善，反而更低。
  - 全 100 题中 `skill_v3` 只有 14 行出现 `<tool_call>`，完整有效 structured tool call 为 0。
  - 这说明简单增加说明和 examples 不足以解决问题，可能还增加了 3B 模型的 prompt 负担。
  - 下一步更应该做“对齐旧 prompt 的最小 structured 格式”，或者把 legacy 正确轨迹转换成 structured 格式做 SFT / few-shot，而不是继续堆长说明。

### Change 039: 设计 skill_v4 最小 prompt

- 日期：2026-05-23
- 改动：
  - 修改 `alphaapollo/core/environments/prompts/informal_math_training.py`
  - 修改 `alphaapollo/core/skills/prompt.py`
  - 修改 `alphaapollo/core/skills/builtin/python_code/SKILL.md`
  - 修改 `tests/test_skill_prompt_renderer.py`
- 我理解的目的：前面 `skill_v3` 说明更长、examples 更多，但 3B 模型反而表现更差，所以这次反过来做“减法”，让 Skill 版 prompt 更像原来的 tool-call prompt。
- 具体变化：
  - 去掉冗长的 structured tool-call 说明，只保留两种动作：`<tool_call>{...}</tool_call>` 或 `<answer>...</answer>`。
  - `SkillSpec` 生成的工具说明从长列表改成紧凑的 `Tool schemas`。
  - `python_code/SKILL.md` 暂时只保留一个最简单 example，避免 examples 太多挤占题目和推理空间。
- 通俗解释：
  - 这次不是改工具能力，而是改“给模型看的说明书”。
  - v3 像一份很详细的操作手册，但小模型可能看晕。
  - v4 像原来的简短考试说明：你可以调用工具，也可以直接交答案，但格式要对。
- 已验证：
  - `python tests/test_skill_prompt_renderer.py` 通过。
  - `python tests/test_informal_math_skill_bridge.py` 通过。
  - `python tests/test_skill_dispatcher.py` 通过。
  - `python tests/test_tool_call_parser.py` 通过。
  - `python tests/test_skill_loader.py` 通过。
  - `python tests/test_skill_registry.py` 通过。
  - `python tests/test_skill_argument_validation.py` 通过。
- 下一步：
  - 提交并同步到 GitHub。
  - 在服务器拉取最新代码，作为 `skill_v4` 跑固定 100 题回归。
  - 如果 `skill_v4` 仍然明显低于 `legacy=0.58`，就说明仅靠 prompt 调整很可能不够，需要考虑 few-shot 轨迹或训练数据对齐。

### Change 040: 跑 skill_v4 100 题回归

- 日期：2026-05-23
- 改动：
  - 在服务器拉取 commit `0188438`。
  - 基于同一个 MATH-500 固定 100 题子集运行 `skill_v4`。
  - 同步 `qwen25_3b_vllm_math500_100_skill_v4.json` 和 `run_math500_100_skill_v4.sh` 到 artifact 目录。
- 实验结果：
  - `legacy`: `avg@1/pass@1 = 0.58`
  - `skill`: `avg@1/pass@1 = 0.38`
  - `skill_v2`: `avg@1/pass@1 = 0.32`
  - `skill_v3`: `avg@1/pass@1 = 0.28`
  - `skill_v4`: `avg@1/pass@1 = 0.33`
- 细节观察：
  - `skill_v4` 有 51 行输出 `<answer>`。
  - `skill_v4` 有 28 行出现 `<tool_call>`。
  - 但完整有效的 structured JSON tool call 只有 1 个。
  - 还有 8 行输出了旧的 `<python_code>` 或 `<local_rag>` 标签，说明模型仍会被旧格式习惯影响。
- 我理解的结论：
  - `skill_v4` 比 `skill_v3` 好一点，但仍远低于 Task A baseline。
  - 这说明“把 prompt 写短”可以减少一点负担，但不能根治格式跟随问题。
  - 目前 B6 仍未通过，主要卡点是模型没有稳定学会 `<tool_call>{"name": ..., "arguments": ...}</tool_call>`。

### Change 041: 设计 skill_v5 adapter prompt

- 日期：2026-05-23
- 改动：
  - 修改 `alphaapollo/core/environments/prompts/informal_math_training.py`
  - 更新 `docs/task-b/regression-analysis.md`
- 我理解的目的：根据 `skill` 到 `skill_v4` 的真实输出，针对模型最常犯的 tool-call 格式错误做最小纠偏。
- 具体变化：
  - 去掉动作说明里容易被模型照抄的 `<tool_call>...</tool_call>` 占位表达。
  - 增加两个 Bad 例子：
    - `<tool_call>python_code {"code":"print(1+1)"}</tool_call>`
    - `<tool_call>...</tool_call>`
  - 增加一个 Good 例子：
    - `<tool_call>{"name":"python_code","arguments":{"code":"print(1+1)"}}</tool_call>`
  - 明确不要写 YAML、重复 `<tool_call>`、placeholder dots，或在 JSON 前写额外文本。
- 通俗解释：
  - v5 不是继续堆长说明。
  - v5 是“对症下药”：模型之前怎么写坏，我们就用很短的 Bad/Good 对照提醒它。
  - prompt 长度从 v4 的约 1157 字符增加到约 1398 字符，仍明显短于 v1/v2/v3。
- 已验证：
  - `python tests/test_skill_prompt_renderer.py` 通过。
  - `python tests/test_informal_math_skill_bridge.py` 通过。
  - `python tests/test_skill_dispatcher.py` 通过。
  - `python tests/test_tool_call_parser.py` 通过。
  - `python tests/test_skill_loader.py` 通过。
  - `python tests/test_skill_registry.py` 通过。
  - `python tests/test_skill_argument_validation.py` 通过。
  - `python -m py_compile alphaapollo/core/environments/prompts/informal_math_training.py alphaapollo/core/skills/prompt.py tests/test_skill_prompt_renderer.py` 通过。
- 下一步：
  - 提交并同步到服务器。
  - 作为 `skill_v5` 跑固定 100 题回归，观察有效 JSON tool call 数是否上升。

### Change 042: 跑 skill_v5 100 题回归

- 日期：2026-05-23
- 改动：
  - 在服务器拉取 commit `7e50310`。
  - 基于同一个 MATH-500 固定 100 题子集运行 `skill_v5`。
  - 同步 `qwen25_3b_vllm_math500_100_skill_v5.json`、`run_math500_100_skill_v5.sh` 和 `task_b_regression_analysis_with_v5.json` 到 artifact 目录。
- 实验结果：
  - `legacy`: `avg@1/pass@1 = 0.58`
  - `skill_v4`: `avg@1/pass@1 = 0.33`
  - `skill_v5`: `avg@1/pass@1 = 0.11`
- 细节观察：
  - `skill_v5` 有 53 行出现 `<tool_call>`，比 `skill_v4` 的 28 行更多。
  - 完整有效 JSON tool call 从 `skill_v4` 的 1 个增加到 4 个。
  - 但 `<answer>` 行数从 `skill_v4` 的 51 行下降到 19 行。
  - 无动作行数增加到 34 行。
  - 很多输出开始照抄 `Tool-call format adapter:`、`Good:` 等 prompt 文本。
- 我理解的结论：
  - Bad/Good adapter prompt 没有解决问题，反而明显伤害准确率。
  - 这说明 3B 模型容易把 prompt 里的格式教学内容当成要输出的正文。
  - 下一步不要继续在 prompt 中加入 Bad/Good 对照；如果继续 prompt 路线，更应该考虑在 parser 侧做兼容，或者用 few-shot 但避免显式 “Bad/Good” 字样。

### Change 043: 实现 Skill 驱动的 legacy parser adapter

- 日期：2026-05-23
- 改动：
  - 在 `SkillSpec` 中增加 `legacy_calls` 字段。
  - 在 `SKILL.md` 中声明旧标签兼容入口：
    - `python_code`: `<python_code>...</python_code>` 映射到参数 `code`
    - `local_rag`: `<local_rag>{...}</local_rag>` 按 JSON object 解析
  - 修改 informal math parser：旧标签不再由 `skill_bridge.py` 硬编码表驱动，而是从 registry 中已加载 skill 的 `legacy_calls` 读取。
  - env 调用 parser 时传入 `self.skill_registry`。
- 我理解的目的：
  - 让模型可以继续使用 Task A 中更熟悉的旧格式，减少严格 JSON `<tool_call>` 带来的格式失败。
  - 但内部仍统一转换成 `ToolCall(name, arguments)`，后续继续走 SkillSpec 参数校验、registry 和 dispatcher。
  - 这样更符合 B6 的“行为不变”，同时避免核心 parser 写死 `python_code` / `local_rag`。
- 已验证：
  - `python tests/test_skill_loader.py` 通过。
  - `python tests/test_informal_math_skill_bridge.py` 通过。
  - `python tests/test_skill_dispatcher.py` 通过。
  - `python tests/test_skill_registry.py` 通过。
  - `python tests/test_skill_prompt_renderer.py` 通过。
  - `python tests/test_tool_call_parser.py` 通过。
  - `python -m py_compile` 相关模块通过。
- 下一步：
  - 把 prompt 从失败的 `skill_v5` Bad/Good 说明回退到更接近 legacy 的工具说明。
  - 作为 `skill_v6_legacy_adapter` 跑固定 100 题回归，观察是否接近 Task A baseline `0.58`。

### Change 044: 实现 skill_v6 legacy adapter prompt

- 日期：2026-05-23
- 改动：
  - 新增 `render_legacy_skill_prompt_block(...)`，从 `SkillSpec.legacy_calls` 自动生成旧标签工具说明。
  - 新增 `tool_call_style="legacy"`，使 `get_policy_training_prompt(..., tool_specs=...)` 可以渲染 SKILL.md 驱动的 legacy prompt。
  - 新增 `env.tool_prompt_format=skill_legacy|legacy_adapter`，用于区分：
    - `legacy`: 旧手写 baseline prompt
    - `skill`: structured `<tool_call>` prompt
    - `skill_legacy`: SKILL.md 驱动的 `<python_code>` / `<local_rag>` prompt
- 我理解的目的：
  - 主线实验不再强迫 3B 模型学习严格 JSON tool call。
  - 让模型侧尽量接近 Task A 习惯，同时内部仍走 SkillSpec / registry / dispatcher。
  - 这比错误反馈重试更公平，因为没有给 Skill 版额外“补考机会”。
- prompt 对比：
  - `skill_v5 structured`: 约 1398 字符 / 20 行。
  - `skill_v6 legacy adapter`: 约 895 字符 / 10 行。
  - `legacy baseline`: 约 818 字符 / 9 行。
- 已验证：
  - `python tests/test_skill_prompt_renderer.py` 通过。
  - `python -m py_compile` prompt 相关模块通过。
- 下一步：
  - 提交并同步到服务器。
  - 用 `+env.tool_prompt_format=skill_legacy` 跑固定 100 题回归。

### Change 045: 跑 skill_legacy 100 题回归并生成 prompt 展示

- 日期：2026-05-23
- 改动：
  - 在服务器拉取 commit `9433df1`。
  - 使用 `+env.tool_prompt_format=skill_legacy` 跑同一个 MATH-500 固定 100 题子集。
  - 同步 `qwen25_3b_vllm_math500_100_skill_legacy.json`。
  - 生成 `docs/task-b/prompts/current-prompt-gallery.md`，展示当前几类 prompt 的完整文本。
- 实验结果：
  - `legacy`: `avg@1/pass@1 = 0.58`
  - `skill`: `avg@1/pass@1 = 0.38`
  - `skill_v5`: `avg@1/pass@1 = 0.11`
  - `skill_legacy`: `avg@1/pass@1 = 0.48`
- 细节观察：
  - `skill_legacy` 有 59 行输出旧 `<python_code>` / `<local_rag>` 标签。
  - 没有 structured `<tool_call>`，因为这版 prompt 故意让模型使用旧标签。
  - `<answer>` 行数是 47。
  - 准确率比最初 `skill` 高 10 个百分点，比 `skill_v5` 高 37 个百分点。
- 我理解的结论：
  - parser legacy adapter 的方向是对的，证明主要问题确实是模型不稳定输出严格 JSON tool call。
  - 但 `0.48` 仍低于 Task A baseline `0.58`，B6 还没有通过。
  - 下一步应该对比 `legacy` 和 `skill_legacy` prompt 的细小差异，以及检查 tool_response / reward 轨迹是否有行为差异。

## 7. 下一步

下一步继续 Phase 6 的回归失败分析：对比 `legacy` 和 `skill_legacy` 的 prompt/trajectory 差异，找出剩余 10 个百分点差距来自哪里。

```text
目标：从固定 100 题结果中抽取 legacy 正确、skill 错误的样本，
确认准确率下降主要来自 prompt 行为、tool-call 格式，还是最终答案质量。
```

只有当 100 题回归进入 3% 误差以内，再考虑全量 500 题。

### Change 046: 参考 vLLM/Qwen Hermes 思路，但保留自己的 parser

- 日期：2026-05-23
- 背景：
  - vLLM 文档提到 Qwen2.5 的 tokenizer chat template 支持 Hermes-style tool use，可以配合 `--tool-call-parser hermes`。
  - 但 Task B 要求我们自己实现 parser / dispatcher，所以不能直接用 vLLM hermes parser 替代项目里的 parser。
- 改动：
  - `alphaapollo/core/skills/call_parser.py` 继续保留 canonical `<tool_call>{...}</tool_call>` 解析。
  - 新增对 Hermes-like / OpenAI-like 结构的兼容：
    - `<tool_calls>[{"name":"python_code","arguments":{...}}]</tool_calls>`
    - `<tool_calls>{"tool_calls":[{"type":"function","function":{"name":"python_code","arguments":"{...}"}}]}</tool_calls>`
  - 这些格式最终都会被归一化成同一个内部对象：

```text
ToolCall(name="python_code", arguments={"code": "..."})
```

  - `skill_bridge.py` 识别 `<tool_calls>`，但后续仍走 SkillSpec / registry / dispatcher。
  - 新增 `render_hermes_skill_prompt_block(...)`，从 `SKILL.md` 生成 OpenAI/Hermes-like function schema。
  - 新增 `env.tool_prompt_format=skill_hermes|hermes|qwen_hermes`，作为一个实验 prompt 格式。
- 我理解的目的：
  - 不是“让 vLLM 代替我们解析”，而是“学习 vLLM/Qwen 对小模型更友好的函数调用格式”。
  - 这样既保留 Task B 的内部实现要求，又给 3B 模型一个更接近官方 tool-use 习惯的输出空间。
  - 这条路线是实验分支，不替代当前最稳的 `skill_legacy` 路线。
- 已验证：
  - `python tests/test_tool_call_parser.py` 通过。
  - `python tests/test_informal_math_skill_bridge.py` 通过。
  - `python tests/test_skill_prompt_renderer.py` 通过。
  - `python tests/test_skill_loader.py` 通过。
  - `python tests/test_skill_dispatcher.py` 通过。
  - `python tests/test_skill_registry.py` 通过。
  - `python -m py_compile` 相关模块通过。
- 下一步：
  - 可以用固定 100 题跑一版 `+env.tool_prompt_format=skill_hermes`，验证它是否比 structured `skill=0.38` 更好。
  - 如果 `skill_hermes` 仍然低于 `skill_legacy=0.48`，主线仍建议回到 `skill_legacy` 并继续缩小它和 Task A baseline 的 prompt 差异。

### Change 047: 在服务器验证 skill_hermes 固定 100 题回归

- 日期：2026-05-23
- 服务器：
  - 美国 RTX 4090 实验服务器。
  - 项目路径：`/root/AlphaApollo-TaskB`。
  - 模型路径：`/root/AlphaApollo-TaskB/models/Qwen2.5-3B-Instruct`。
- 执行内容：
  - 将本地 Hermes-like parser / prompt 补丁应用到服务器 `9433df1` 工作树。
  - 服务器侧通过以下测试：
    - `python tests/test_tool_call_parser.py`
    - `python tests/test_informal_math_skill_bridge.py`
    - `python tests/test_skill_prompt_renderer.py`
    - `python tests/test_skill_loader.py`
    - `python tests/test_skill_dispatcher.py`
    - `python tests/test_skill_registry.py`
    - `python -m py_compile` 相关模块
  - 使用同一个 MATH-500 固定 100 题子集运行：

```text
+env.tool_prompt_format=skill_hermes
```

- 输出文件：
  - 服务器 JSONL：`/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill_hermes.json`
  - 服务器 parquet：`/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill_hermes.parquet`
  - 本地同步：`docs/task-b/artifacts/regression-100/qwen25_3b_vllm_math500_100_skill_hermes.json`
  - 可读版 rollout：`docs/task-b/artifacts/regression-100/readable/qwen25_3b_vllm_math500_100_skill_hermes_rollouts.md`
- 实验结果：
  - `avg@1 = 0.4400`
  - `pass@1 = 0.4400`
  - 重新统计：`44 / 100 = 0.44`
  - `assistant_has_answer = 74`
  - `assistant_has_plural_tool_calls = 46`
  - `assistant_has_structured_tool_call = 1`
  - `valid_structured_tool_calls = 3`
  - `assistant_has_legacy_tool_tag = 0`
- 我理解的结论：
  - `skill_hermes=0.44` 比最初 structured `skill=0.38` 好，说明参考 Qwen/Hermes 格式是有帮助的。
  - 但它低于 `skill_legacy=0.48`，更低于 Task A baseline `legacy=0.58`。
  - 所以主线仍建议优先优化 `skill_legacy`，因为它最符合“行为不变”，也更接近 3B 模型已经习惯的旧 `<python_code>` 标签。

### Change 048: 重新生成完整 prompt 展示文档

- 日期：2026-05-23
- 改动：
  - 新增 `scripts/task_b/export_current_prompts.py`。
  - 重新生成 `docs/task-b/prompts/current-prompt-gallery.md`。
  - 展示当前代码能生成的主要 prompt 分支：
    - `no_tool`
    - `legacy_python_only`
    - `legacy_python_rag`
    - `legacy_rag_only`
    - `structured_skill_python_only`
    - `structured_skill_python_rag`
    - `skill_legacy_adapter_python_only`
    - `skill_legacy_adapter_python_rag`
    - `skill_hermes_python_only`
    - `skill_hermes_python_rag`
  - 每个分支都有 no-history / with-history 两个版本。
- 我理解的目的：
  - 不再靠手动拼 prompt，而是直接用当前代码调用 `get_policy_training_prompt(...)` 渲染。
  - 以后改 prompt 后，只要重新运行这个脚本，就能得到新的完整 prompt 展示。
  - 这方便解释为什么不同实验的成功率不同：可以直接对比模型实际看到的输入。
- 重新生成命令：

```bash
PYTHONPATH=/Users/wangjiaxuan/mini-project/AlphaApollo \
  /Users/wangjiaxuan/miniforge3/envs/alphaapollo/bin/python \
  scripts/task_b/export_current_prompts.py \
  --output docs/task-b/prompts/current-prompt-gallery.md
```

### Change 049: 记录 skill_hermes 中的评分器漏判样本

- 日期：2026-05-23
- 发现：
  - 在 `skill_hermes` 100 题回归中，`Sample 000 / dataset index 0` 的 reward 是 `[[0.0]]`。
  - 题目：把直角坐标点 `(0, 3)` 转成极坐标。
  - 标准答案：`\left( 3, \frac{\pi}{2} \right)`。
  - 模型输出：

```text
<answer>\(\left(3, \frac{\pi}{2}\right)\)</answer>
```

- 人工判断：
  - 这个答案在数学上是正确的。
  - 它和标准答案只差外层 `\(...\)` 和空格。
- 为什么 reward 还是 0：
  - `env.py` 里最终 reward 来自 `compute_score(solution_str, ground_truth)`。
  - `qwen_math.py` 的 `extract_answer(...)` 优先找 `\boxed{...}`。
  - 但这个样本没有写 `\boxed{...}`，而是写在 `<answer>...</answer>` 里。
  - 当前 `extract_answer(...)` 没有优先解析 `<answer>` 标签，所以误抽取了其他文本，导致自动评分为 0。
- 本地验证：

```text
math_equal("\left(3, \frac{\pi}{2}\right)", "\left( 3, \frac{\pi}{2} \right)") -> True
compute_score("<answer>\(\left(3, \frac{\pi}{2}\right)\)</answer>", ground_truth) -> 0.0
compute_score("\boxed{\left(3, \frac{\pi}{2}\right)}", ground_truth) -> 1.0
```

- 我理解的结论：
  - 这是一个 false negative：模型答对了，但自动评分器漏判。
  - 现在主回归暂时不改评分器，因为 Task B 要和 Task A baseline 使用同一套评分规则才公平。
  - 后续可以单独做“人工复核 / 修正版评分器”分析，但不能直接拿修正版结果替代主表里的 baseline 对比。

### Change 050: 强化 `<answer>` 中必须写 `\boxed{...}` 的提示

- 日期：2026-05-23
- 背景：
  - `skill_hermes` 的 `Sample 000` 暴露出一个问题：模型写了数学正确的 `<answer>\(...\)</answer>`，但评分器优先抽取 `\boxed{...}`，导致 reward 为 0。
  - 为了不改评分器、保持和 Task A baseline 可比，更合理的做法是让 prompt 明确告诉模型：最终答案必须用 `\boxed{...}`。
- 改动：
  - 更新 `alphaapollo/core/environments/prompts/informal_math_training.py` 中所有最终答案说明。
  - 原来是较弱的：

```text
formatted in LaTeX, e.g., \boxed{...}
```

  - 现在改成更明确的：

```text
The content inside <answer> must include the final answer in \boxed{...}, e.g., <answer>\boxed{...}</answer>.
```

  - 重新生成 `docs/task-b/prompts/current-prompt-gallery.md`，现在所有 prompt 分支都展示了这个更强约束。
  - 更新 `tests/test_skill_prompt_renderer.py`，增加测试防止这个提示被误删。
- 已验证：
  - `python tests/test_skill_prompt_renderer.py` 通过。
  - `python -m py_compile` 相关模块通过。
- 注意：
  - 这个改动会改变模型输入 prompt，所以需要重新跑固定 100 题才能知道是否提升。
  - 它没有改评分器，因此仍然保持和 baseline 使用同一套 reward 规则。

### Change 051: 服务器回归测试 `skill_hermes_boxed`

- 日期：2026-05-23
- 目的：
  - 验证 Change 050 的 boxed-answer prompt 是否能提升固定 100 题回归。
  - 仍然不改评分器，保持和 Task A baseline 可比。
- 服务器：
  - 仓库路径：`/root/AlphaApollo-TaskB`
  - 模型：`/root/AlphaApollo-TaskB/models/Qwen2.5-3B-Instruct`
  - 数据：`/root/AlphaApollo-TaskB/data/task-b-regression-100/custom_data/test.parquet`
- 运行方式：

```text
env.tool_prompt_format=skill_hermes
输出后缀: skill_hermes_boxed
```

- 输出文件：
  - 服务器 JSONL：`/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill_hermes_boxed.json`
  - 服务器 parquet：`/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill_hermes_boxed.parquet`
  - 本地同步：`docs/task-b/artifacts/regression-100/qwen25_3b_vllm_math500_100_skill_hermes_boxed.json`
  - 可读版 rollout：`docs/task-b/artifacts/regression-100/readable/qwen25_3b_vllm_math500_100_skill_hermes_boxed_rollouts.md`
  - 分析文件：`docs/task-b/artifacts/regression-100/task_b_regression_analysis_with_skill_hermes_boxed.json`
- 实验结果：
  - `avg@1 = 0.4400`
  - `pass@1 = 0.4400`
  - 重新统计：`44 / 100 = 0.44`
  - `assistant_has_answer = 69`
  - `assistant_answer_contains_boxed = 66`
  - `assistant_has_plural_tool_calls = 27`
  - `assistant_has_structured_tool_call = 1`
  - `valid_structured_tool_calls = 6`
- 我理解的结论：
  - 强调 `<answer>\boxed{...}</answer>` 后，模型确实更常把最终答案写成评分器喜欢的 boxed 格式。
  - 完整有效 tool call 也从 `skill_hermes` 的 3 个增加到 6 个。
  - 但最终分数仍然是 0.44，没有超过 `skill_legacy=0.48`，更没有追上 baseline `legacy=0.58`。
  - 所以 boxed prompt 是一个有用的格式修补，但不是解决 B6 回归差距的关键。

### Change 052: 分析并优化 `skill_legacy` prompt 对齐

- 日期：2026-05-23
- 背景：
  - 当前最接近 baseline 的版本是 `skill_legacy=0.48`，而 legacy baseline 是 `0.58`。
  - 因此优先优化 `skill_legacy`，而不是继续堆 Hermes / structured prompt。
- 新增分析脚本：
  - `scripts/task_b/analyze_legacy_gap.py`
  - 输出：`docs/task-b/legacy-vs-skill-legacy-analysis.md`
- 分析结果：
  - `legacy 对，skill_legacy 也对`: 42
  - `legacy 对，skill_legacy 错`: 16
  - `legacy 错，skill_legacy 对`: 6
  - `legacy 错，skill_legacy 也错`: 36
  - `legacy` 的 assistant 含 `<python_code>`：8
  - `skill_legacy` 的 assistant 含 `<python_code>`：21
- 我理解的问题：
  - `skill_legacy` 不是工具用少了，而是更容易在最后一步继续调用 `<python_code>`，没有及时交 `<answer>`。
  - 一个明显 prompt 差异是：`skill_legacy` 自动生成的 `python_code` 说明原来多了内联示例：

```text
Example: <python_code>print(1 + 1)</python_code>
```

  - 这个例子可能让 3B 模型更倾向于照着继续写代码。
- 改动：
  - `alphaapollo/core/skills/prompt.py`
    - `python_code` 的 legacy prompt 不再附带内联 Example。
    - prompt 渲染顺序优先保持 `python_code -> local_rag`，更贴近旧版手写 prompt。
  - `alphaapollo/core/environments/prompts/informal_math_training.py`
    - 只有一个 legacy tool 时使用旧版措辞 `do not perform both`。
    - 多个 legacy tool 时仍使用 `do not perform multiple actions at the same time`。
  - 重新生成 `docs/task-b/prompts/current-prompt-gallery.md`。
- 当前状态：
  - 已继续跑服务器 100 题，结果记录在 Change 053。

### Change 053: 服务器回归测试 `skill_legacy_aligned`

- 日期：2026-05-23
- 目的：
  - 验证 Change 052 的 prompt 对齐是否能修复 `skill_legacy=0.48` 的回归差距。
- 运行方式：

```text
+env.tool_prompt_format=skill_legacy
输出后缀: skill_legacy_aligned
```

- 输出文件：
  - 服务器 JSONL：`/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill_legacy_aligned.json`
  - 服务器 parquet：`/root/AlphaApollo-TaskB/data/task-b-regression-100/qwen25_3b_vllm_math500_100_skill_legacy_aligned.parquet`
  - 本地同步：`docs/task-b/artifacts/regression-100/qwen25_3b_vllm_math500_100_skill_legacy_aligned.json`
  - 可读版 rollout：`docs/task-b/artifacts/regression-100/readable/qwen25_3b_vllm_math500_100_skill_legacy_aligned_rollouts.md`
  - 差异分析：`docs/task-b/legacy-vs-skill-legacy-aligned-analysis.md`
- 实验结果：
  - `avg@1 = 0.6200`
  - `pass@1 = 0.6200`
  - 重新统计：`62 / 100 = 0.62`
  - `assistant_has_answer = 89`
  - `assistant_answer_contains_boxed = 89`
  - `assistant_has_legacy_tool_tag = 14`
- 对比：

```text
legacy baseline:        0.58
skill_legacy:           0.48
skill_legacy_aligned:   0.62
```

- 我理解的结论：
  - 固定 100 题回归已经通过 B6。
  - 这次提升来自“行为对齐”，不是换更复杂的新格式。
  - 原来的 `skill_legacy` 多了一个 `python_code` 内联 example，导致模型更容易在最后一步继续写 `<python_code>`，不交 `<answer>`。
  - 去掉这个 example 后，answer 数从 73 回升到 89，assistant 中 `<python_code>` 从 21 降到 14。

### Change 054: 尝试 7B 模型回归，对当前 4090 机器做资源判断

- 日期：2026-05-23
- 目的：
  - 在同一套 Task B 回归设置下，用 `Qwen2.5-7B-Instruct` 跑一组 100 题对比。
  - 先验证当前服务器是否能承载 7B，再决定是否正式跑 `legacy` 和 `skill_legacy_aligned`。
- 服务器资源：
  - GPU：`NVIDIA GeForce RTX 4090`
  - 显存：`24564 MiB`
  - 模型路径：`/root/AlphaApollo-TaskB/models/Qwen2.5-7B-Instruct`
- 新增脚本：
  - `docs/task-b/artifacts/regression-100/run_math500_100_7b_regression.sh`
  - `docs/task-b/artifacts/regression-100/run_math500_100_7b_hf_regression.sh`
- vLLM 尝试：
  - 命令后缀：`legacy_7b`
  - 日志：服务器 `/tmp/run_math500_100_7b_legacy.log`
  - 结果：失败，CUDA OOM。
  - 现象：vLLM 加载 7B 模型时显存已经接近满载，只剩约 `115 MiB`，再申请 `130 MiB` 失败。
- HF rollout 尝试：
  - 命令后缀：`legacy_7b_hf`
  - 日志：服务器 `/tmp/run_math500_100_7b_hf_legacy.log`
  - 结果：失败，CUDA OOM。
  - 现象：FSDP 初始化时需要再申请约 `14.19 GiB`，但 GPU 只剩约 `8.58 GiB`。
- 我理解的结论：
  - 不是模型没有下载，也不是脚本入口错了。
  - 当前 AlphaApollo/verl 回归链路会带来额外显存开销；7B 在单张 24GB 4090 上跑不起来。
  - 如果要做 7B 对比，建议换至少 `40GB` 显存机器，更稳的是 `48GB` 显存机器，例如 A100 40GB、A6000 48GB、L40S 48GB。
  - 后续换机器后可以直接复用这两个 7B 脚本，继续跑 `legacy` 和 `skill_legacy_aligned` 对比。
