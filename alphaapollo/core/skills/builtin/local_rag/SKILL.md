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
legacy_calls:
  - tag: local_rag
    input_format: json
examples:
  - name: query sympy solving
    arguments:
      repo_name: sympy
      query: How to solve polynomial equations with sympy?
      top_k: 3
---

# Local RAG

Retrieve local documentation snippets for math-related Python packages.
