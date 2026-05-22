# Task B 服务器配置与环境选择

这份文档记录 Task B 后续跑测试、回归实验时使用的服务器和 conda 环境。目标是让以后重新接手时，能快速知道“代码在哪台机器上、用哪个 Python、为什么这么选”。

## 1. 服务器连接信息

本机 SSH 配置里已经有服务器记录：

```sshconfig
Host 106.55.163.7
  HostName 106.55.163.7
  Port 6000
  User ubuntu
```

连接命令：

```bash
ssh 106.55.163.7
```

说明：

- 服务器用户是 `ubuntu`。
- SSH 端口是 `6000`，不是默认的 `22`。
- 密码属于敏感信息，不写进仓库文档。

## 2. 服务器硬件

已检查到的 GPU：

```text
NVIDIA GeForce RTX 5090
显存约 24GB
```

当时检查时，GPU 基本空闲，只被桌面进程占用了少量显存。

这意味着：

- 可以跑轻量测试、smoke test 和小规模回归。
- 如果要跑完整训练，需要再评估显存、模型大小、batch size 和 rollout 配置。

## 3. 远端仓库位置

Task B 仓库已经放在服务器 home 目录下：

```bash
/home/ubuntu/AlphaApollo-TaskB
```

进入仓库：

```bash
cd /home/ubuntu/AlphaApollo-TaskB
```

当前远端仓库来自本机 Git bundle 克隆，因为服务器当时无法直接通过 GitHub HTTPS/SSH 拉取代码。

克隆后已确认最新提交：

```text
3dbe130 docs: add task b trajectory and experiment notes
```

远端 `origin` 已设置为：

```text
https://github.com/xuanhh567/AlphaApollo-TaskB.git
```

## 4. Conda 环境列表

服务器上检查到的 conda 环境包括：

```text
base
ACT
RoboTwin
alphaapollo
alphaapollo5090
env_isaaclab
lerobot
ns3-cosim
simpler
starai
vllm
```

和本项目最相关的是：

- `alphaapollo`
- `alphaapollo5090`

## 5. 推荐环境：alphaapollo5090

后续 Task B 优先使用：

```bash
/home/ubuntu/miniconda3/envs/alphaapollo5090/bin/python
```

原因：

- 服务器 GPU 是 RTX 5090。
- `alphaapollo5090` 从名字看就是为 5090 准备的环境。
- 这个环境里的 PyTorch / CUDA 版本更新，更适合新显卡。
- 项目 import 和 Task B 单元测试已经在这个环境里通过。

已检查版本：

```text
Python 3.12.13
torch 2.8.0+cu128
CUDA 可用: True
transformers 4.57.6
```

关键依赖检查结果：

```text
verl: True
datasets: True
vllm: True
ray: True
pandas: True
pyarrow: True
omegaconf: True
```

## 6. 备用环境：alphaapollo

另一个可用环境是：

```bash
/home/ubuntu/miniconda3/envs/alphaapollo/bin/python
```

已检查版本：

```text
Python 3.12.0
torch 2.6.0+cu124
CUDA 可用: True
transformers 4.51.1
```

这个环境也能 import 项目，但因为服务器是 RTX 5090，后续优先使用 `alphaapollo5090`。

## 7. 已完成的轻量验证

在服务器仓库目录：

```bash
cd /home/ubuntu/AlphaApollo-TaskB
```

使用 `alphaapollo5090` 跑过 Task B 相关测试：

```bash
ALPHAAPOLLO_SKIP_VERL_ALIAS=1 /home/ubuntu/miniconda3/envs/alphaapollo5090/bin/python tests/test_skill_prompt_renderer.py
ALPHAAPOLLO_SKIP_VERL_ALIAS=1 /home/ubuntu/miniconda3/envs/alphaapollo5090/bin/python tests/test_informal_math_skill_bridge.py
ALPHAAPOLLO_SKIP_VERL_ALIAS=1 /home/ubuntu/miniconda3/envs/alphaapollo5090/bin/python tests/test_skill_dispatcher.py
ALPHAAPOLLO_SKIP_VERL_ALIAS=1 /home/ubuntu/miniconda3/envs/alphaapollo5090/bin/python tests/test_skill_argument_validation.py
ALPHAAPOLLO_SKIP_VERL_ALIAS=1 /home/ubuntu/miniconda3/envs/alphaapollo5090/bin/python tests/test_tool_call_parser.py
ALPHAAPOLLO_SKIP_VERL_ALIAS=1 /home/ubuntu/miniconda3/envs/alphaapollo5090/bin/python tests/test_skill_registry.py
ALPHAAPOLLO_SKIP_VERL_ALIAS=1 /home/ubuntu/miniconda3/envs/alphaapollo5090/bin/python tests/test_skill_loader.py
```

测试结果：

```text
skill prompt renderer tests passed
informal math skill bridge tests passed
skill dispatcher tests passed
skill argument validation tests passed
tool call parser tests passed
skill registry tests passed
skill loader tests passed
```

通俗理解：

- 服务器能跑我们的代码。
- `alphaapollo5090` 里有项目需要的核心依赖。
- Task B 的 parser、registry、dispatcher、env bridge、prompt 生成这些基础模块在服务器上没有坏。

## 8. 下一步使用方式

以后在服务器上做 Task B 验证，可以先执行：

```bash
ssh 106.55.163.7
cd /home/ubuntu/AlphaApollo-TaskB
```

然后优先使用这个 Python：

```bash
/home/ubuntu/miniconda3/envs/alphaapollo5090/bin/python
```

如果要避免每次写完整路径，也可以临时激活环境：

```bash
conda activate alphaapollo5090
```

然后确认：

```bash
python -V
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

## 9. 对 Task B 的意义

Task B 现在还剩真正的回归实验没有完成，主要是比较：

- 改造前：原来的硬编码工具标签流程。
- 改造后：新的 `SKILL.md` + registry + structured `<tool_call>` 流程。

服务器环境已经准备好，下一步可以在这里跑：

- 小规模 smoke test。
- MATH-500 子集回归。
- 如果资源允许，再跑完整 MATH-500 回归。

