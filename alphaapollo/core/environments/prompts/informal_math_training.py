# ------------- Training prompts -------------
from typing import Iterable

from alphaapollo.core.skills.prompt import render_skill_prompt_block
from alphaapollo.core.skills.schema import SkillSpec

# NOTE: initial training prompt for policy agent
# Memory: disabled 
# Python code: enabled
# Answer tag: <answer>...</answer>

INFORMAL_MATH_TEMPLATE_NO_TOOL = """
You are a math problem solver agent tasked with solving the given math problem step-by-step.

Your question: {question}

You should first conduct the reasoning process. This process MUST be enclosed within <think> </think> tags.
After completing your reasoning, provide the final answer only inside <answer>...</answer>, formatted in LaTeX, e.g., \\boxed{{...}}.
"""

INFORMAL_MATH_TEMPLATE_DYNAMIC_NO_HIS = """
You are a math problem solver agent tasked with solving the given math problem step-by-step.

Your question: {question}

Now it's your turn to respond to the current step.
You should first conduct the reasoning process. This process MUST be enclosed within <think> </think> tags.
After completing your reasoning, choose only one of the following actions:
1) Tool call: If a tool is helpful, use exactly one structured tool call.
{tool_instructions}
2) Answer: If you are ready to provide the self-contained solution, provide the answer only inside <answer>...</answer>, formatted in LaTeX, e.g., \\boxed{{...}}.
"""

INFORMAL_MATH_TEMPLATE_DYNAMIC_WITH_HIS = """
You are a math problem solver agent tasked with solving the given math problem step-by-step.

Your question: {question}

Prior to this step, you have already taken {step_count} step(s).
Below is the interaction history:
{memory_context}

Now it's your turn to respond to the current step.
You should first conduct the reasoning process. This process MUST be enclosed within <think> </think> tags.
After completing your reasoning, choose only one of the following actions:
1) Tool call: If a tool is helpful, use exactly one structured tool call.
{tool_instructions}
2) Answer: If you are ready to provide the self-contained solution, provide the answer only inside <answer>...</answer>, formatted in LaTeX, e.g., \\boxed{{...}}.
"""


INFORMAL_MATH_TEMPLATE_NO_HIS = """
You are a math problem solver agent tasked with solving the given math problem step-by-step.

Your question: {question}

Now it's your turn to respond to the current step.
You should first conduct the reasoning process. This process MUST be enclosed within <think> </think> tags. 
After completing your reasoning, choose only one of the following actions (do not perform both):
1) <python_code>...</python_code>: If computation/checking is helpful, emit exactly ONE <python_code>...</python_code> block with pure Python 3. Inspect the <tool_response> (stdout from your code). If it disagrees with your reasoning, correct yourself.
2) <answer>...</answer>: If you are ready to provide the self-contained solution, provide the answer only inside <answer>...</answer>, formatted in LaTeX, e.g., \\boxed{{...}}.
"""

INFORMAL_MATH_TEMPLATE_WITH_HIS = """
You are a math problem solver agent tasked with solving the given math problem step-by-step.

Your question: {question}

Prior to this step, you have already taken {step_count} step(s).
Below is the interaction history:
{memory_context}

Now it's your turn to respond to the current step.
You should first conduct the reasoning process. This process MUST be enclosed within <think> </think> tags. 
After completing your reasoning, choose only one of the following actions (do not perform both):
1) <python_code>...</python_code>: If computation/checking is helpful, emit exactly ONE <python_code>...</python_code> block with pure Python 3. Inspect the <tool_response> (stdout from your code). If it disagrees with your reasoning, correct yourself.
2) <answer>...</answer>: If you are ready to provide the self-contained solution, provide the answer only inside <answer>...</answer>, formatted in LaTeX, e.g., \\boxed{{...}}.
"""

INFORMAL_MATH_TEMPLATE_RAG_NO_HIS = """
You are a math problem solver agent tasked with solving the given math problem step-by-step.

Your question: {question}

Now it's your turn to respond to the current step.
You should first conduct the reasoning process. This process MUST be enclosed within <think> </think> tags. 
After completing your reasoning, choose only one of the following actions (do not perform multiple actions at the same time):
1) <python_code>...</python_code>: If computation/checking is helpful, emit exactly ONE <python_code>...</python_code> block with pure Python 3. Inspect the <tool_response> (stdout from your code). If it disagrees with your reasoning, correct yourself.
2) <local_rag>...</local_rag>: You have access to a RAG System tool to search for documentation or examples (Supported repos: sympy, scipy, numpy, math, cmath, fractions, itertools). Emit exactly ONE <local_rag>...</local_rag> block with a JSON object. Inspect the returned <tool_response> (RAG result). If it disagrees with your reasoning, correct yourself. For example: <local_rag>{{"repo_name": "sympy", "query": "your query here"}}</local_rag>.
3) <answer>...</answer>: If you are ready to provide the self-contained solution, provide the answer only inside <answer>...</answer>, formatted in LaTeX, e.g., \\boxed{{...}}.
"""

INFORMAL_MATH_TEMPLATE_RAG_WITH_HIS = """
You are a math problem solver agent tasked with solving the given math problem step-by-step.

Your question: {question}

Prior to this step, you have already taken {step_count} step(s).
Below is the interaction history:
{memory_context}

Now it's your turn to respond to the current step.
You should first conduct the reasoning process. This process MUST be enclosed within <think> </think> tags. 
After completing your reasoning, choose only one of the following actions (do not perform multiple actions at the same time):
1) <python_code>...</python_code>: If computation/checking is helpful, emit exactly ONE <python_code>...</python_code> block with pure Python 3. Inspect the <tool_response> (stdout from your code). If it disagrees with your reasoning, correct yourself.
2) <local_rag>...</local_rag>: You have access to a RAG System tool to search for documentation or examples (Supported repos: sympy, scipy, numpy, math, cmath, fractions, itertools). Emit exactly ONE <local_rag>...</local_rag> block with a JSON object. Inspect the returned <tool_response> (RAG result). If it disagrees with your reasoning, correct yourself. For example: <local_rag>{{"repo_name": "sympy", "query": "your query here"}}</local_rag>.
3) <answer>...</answer>: If you are ready to provide the self-contained solution, provide the answer only inside <answer>...</answer>, formatted in LaTeX, e.g., \\boxed{{...}}.
"""

INFORMAL_MATH_TEMPLATE_RAG_ONLY_NO_HIS = """
You are a math problem solver agent tasked with solving the given math problem step-by-step.

Your question: {question}

Now it's your turn to respond to the current step.
You should first conduct the reasoning process. This process MUST be enclosed within <think> </think> tags. 
After completing your reasoning, choose only one of the following actions (do not perform both):
1) <local_rag>...</local_rag>: You have access to a RAG System tool to search for documentation or examples (Supported repos: sympy, scipy, numpy, math, cmath, fractions, itertools). Emit exactly ONE <local_rag>...</local_rag> block with a JSON object. Inspect the returned <tool_response> (RAG result). If it disagrees with your reasoning, correct yourself. For example: <local_rag>{{"repo_name": "sympy", "query": "your query here"}}</local_rag>.
2) <answer>...</answer>: If you are ready to provide the self-contained solution, provide the answer only inside <answer>...</answer>, formatted in LaTeX, e.g., \\boxed{{...}}.
"""

INFORMAL_MATH_TEMPLATE_RAG_ONLY_WITH_HIS = """
You are a math problem solver agent tasked with solving the given math problem step-by-step.

Your question: {question}

Prior to this step, you have already taken {step_count} step(s).
Below is the interaction history:
{memory_context}

Now it's your turn to respond to the current step.
You should first conduct the reasoning process. This process MUST be enclosed within <think> </think> tags. 
After completing your reasoning, choose only one of the following actions (do not perform both):
1) <local_rag>...</local_rag>: You have access to a RAG System tool to search for documentation or examples (Supported repos: sympy, scipy, numpy, math, cmath, fractions, itertools). Emit exactly ONE <local_rag>...</local_rag> block with a JSON object. Inspect the returned <tool_response> (RAG result). If it disagrees with your reasoning, correct yourself. For example: <local_rag>{{"repo_name": "sympy", "query": "your query here"}}</local_rag>.
2) <answer>...</answer>: If you are ready to provide the self-contained solution, provide the answer only inside <answer>...</answer>, formatted in LaTeX, e.g., \\boxed{{...}}.
"""

def get_policy_training_prompt(use_history=False, max_steps=8, tool_config=None, tool_specs: Iterable[SkillSpec] | None = None) -> str:
   """
   Get the policy training prompt based on tool configuration.
   
   Args:
       use_history: Whether to include history in the prompt
       max_steps: Maximum number of steps allowed
       tool_specs: Optional enabled skills used to auto-generate structured
                   tool-call instructions.
       tool_config: Dict with tool enable flags. 
                    Supported keys: "enable_python_code", "enable_local_rag"
                    Defaults to {"enable_python_code": True, "enable_local_rag": True}
   
   Example:
       tool_config = {"enable_python_code": True, "enable_local_rag": False}
       prompt = get_policy_training_prompt(use_history=True, tool_config=tool_config)
   """
   if tool_specs is not None:
       specs = list(tool_specs)
       if max_steps == 1 or not specs:
           return INFORMAL_MATH_TEMPLATE_NO_TOOL
       tool_instructions = render_skill_prompt_block(specs, escape_braces=True)
       template = INFORMAL_MATH_TEMPLATE_DYNAMIC_WITH_HIS if use_history else INFORMAL_MATH_TEMPLATE_DYNAMIC_NO_HIS
       return template.replace("{tool_instructions}", tool_instructions)

   if tool_config is None:
       tool_config = {}
   
   enable_python_code = tool_config.get("enable_python_code", True)
   enable_local_rag = tool_config.get("enable_local_rag", True)

   if max_steps == 1:
      return INFORMAL_MATH_TEMPLATE_NO_TOOL

   if enable_local_rag and enable_python_code:
        return INFORMAL_MATH_TEMPLATE_RAG_WITH_HIS if use_history else INFORMAL_MATH_TEMPLATE_RAG_NO_HIS
   
   if enable_local_rag and not enable_python_code:
       return INFORMAL_MATH_TEMPLATE_RAG_ONLY_WITH_HIS if use_history else INFORMAL_MATH_TEMPLATE_RAG_ONLY_NO_HIS

   return INFORMAL_MATH_TEMPLATE_WITH_HIS  if use_history else INFORMAL_MATH_TEMPLATE_NO_HIS
