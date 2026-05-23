# Task B 服务器配置与环境选择

这份文档记录 Task B 后续跑测试、回归实验时使用的服务器和 conda 环境。目标是让以后重新接手时，能快速知道“代码在哪台机器上、用哪个 Python、为什么这么选”。

## 0. 当前推荐服务器：RTX 4090 实验机

后来新开了一台 RTX 4090 服务器。和前面的 RTX 5090 相比，4090 的 PyTorch / vLLM 生态更成熟，所以它更适合作为 Task B 后续复现和小规模回归实验的主机器。

连接命令：

```bash
ssh -p 38983 root@proxy.cn-south-1.gpu-instance.ppinfra.com
```

说明：

- 服务器用户是 `root`。
- SSH 端口是 `38983`。
- 密码属于敏感信息，不写进仓库文档。

已检查硬件：

```text
GPU: NVIDIA GeForce RTX 4090
显存: 24564 MiB
Driver: 580.126.20
系统: Ubuntu 22.04.5
nvcc: CUDA 12.8
```

远端项目路径：

```bash
/root/AlphaApollo-TaskB
```

当前模型路径：

```bash
/root/AlphaApollo-TaskB/models/Qwen2.5-3B-Instruct
```

模型来源：

```text
ModelScope: Qwen/Qwen2.5-3B-Instruct
```

选择 ModelScope 的原因是服务器在国内访问 Hugging Face 容易超时，ModelScope 下载更稳定。

当前使用的 Python 环境：

```bash
/root/miniconda3/envs/alphaapollo/bin/python
```

已安装的关键包：

```text
Python 3.12.13
torch 2.6.0+cu124
vLLM 0.8.5
transformers 4.51.1
ray 2.47.1
pandas 3.0.3
pyarrow 24.0.0
datasets 4.8.5
omegaconf 2.3.0
```

GPU 检查结果：

```text
torch.cuda.is_available(): True
torch.version.cuda: 12.4
GPU: NVIDIA GeForce RTX 4090
bf16 matrix multiply: passed
```

模型与 vLLM 检查结果：

```text
Transformers 本地加载: passed
vLLM 直接推理: passed
main_generation + vLLM + informal_math_training 单题 rollout: passed
```

注意：vLLM 0.8.5 不接受 `rollout.top_k=0`。在这台服务器上跑 vLLM rollout 时，需要使用：

```bash
rollout.top_k=-1
```

`-1` 的意思是关闭 top-k 过滤。

Task B 单元测试已在这台 4090 服务器通过：

```bash
cd /root/AlphaApollo-TaskB

ALPHAAPOLLO_SKIP_VERL_ALIAS=1 PYTHONPATH=/root/AlphaApollo-TaskB /root/miniconda3/envs/alphaapollo/bin/python tests/test_skill_prompt_renderer.py
ALPHAAPOLLO_SKIP_VERL_ALIAS=1 PYTHONPATH=/root/AlphaApollo-TaskB /root/miniconda3/envs/alphaapollo/bin/python tests/test_informal_math_skill_bridge.py
ALPHAAPOLLO_SKIP_VERL_ALIAS=1 PYTHONPATH=/root/AlphaApollo-TaskB /root/miniconda3/envs/alphaapollo/bin/python tests/test_skill_dispatcher.py
ALPHAAPOLLO_SKIP_VERL_ALIAS=1 PYTHONPATH=/root/AlphaApollo-TaskB /root/miniconda3/envs/alphaapollo/bin/python tests/test_skill_argument_validation.py
ALPHAAPOLLO_SKIP_VERL_ALIAS=1 PYTHONPATH=/root/AlphaApollo-TaskB /root/miniconda3/envs/alphaapollo/bin/python tests/test_tool_call_parser.py
ALPHAAPOLLO_SKIP_VERL_ALIAS=1 PYTHONPATH=/root/AlphaApollo-TaskB /root/miniconda3/envs/alphaapollo/bin/python tests/test_skill_registry.py
ALPHAAPOLLO_SKIP_VERL_ALIAS=1 PYTHONPATH=/root/AlphaApollo-TaskB /root/miniconda3/envs/alphaapollo/bin/python tests/test_skill_loader.py
```

结果：

```text
skill prompt renderer tests passed
informal math skill bridge tests passed
skill dispatcher tests passed
skill argument validation tests passed
tool call parser tests passed
skill registry tests passed
skill loader tests passed
```

最小真实 rollout 已通过：

```text
输入: What is 1+1? Put the final answer in \boxed{}.
模型: /root/AlphaApollo-TaskB/models/Qwen2.5-3B-Instruct
后端: vLLM
输出: <answer>\boxed{2}</answer>
avg@1: 1.0000
pass@1: 1.0000
Reward: 1.0
```

输出文件：

```text
/root/AlphaApollo-TaskB/data/task-b-single-smoke/qwen25_3b_vllm_no_think_only.json
/root/AlphaApollo-TaskB/data/task-b-single-smoke/qwen25_3b_vllm_no_think_only.parquet
```

MATH-500 5 题 sanity test 已通过运行：

```text
输入: /root/AlphaApollo-TaskB/data/task-b-sanity-5/custom_data/test.parquet
输出: /root/AlphaApollo-TaskB/data/task-b-sanity-5/qwen25_3b_vllm_math500_5_strict_format.json
输出: /root/AlphaApollo-TaskB/data/task-b-sanity-5/qwen25_3b_vllm_math500_5_strict_format.parquet
avg@1: 0.6000
pass@1: 0.6000
```

这一步验证的是小样本连续 rollout 稳定性，不是正式回归指标。正式回归还需要固定更大的样本数，例如 100 题或全量 500 题。

依赖检查注意事项：

```text
pip check
-> decord 0.6.0 is not supported on this platform
```

这个问题目前不影响 Task B 的 parser、registry、dispatcher、prompt、env bridge 单元测试。`decord` 主要和视频读取相关，Task B 的数学工具调用主线暂时用不到它。后续如果跑到多模态或视频相关流程，再单独处理。

安装过程中的一个小坑：

```bash
curl -LO https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniforge/Miniforge3-Linux-x86_64.sh
```

这个地址当时下载到的是 153 字节的 404 HTML 页面，所以执行会出现：

```text
line 1: html: No such file or directory
syntax error near unexpected token `<'
```

这不是 conda 本身坏了，而是下载地址不对。当前服务器已经安装并使用 `/root/miniconda3`，所以不需要继续执行那个坏掉的 `Miniforge3-Linux-x86_64.sh` 文件。

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
48fbbb0 docs: record task b server environment
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

然后优先使用这个 Python 做单元测试、数据检查和非 vLLM 小实验：

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

## 10. 已发现的服务器运行注意事项

本地模型路径：

```text
/home/ubuntu/wjx/AlphaApollo/models/Qwen2.5-3B-Instruct
```

这个路径下已看到：

```text
config.json
tokenizer.json
model-00001-of-00002.safetensors
model-00002-of-00002.safetensors
```

服务器访问 Hugging Face 数据集时出现过连接超时。因此，小规模实验可以先在本机生成 parquet，再传到服务器运行。

`alphaapollo5090` 里的 vLLM 在 RTX 5090 上运行时遇到 CUDA kernel 兼容问题：

```text
CUDA error: no kernel image is available for execution on the device
```

已验证 PyTorch 本身可以在 GPU 上做 bf16 矩阵乘法，所以问题更接近 vLLM 编译 / CUDA kernel 适配，而不是 GPU 完全不可用。

HF rollout 临时能跑通链路：

```text
rollout.name=hf
```

但是 5 题 sanity test 显示，HF rollout 的生成结果严重重复，没有稳定输出 `<answer>` 或 `<tool_call>`，所以不适合作为正式 MATH-500 回归后端。

服务器还有一个独立 `vllm` 环境：

```text
/home/ubuntu/miniconda3/envs/vllm/bin/python
torch 2.11.0+cu130
vllm 0.20.0
transformers 5.9.0
CUDA 可用: True
```

这个环境已经验证可以直接用 vLLM 运行本地 Qwen 模型，输出正常。

但它暂时缺少 AlphaApollo 所需依赖：

```text
ray: False
datasets: False
omegaconf: False
pandas: False
pyarrow: False
tensordict: False
accelerate: False
codetiming: False
hydra: False
```

因此，后续更推荐的环境路线是：

```text
基于 /home/ubuntu/miniconda3/envs/vllm 补齐 AlphaApollo 依赖，
或者创建一个新的 alphaapollo-vllm5090 环境，
保留 torch 2.11.0+cu130 / vllm 0.20.0，
再跑 5 -> 20 -> 100 题回归。
```
