# Task B 实验记录

> 这里记录 Task B 的验证命令、trajectory 样例、回归计划和当前状态。

## 1. Smoke Test：Structured Python Code

### 目的

验证结构化 tool call 主线是否能端到端工作：

```text
auto-generated prompt
-> structured <tool_call>
-> dispatcher runtime executor
-> InformalMathToolGroup
-> <tool_response>
```

### 样例文件

```text
docs/task-b/trajectories/structured-python-code-smoke.md
```

### 结果

```text
Status: passed
Tool: python_code
Action format: structured <tool_call>
Observation: <tool_response>{"result": "2\n", "stderr": "", "status": "success", "returncode": 0}</tool_response>
Metadata: tool_call_format = structured, score = 1
```

## 2. 单元测试

当前已通过：

```bash
python tests/test_skill_prompt_renderer.py
python tests/test_informal_math_skill_bridge.py
python tests/test_skill_dispatcher.py
python tests/test_skill_argument_validation.py
python tests/test_tool_call_parser.py
python tests/test_skill_registry.py
python tests/test_skill_loader.py
```

编译检查：

```bash
python -m py_compile alphaapollo/core/skills/schema.py alphaapollo/core/skills/loader.py alphaapollo/core/skills/registry.py alphaapollo/core/skills/call_parser.py alphaapollo/core/skills/validation.py alphaapollo/core/skills/dispatcher.py alphaapollo/core/skills/prompt.py alphaapollo/core/skills/__init__.py alphaapollo/core/environments/informal_math_training/skill_bridge.py alphaapollo/core/environments/informal_math_training/env.py alphaapollo/core/environments/prompts/informal_math_training.py alphaapollo/core/environments/env_manager.py
```

## 3. MATH-500 回归状态

| 项目 | 数据集 | 状态 | 结果 |
|---|---|---|---|
| Task A baseline | MATH-500 | Pending | 未运行 |
| Task B skill version | MATH-500 | Pending | 未运行 |
| 指标差值 | MATH-500 | Pending | 未计算 |

当前未运行原因：

```text
MATH-500 回归需要模型服务、GPU 资源和较长运行时间。
```

建议后续至少固定随机种子抽样 100 题，再视资源跑全量 500 题。

## 4. 建议回归入口

Task B 主线配置：

```text
examples/configs/rl_informal_math_tool.yaml
```

需要重点确认：

```text
env.env_name=informal_math_training
env.max_steps=4
env.informal_math.enable_python_code=true
env.informal_math.enable_local_rag=false
```

后续补充：

```text
Task A baseline 命令
Task B skill version 命令
运行日志路径
评估 JSON 路径
最终 accuracy / pass rate
```
