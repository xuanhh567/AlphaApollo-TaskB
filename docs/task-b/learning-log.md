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

## 7. 下一步

下一步进入 Phase 2 / B2，不急着接入 `env.py`，先设计 registry：

```text
目标：能扫描多个 skill 目录，并把合法 SkillSpec 注册成可查询的工具表。
```

完成 registry 后，再继续结构化 tool_call 和 dispatcher。
