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

# Python Code

Execute short Python snippets during informal math reasoning.
