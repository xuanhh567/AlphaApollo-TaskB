# Task B Prompt 展示

这个文件把当前代码能生成的几类 prompt 直接展开，方便对比。

- 示例题目：`Evaluate $(1+2i)6-3i$.`
- `legacy`: Task A 风格旧手写 prompt。
- `structured_skill`: SKILL.md 驱动的 `<tool_call>{JSON}</tool_call>` prompt。
- `skill_legacy_adapter`: SKILL.md 驱动的 `<python_code>` / `<local_rag>` prompt。

## legacy_no_history

旧手写 baseline prompt。模型看到 <python_code> 标签；不经过 SKILL.md 自动生成说明。

- 字符数：`818`
- 行数：`10`

```text
You are a math problem solver agent tasked with solving the given math problem step-by-step.

Your question: Evaluate $(1+2i)6-3i$.

Now it's your turn to respond to the current step.
You should first conduct the reasoning process. This process MUST be enclosed within <think> </think> tags. 
After completing your reasoning, choose only one of the following actions (do not perform both):
1) <python_code>...</python_code>: If computation/checking is helpful, emit exactly ONE <python_code>...</python_code> block with pure Python 3. Inspect the <tool_response> (stdout from your code). If it disagrees with your reasoning, correct yourself.
2) <answer>...</answer>: If you are ready to provide the self-contained solution, provide the answer only inside <answer>...</answer>, formatted in LaTeX, e.g., \boxed{...}.
```

## legacy_with_history

旧手写 baseline prompt。模型看到 <python_code> 标签；不经过 SKILL.md 自动生成说明。

- 字符数：`1081`
- 行数：`16`

```text
You are a math problem solver agent tasked with solving the given math problem step-by-step.

Your question: Evaluate $(1+2i)6-3i$.

Prior to this step, you have already taken 1 step(s).
Below is the interaction history:
<think>I will use Python to check the arithmetic.</think>
<python_code>print((1+2j)*6-3j)</python_code>
<tool_response>{"result":"(6+9j)","status":"success"}</tool_response>

Now it's your turn to respond to the current step.
You should first conduct the reasoning process. This process MUST be enclosed within <think> </think> tags. 
After completing your reasoning, choose only one of the following actions (do not perform both):
1) <python_code>...</python_code>: If computation/checking is helpful, emit exactly ONE <python_code>...</python_code> block with pure Python 3. Inspect the <tool_response> (stdout from your code). If it disagrees with your reasoning, correct yourself.
2) <answer>...</answer>: If you are ready to provide the self-contained solution, provide the answer only inside <answer>...</answer>, formatted in LaTeX, e.g., \boxed{...}.
```

## structured_skill_python_only_no_history

SKILL.md 自动生成的结构化 <tool_call> JSON prompt。

- 字符数：`1398`
- 行数：`20`

```text
You are a math problem solver agent tasked with solving the given math problem step-by-step.

Your question: Evaluate $(1+2i)6-3i$.

Now it's your turn to respond to the current step.
You should first conduct the reasoning process. This process MUST be enclosed within <think> </think> tags.
After completing your reasoning, choose only one of the following actions (do not perform both):
1) Tool call: If computation/checking is helpful, emit exactly ONE complete <tool_call> block. Put pure Python 3 code in arguments.code. Inspect the <tool_response> (stdout from your code). If it disagrees with your reasoning, correct yourself.
2) <answer>...</answer>: If you are ready to provide the self-contained solution, provide the answer only inside <answer>...</answer>, formatted in LaTeX, e.g., \boxed{...}.
Tool-call format adapter:
Bad: <tool_call>python_code {"code":"print(1+1)"}</tool_call>
Bad: <tool_call>...</tool_call>
Good: <tool_call>{"name":"python_code","arguments":{"code":"print(1+1)"}}</tool_call>
Do not write YAML, duplicate <tool_call>, placeholder dots, or text before the JSON inside <tool_call>.
Tool schemas:

1. python_code: Execute Python code for math reasoning and return stdout, stderr, return code, and status.
   arguments: code (string, required): Python code to execute.
   example: <tool_call>{"name":"python_code","arguments":{"code":"print(1 + 1)"}}</tool_call>
```

## structured_skill_python_only_with_history

SKILL.md 自动生成的结构化 <tool_call> JSON prompt。

- 字符数：`1661`
- 行数：`26`

```text
You are a math problem solver agent tasked with solving the given math problem step-by-step.

Your question: Evaluate $(1+2i)6-3i$.

Prior to this step, you have already taken 1 step(s).
Below is the interaction history:
<think>I will use Python to check the arithmetic.</think>
<python_code>print((1+2j)*6-3j)</python_code>
<tool_response>{"result":"(6+9j)","status":"success"}</tool_response>

Now it's your turn to respond to the current step.
You should first conduct the reasoning process. This process MUST be enclosed within <think> </think> tags.
After completing your reasoning, choose only one of the following actions (do not perform both):
1) Tool call: If computation/checking is helpful, emit exactly ONE complete <tool_call> block. Put pure Python 3 code in arguments.code. Inspect the <tool_response> (stdout from your code). If it disagrees with your reasoning, correct yourself.
2) <answer>...</answer>: If you are ready to provide the self-contained solution, provide the answer only inside <answer>...</answer>, formatted in LaTeX, e.g., \boxed{...}.
Tool-call format adapter:
Bad: <tool_call>python_code {"code":"print(1+1)"}</tool_call>
Bad: <tool_call>...</tool_call>
Good: <tool_call>{"name":"python_code","arguments":{"code":"print(1+1)"}}</tool_call>
Do not write YAML, duplicate <tool_call>, placeholder dots, or text before the JSON inside <tool_call>.
Tool schemas:

1. python_code: Execute Python code for math reasoning and return stdout, stderr, return code, and status.
   arguments: code (string, required): Python code to execute.
   example: <tool_call>{"name":"python_code","arguments":{"code":"print(1 + 1)"}}</tool_call>
```

## structured_skill_python_rag_no_history

SKILL.md 自动生成的结构化 <tool_call> JSON prompt。

- 字符数：`1930`
- 行数：`24`

```text
You are a math problem solver agent tasked with solving the given math problem step-by-step.

Your question: Evaluate $(1+2i)6-3i$.

Now it's your turn to respond to the current step.
You should first conduct the reasoning process. This process MUST be enclosed within <think> </think> tags.
After completing your reasoning, choose only one of the following actions (do not perform both):
1) Tool call: If computation/checking is helpful, emit exactly ONE complete <tool_call> block. Put pure Python 3 code in arguments.code. Inspect the <tool_response> (stdout from your code). If it disagrees with your reasoning, correct yourself.
2) <answer>...</answer>: If you are ready to provide the self-contained solution, provide the answer only inside <answer>...</answer>, formatted in LaTeX, e.g., \boxed{...}.
Tool-call format adapter:
Bad: <tool_call>python_code {"code":"print(1+1)"}</tool_call>
Bad: <tool_call>...</tool_call>
Good: <tool_call>{"name":"python_code","arguments":{"code":"print(1+1)"}}</tool_call>
Do not write YAML, duplicate <tool_call>, placeholder dots, or text before the JSON inside <tool_call>.
Tool schemas:

1. local_rag: Retrieve documentation snippets from local math and scientific Python package knowledge bases.
   arguments: repo_name (string, required): Repository name, such as sympy, scipy, numpy, math, cmath, fractions, or itertools.; query (string, required): Natural-language retrieval query.; top_k (integer, optional, default=3): Number of retrieved chunks per query.
   example: <tool_call>{"name":"local_rag","arguments":{"repo_name":"sympy","query":"How to solve polynomial equations with sympy?","top_k":3}}</tool_call>

2. python_code: Execute Python code for math reasoning and return stdout, stderr, return code, and status.
   arguments: code (string, required): Python code to execute.
   example: <tool_call>{"name":"python_code","arguments":{"code":"print(1 + 1)"}}</tool_call>
```

## structured_skill_python_rag_with_history

SKILL.md 自动生成的结构化 <tool_call> JSON prompt。

- 字符数：`2193`
- 行数：`30`

```text
You are a math problem solver agent tasked with solving the given math problem step-by-step.

Your question: Evaluate $(1+2i)6-3i$.

Prior to this step, you have already taken 1 step(s).
Below is the interaction history:
<think>I will use Python to check the arithmetic.</think>
<python_code>print((1+2j)*6-3j)</python_code>
<tool_response>{"result":"(6+9j)","status":"success"}</tool_response>

Now it's your turn to respond to the current step.
You should first conduct the reasoning process. This process MUST be enclosed within <think> </think> tags.
After completing your reasoning, choose only one of the following actions (do not perform both):
1) Tool call: If computation/checking is helpful, emit exactly ONE complete <tool_call> block. Put pure Python 3 code in arguments.code. Inspect the <tool_response> (stdout from your code). If it disagrees with your reasoning, correct yourself.
2) <answer>...</answer>: If you are ready to provide the self-contained solution, provide the answer only inside <answer>...</answer>, formatted in LaTeX, e.g., \boxed{...}.
Tool-call format adapter:
Bad: <tool_call>python_code {"code":"print(1+1)"}</tool_call>
Bad: <tool_call>...</tool_call>
Good: <tool_call>{"name":"python_code","arguments":{"code":"print(1+1)"}}</tool_call>
Do not write YAML, duplicate <tool_call>, placeholder dots, or text before the JSON inside <tool_call>.
Tool schemas:

1. local_rag: Retrieve documentation snippets from local math and scientific Python package knowledge bases.
   arguments: repo_name (string, required): Repository name, such as sympy, scipy, numpy, math, cmath, fractions, or itertools.; query (string, required): Natural-language retrieval query.; top_k (integer, optional, default=3): Number of retrieved chunks per query.
   example: <tool_call>{"name":"local_rag","arguments":{"repo_name":"sympy","query":"How to solve polynomial equations with sympy?","top_k":3}}</tool_call>

2. python_code: Execute Python code for math reasoning and return stdout, stderr, return code, and status.
   arguments: code (string, required): Python code to execute.
   example: <tool_call>{"name":"python_code","arguments":{"code":"print(1 + 1)"}}</tool_call>
```

## skill_legacy_adapter_python_only_no_history

SKILL.md 自动生成的 legacy 标签 prompt；模型看到旧标签，内部仍转成 ToolCall。

- 字符数：`895`
- 行数：`10`

```text
You are a math problem solver agent tasked with solving the given math problem step-by-step.

Your question: Evaluate $(1+2i)6-3i$.

Now it's your turn to respond to the current step.
You should first conduct the reasoning process. This process MUST be enclosed within <think> </think> tags.
After completing your reasoning, choose only one of the following actions (do not perform multiple actions at the same time):
1) <python_code>...</python_code>: If computation/checking is helpful, emit exactly ONE <python_code>...</python_code> block with pure Python 3. Inspect the <tool_response> (stdout from your code). If it disagrees with your reasoning, correct yourself. Example: <python_code>print(1 + 1)</python_code>
2) <answer>...</answer>: If you are ready to provide the self-contained solution, provide the answer only inside <answer>...</answer>, formatted in LaTeX, e.g., \boxed{...}.
```

## skill_legacy_adapter_python_only_with_history

SKILL.md 自动生成的 legacy 标签 prompt；模型看到旧标签，内部仍转成 ToolCall。

- 字符数：`1158`
- 行数：`16`

```text
You are a math problem solver agent tasked with solving the given math problem step-by-step.

Your question: Evaluate $(1+2i)6-3i$.

Prior to this step, you have already taken 1 step(s).
Below is the interaction history:
<think>I will use Python to check the arithmetic.</think>
<python_code>print((1+2j)*6-3j)</python_code>
<tool_response>{"result":"(6+9j)","status":"success"}</tool_response>

Now it's your turn to respond to the current step.
You should first conduct the reasoning process. This process MUST be enclosed within <think> </think> tags.
After completing your reasoning, choose only one of the following actions (do not perform multiple actions at the same time):
1) <python_code>...</python_code>: If computation/checking is helpful, emit exactly ONE <python_code>...</python_code> block with pure Python 3. Inspect the <tool_response> (stdout from your code). If it disagrees with your reasoning, correct yourself. Example: <python_code>print(1 + 1)</python_code>
2) <answer>...</answer>: If you are ready to provide the self-contained solution, provide the answer only inside <answer>...</answer>, formatted in LaTeX, e.g., \boxed{...}.
```

## skill_legacy_adapter_python_rag_no_history

SKILL.md 自动生成的 legacy 标签 prompt；模型看到旧标签，内部仍转成 ToolCall。

- 字符数：`1246`
- 行数：`11`

```text
You are a math problem solver agent tasked with solving the given math problem step-by-step.

Your question: Evaluate $(1+2i)6-3i$.

Now it's your turn to respond to the current step.
You should first conduct the reasoning process. This process MUST be enclosed within <think> </think> tags.
After completing your reasoning, choose only one of the following actions (do not perform multiple actions at the same time):
1) <local_rag>...</local_rag>: Retrieve documentation snippets from local math and scientific Python package knowledge bases. Emit exactly ONE <local_rag>...</local_rag> block containing a JSON object with repo_name, query, top_k. Example: <local_rag>{"repo_name":"sympy","query":"How to solve polynomial equations with sympy?","top_k":3}</local_rag>
2) <python_code>...</python_code>: If computation/checking is helpful, emit exactly ONE <python_code>...</python_code> block with pure Python 3. Inspect the <tool_response> (stdout from your code). If it disagrees with your reasoning, correct yourself. Example: <python_code>print(1 + 1)</python_code>
3) <answer>...</answer>: If you are ready to provide the self-contained solution, provide the answer only inside <answer>...</answer>, formatted in LaTeX, e.g., \boxed{...}.
```

## skill_legacy_adapter_python_rag_with_history

SKILL.md 自动生成的 legacy 标签 prompt；模型看到旧标签，内部仍转成 ToolCall。

- 字符数：`1509`
- 行数：`17`

```text
You are a math problem solver agent tasked with solving the given math problem step-by-step.

Your question: Evaluate $(1+2i)6-3i$.

Prior to this step, you have already taken 1 step(s).
Below is the interaction history:
<think>I will use Python to check the arithmetic.</think>
<python_code>print((1+2j)*6-3j)</python_code>
<tool_response>{"result":"(6+9j)","status":"success"}</tool_response>

Now it's your turn to respond to the current step.
You should first conduct the reasoning process. This process MUST be enclosed within <think> </think> tags.
After completing your reasoning, choose only one of the following actions (do not perform multiple actions at the same time):
1) <local_rag>...</local_rag>: Retrieve documentation snippets from local math and scientific Python package knowledge bases. Emit exactly ONE <local_rag>...</local_rag> block containing a JSON object with repo_name, query, top_k. Example: <local_rag>{"repo_name":"sympy","query":"How to solve polynomial equations with sympy?","top_k":3}</local_rag>
2) <python_code>...</python_code>: If computation/checking is helpful, emit exactly ONE <python_code>...</python_code> block with pure Python 3. Inspect the <tool_response> (stdout from your code). If it disagrees with your reasoning, correct yourself. Example: <python_code>print(1 + 1)</python_code>
3) <answer>...</answer>: If you are ready to provide the self-contained solution, provide the answer only inside <answer>...</answer>, formatted in LaTeX, e.g., \boxed{...}.
```
