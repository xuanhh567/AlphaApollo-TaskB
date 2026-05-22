# Structured Python Code Smoke Trajectory

> 这个样例用于证明 Task B 的结构化 tool call 主线已经能端到端工作：prompt 自动生成 `<tool_call>` 示例，模型动作使用 `<tool_call>`，env 返回 `<tool_response>`。

## 运行环境

```text
Python: /Users/wangjiaxuan/miniforge3/envs/alphaapollo/bin/python
Env: informal_math_training
Tool: python_code
RAG: disabled
```

## Question

```text
What is 1 + 1?
```

## Prompt Excerpt

```text
You may call exactly one tool by emitting exactly one <tool_call> block.

The JSON inside <tool_call> must be an object with "name" and "arguments".

Available tools:

1. python_code: Execute Python code for math reasoning and return stdout, stderr, return code, and status.
Parameters:
   - code (string, required): Python code to execute.
Examples:
   - compute arithmetic: <tool_call>{"name":"python_code","arguments":{"code":"print(1 + 1)"}}</tool_call>
```

## Assistant Action

```xml
<think>I will verify the arithmetic with Python.</think><tool_call>{"name":"python_code","arguments":{"code":"print(1 + 1)"}}</tool_call>
```

## Tool Response

```xml
<tool_response>{"result": "2\n", "stderr": "", "status": "success", "returncode": 0}</tool_response>
```

## Metadata

```json
[
  {
    "tool_calling": true,
    "tool_group": "InformalMathToolGroup",
    "tool_name": "python_code",
    "tool_input": {
      "code": "print(1 + 1)"
    },
    "tool_call_format": "structured",
    "data_source": "smoke_math",
    "score": 1
  }
]
```

## 结论

```text
structured <tool_call> -> dispatcher runtime executor -> InformalMathToolGroup -> <tool_response>
```

这条最小样例通过。
