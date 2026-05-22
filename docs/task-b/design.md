# Task B 总体设计地图

> 这份文件只做“总览”。每个阶段的详细理解、设计和验证，单独放到对应的 phase 文档里。

## 1. Task B 要解决什么

当前工具调用链大致是：

```text
模型输出特定标签
-> projection.py 用正则解析
-> env.py 用 if/elif 判断工具名
-> manager.py 执行对应工具
-> tool_response 返回模型
```

Task B 想把它改成：

```text
每个工具都有自己的 SKILL.md
-> registry 自动加载工具说明
-> 模型输出统一 <tool_call>{...}</tool_call>
-> dispatcher 根据工具名执行
-> tool_response 返回模型
```

一句话理解：**把写死在代码里的工具，改成可注册、可校验、可扩展的 Skill 系统。**

## 2. 分阶段文档

| 阶段 | 文档 | 当前状态 | 主要问题 |
|---|---|---|---|
| Phase 1 | `phase-1-skill-md-spec.md` | 已完成 | `SKILL.md` 怎么写，parser 怎么读 |
| Phase 2 | `phase-2-registry.md` | 设计中 | 多个 skill 怎么被扫描、注册、启用 |
| Phase 3 | `phase-3-tool-call.md` | 未开始 | `<tool_call>` 怎么解析和校验 |
| Phase 4 | `phase-4-dispatcher.md` | 未开始 | dispatcher 怎么执行真正的工具 |
| Phase 5 | `phase-5-prompt.md` | 未开始 | prompt 怎么从 registry 自动生成 |
| Phase 6 | `phase-6-regression.md` | 未开始 | 怎么证明迁移前后行为没有明显变坏 |

## 3. 关键模块关系

```text
SKILL.md
  |
  v
loader.py
  |
  v
SkillSpec
  |
  v
registry.py
  |
  +--> prompt generator
  |
  +--> dispatcher.py
            |
            v
        real tool function
```

新手理解版：

- `SKILL.md`：工具说明书。
- `loader.py`：读懂一本工具说明书。
- `SkillSpec`：说明书读完后得到的标准内部数据。
- `registry.py`：工具登记表。
- `prompt generator`：把工具登记表转换成给模型看的说明。
- `dispatcher.py`：根据模型点名的工具，找到并执行它。

## 4. 当前已经完成

Phase 1 已经完成：

- 设计了 `SKILL.md` 的最小字段规范。
- 实现了 `SkillSpec` 等内部数据结构。
- 实现了 `loader.py`，可以读取和校验 `SKILL.md`。
- 新增了 `tests/test_skill_loader.py` 验证合法和非法输入。

详细内容见：

```text
docs/task-b/phase-1-skill-md-spec.md
```

## 5. 下一步

下一步进入 Phase 2：registry。

Phase 2 暂时先不急着接 `env.py`，先完成 registry 设计和计划：

1. skill 文件夹应该从哪里扫描？
2. 如果两个 skill 重名，registry 怎么报错？
3. 配置里只启用 `python_code` 和 `local_rag` 时，registry 怎么过滤？
