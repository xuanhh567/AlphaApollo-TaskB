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
  - name: verify complex arithmetic
    arguments:
      code: |
        z = (1 + 2j) * 6 - 3j
        print(f"{z.real:g}+{z.imag:g}i")
  - name: count circular arrangements
    arguments:
      code: |
        from math import factorial
        print(factorial(5) * factorial(3))
  - name: compute exact probability
    arguments:
      code: |
        from fractions import Fraction
        print(Fraction(36 - 25, 36))
---

# Python Code

Execute short Python snippets during informal math reasoning.
