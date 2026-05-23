# Legacy vs Skill Legacy 差异分析

这份报告比较固定 100 题中旧 `<python_code>` baseline 和 `skill_legacy` 的结果。

## 总览

| 类型 | 数量 |
|---|---:|
| legacy 对，skill_legacy 也对 | 42 |
| legacy 对，skill_legacy 错 | 16 |
| legacy 错，skill_legacy 对 | 6 |
| legacy 错，skill_legacy 也错 | 36 |

## 行为统计

| 版本 | answer 数 | answer 含 boxed | assistant 含 python_code | history 含 tool_response | 无动作 |
|---|---:|---:|---:|---:|---:|
| legacy | 90 | 80 | 8 | 100 | 6 |
| skill_legacy | 73 | 60 | 21 | 100 | 11 |

## 读数结论

最明显的差异不是 `skill_legacy` 不会调用工具，而是它更容易在该交最终答案的时候继续调用 `<python_code>`：

```text
legacy assistant 含 python_code: 8
skill_legacy assistant 含 python_code: 21
```

在 `legacy 对，skill_legacy 错` 的 16 个样本里，有不少 `skill_legacy` 的最后动作是 `<python_code>`，没有及时输出 `<answer>`。这和 prompt 差异吻合：旧 legacy prompt 没有内联 Python 示例，而 `skill_legacy` 自动生成的 prompt 里原来多了一句：

```text
Example: <python_code>print(1 + 1)</python_code>
```

对 3B 模型来说，这个例子可能会提高“继续写代码”的倾向，尤其是在第二步已经有 `<tool_response>` 的情况下。

## 本次针对性改动

为了让 `skill_legacy` 更贴近原始 legacy 行为，当前代码做了两个小改动：

```text
1. python_code 的 legacy prompt 不再附带内联 Example。
2. SKILL.md 自动生成 legacy prompt 时，工具顺序优先保持 python_code -> local_rag。
```

改动后，`skill_legacy_adapter_python_only_no_history` 和 `legacy_python_only_no_history` 的核心文本已经基本一致，只差旧模板里一个历史遗留的行尾空格。

## 最需要看的样本：legacy 对，skill_legacy 错

| row | dataset index | ground truth | legacy 行为 | skill_legacy 行为 | skill_legacy 输出摘要 |
|---:|---:|---|---|---|---|
| 2 | 20 | `6+9i` | answer, boxed, tool_response | python_code, tool_response | <think> Let's verify the step-by-step calculation using Python code. We'll perform the operations \(6 \cdot (1 + 2i)\) and then subtract \(3i\). The result should be \(6 + 9i\). </think> <python_code> # Define the com... |
| 6 | 41 | `17` | answer, boxed, tool_response | answer, boxed, tool_response | <think>Given the midpoint of diagonal \(AC\) is \((6.0, 3.5)\), we can use this information to find the coordinates of the fourth vertex \(D(x, y)\). The midpoint of \(BD\) must also be \((6.0, 3.5)\). We can set up t... |
| 9 | 48 | `\frac{3}{2}` | answer, boxed, tool_response | answer, tool_response | <think>To solve the problem, we need to find the power \( n \) such that \( 4^n = 8 \). We can express both 4 and 8 as powers of 2: - \( 4 = 2^2 \) - \( 8 = 2^3 \) So, the equation \( 4^n = 8 \) can be rewritten as: \... |
| 11 | 51 | `x^5 - x^4 + x^3 - x^2 + x - 1` | answer, boxed, python_code, tool_response | python_code, tool_response | <think> Let's perform the polynomial long division step by step to find the quotient when \(x^6 - 3\) is divided by \(x + 1\). 1. Divide the leading term of the dividend \(x^6\) by the leading term of the divisor \(x\... |
| 15 | 75 | `\frac{11}{36}` | answer, boxed, tool_response | answer, tool_response | <think>To solve this problem, we need to determine the probability that the product of the numbers on two 6-sided dice is a multiple of 5. For the product to be a multiple of 5, at least one of the dice must show a 5,... |
| 23 | 132 | `4` | answer, boxed, tool_response | answer, boxed, tool_response | <think> From the computation in the previous step, we found that the common positive factors of 14 and 42 are 1, 2, and 7. Therefore, there are 3 possible numbers that Rick and Steve could be thinking of. Let's list t... |
| 25 | 144 | `(15,-29)` | answer, boxed, tool_response | python_code, tool_response | <think>Now that we have the parametric equations for \(x\) and \(y\), let's substitute \(t = 2\) into these equations to find the coordinates of the point on the curve at that value of \(t\). For \(x\): \[x = t^3 + 7\... |
| 35 | 181 | `\frac{\sqrt{3}}{3}` | answer, boxed, tool_response | answer, tool_response | <think> First, let's simplify the expression inside the square root step by step. We start with the innermost expression: \[ \sqrt{\frac{1}{729}} \] The square root of \(\frac{1}{729}\) is: \[ \sqrt{\frac{1}{729}} = \... |
| 41 | 222 | `54` | answer, boxed, tool_response | python_code, tool_response | <think> Let's go through the steps again to ensure the reasoning is correct: 1. **Understand the given information:** - The area of \(\triangle ABC\) is 6 square centimeters. - \(\overline{AB} \parallel \overline{DE}\... |
| 44 | 241 | `17` | answer, boxed, tool_response | answer, boxed, python_code, tool_response | <think>First, let's simplify the derivative of the function \(f(x)\) to find the critical points. The derivative \(f'(x)\) is given by: \[ f'(x) = 18.0x(0.0555555555555556x^2 - 1) + 2x \] We can simplify this expressi... |
| 53 | 272 | `1030` | answer, boxed, tool_response | python_code, tool_response | <think> Given that the GCD of 1331 and 9999 is 11, we can simplify the fraction \(\frac{1331}{9999}\) by dividing both the numerator and the denominator by 11. \[ \frac{1331 \div 11}{9999 \div 11} = \frac{121}{909} \]... |
| 64 | 320 | `-\frac{24}{25}` | answer, boxed, tool_response | answer, tool_response | To solve this problem, let's first analyze the given information and the diagram. Given: - \(\sin \angle RPQ = \frac{7}{25}\) From the diagram, we can see that \(\angle RPQ\) is an angle in a right triangle with \(PQ\... |
| 68 | 360 | `\frac{7}{4}` | answer, boxed, tool_response | answer, boxed, python_code, tool_response | <think>From the graph, we can see that the line passes through the points \((-5, 4)\) and \((-1, 3)\). The direction vector \(\begin{pmatrix} -7 \\ b \end{pmatrix}\) should represent the slope of the line. The slope \... |
| 77 | 411 | `60` | answer, boxed, tool_response | python_code, tool_response | <think>From the calculation, we have the number of witches as 6 and the number of sorcerers as 10. Since each witch shakes hands with each sorcerer, the total number of handshakes is the product of these two numbers. ... |
| 92 | 465 | `121` | answer, boxed, tool_response | answer, tool_response | <think>To determine the positive integers with exactly three positive divisors, we need to understand the structure of such numbers. A number has exactly three positive divisors if and only if it is the square of a pr... |
| 99 | 489 | `15` | answer, boxed, tool_response | python_code, tool_response | <think> To confirm the reasoning, let's re-evaluate the function \(f(x) = x - 2p\) within the interval \(p \leq x \leq 15\). The function is linear and increasing, so the minimum value will indeed occur at the smalles... |

## 反向样本：legacy 错，skill_legacy 对

| row | dataset index | ground truth | legacy 行为 | skill_legacy 行为 | skill_legacy 输出摘要 |
|---:|---:|---|---|---|---|
| 0 | 0 | `\left( 3, \frac{\pi}{2} \right)` | answer, boxed, tool_response | answer, boxed, tool_response | <think> From the computation provided, we have \( r = 3.0 \) and \( \theta = 90.0 \) degrees. This means the polar coordinates for the point \((0, 3)\) are \((3, \frac{\pi}{2})\). The angle \(\theta = 90.0\) degrees i... |
| 13 | 71 | `2516_8` | answer, boxed, tool_response | answer, boxed, tool_response | <think> Let's verify the conversion using the provided Python code. The code converts the binary number \(10101001110_2\) to its octal equivalent and outputs the result. The output from the code is "2516\n". This mean... |
| 34 | 170 | `1736` | answer, boxed, tool_response | answer, boxed, tool_response | <think> The Python code executed and returned a result of approximately 1736. Given the precision of floating-point arithmetic, we can reasonably conclude that the exact product of the \(y\)-coordinates is 1736. This ... |
| 37 | 197 | `6` | answer, boxed, tool_response | answer, boxed, tool_response | <think> Let's go through the reasoning step-by-step: 1. We have the prime factorization of \(10!\): \[10! = 2^8 \times 3^4 \times 5^2 \times 7\] 2. For \(x^3\) to be a factor of \(10!\), the exponents of the prime fac... |
| 61 | 312 | `(5,\infty)` | answer, tool_response | answer, boxed, python_code, tool_response | <think>Based on the previous reasoning and the verification using SymPy, the solution to the inequality \(\frac{1}{x - 5} > 0\) is indeed \(x \in (5, \infty)\). This means \(x\) can take any value greater than 5 but n... |
| 67 | 350 | `4` | answer, boxed, tool_response | answer, boxed, tool_response | <think>To find the units digit of \(18^6\), we only need to consider the units digit of the base number, which is 8. Therefore, we need to determine the units digit of \(8^6\). Let's observe the pattern in the units d... |
