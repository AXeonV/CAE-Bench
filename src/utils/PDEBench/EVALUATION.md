# PDEBench 宽松试运行评测配置

11 个方程族均已提供 judge-config.json 和 harbor/task.toml。配置标记 stage=provisional，仅用于初步试运行；连续参考误差、评分阈值和性能预算尚未正式校准。

每个 case 独立按墙钟时间限时，同一题的全部 case 共用参数。浮点输出逐项满足 |结果−参考| ≤ atol + rtol·|参考|；每个字段使用其声明单位的数值。当前共享判题器采用一组 atol/rtol 约束该题全部输出，不做字段间归一化或单位换算；尤其可压缩流的不同物理量后续仍需分别校准。IDs、时间轴、shape 和 dtype 的结构检查保持严格。

| 方程族 | atol | rtol | 每例秒数 | CPU 配额 | 内存 MB | 输出文件上限 |
|---|---:|---:|---:|---:|---:|---|
| 1D_Advection | 0.1 | 0.1 | 120 | 2 | 2048 | 128 MiB |
| 1D_Burgers | 0.1 | 0.1 | 120 | 2 | 2048 | 128 MiB |
| 1D_CompressibleNavierStokes | 0.1 | 0.2 | 120 | 2 | 2048 | 128 MiB |
| 1D_DiffusionSorption | 0.02 | 0.2 | 120 | 2 | 2048 | 128 MiB |
| 1D_ReactionDiffusion | 0.05 | 0.1 | 120 | 2 | 2048 | 128 MiB |
| 2D_CompressibleNavierStokes | 0.1 | 0.2 | 600 | 4 | 4096 | 256 MiB |
| 2D_DarcyFlow | 1e-05 | 0.2 | 600 | 4 | 4096 | 256 MiB |
| 2D_IncompressibleNavierStokes | 0.1 | 0.2 | 900 | 4 | 8192 | 256 MiB |
| 2D_ReactionDiffusion | 0.1 | 0.2 | 600 | 4 | 4096 | 256 MiB |
| 2D_ShallowWater | 0.1 | 0.1 | 600 | 4 | 4096 | 256 MiB |
| 3D_CompressibleNavierStokes | 0.1 | 0.2 | 1800 | 4 | 8192 | 2048 MiB |

Darcy 的绝对容限使用较小数值，以免最小源项配置被宽松统一绝对容限吞没；相对容限仍为 20%。吸附浓度的绝对容限也按其量级单独设置。这些选择尚未通过正式区分度与参考误差校准。

Agent 时间上限为 3600 秒，三维题为 7200 秒；环境构建上限为 1800 秒。verifier 的整阶段时限覆盖该题全部 case 达到逐例上限，加 600 秒余量，三维加 1200 秒。具体数值以各题 task.toml 为准。

memory_mb 是 Harbor 环境的容器内存上限，不是 judge-config 中逐例进程的单独限制。实际运行仍需 Docker 主机提供相应内存与 CPU；配置不会自动扩大 Docker 虚拟机的内存。二维不可压缩题和三维题均配置 8192 MB，运行前应给 Docker 足够内存并留出系统开销。

组装后的 Agent 入口 instruction.md 只给出求解与提交要求，以及实际误差容限、逐例时限、CPU、可用内存和输出文件大小上限。试运行状态、阈值校准情况及容器资源的实现说明仅保留在维护文档和配置中，不写入 Agent 入口。

## 无 baseline 的运行路径

baseline 已改为可选。没有 author/baseline.py 的题目也可以组装，组装结果标记 oracle_available=false；直接运行 Codex/Luna，跳过 Oracle。判分仍与已有 reference.npz 比较。旧任务有 baseline 时保留原 Oracle 入口。

在数据已补齐、Docker 和 Harbor 可用的环境中，可自行运行下列命令；本次配置补齐没有启动它们：

```bash
.venv/bin/python src/utils/publish_dist.py --task PDEBench_1D_Advection
.venv/bin/python src/utils/prepare_harbor.py --task PDEBench_1D_Advection
export CODEX_AUTH_JSON_PATH="$HOME/.codex/auth.json"
harbor run -p runs/harbor/tasks/PDEBench_1D_Advection \
  -e docker -a codex -m openai/gpt-6-luna \
  --ak reasoning_effort=medium -n 1 -o runs/harbor/jobs
```

对于其他方程族替换任务名即可；缺少数值文件时先运行数据准备工具。报告仍是每例 0/1，通过率不能直接解释为已校准的正式 Benchmark 能力指标。

## Apple Silicon 与镜像下载

Apple Silicon 的 Docker 默认构建 Linux ARM64；当前固定依赖 gmsh==4.15.2 没有可供该安装流程使用的 Linux ARM64 wheel。此环境在运行 Harbor 前设置：

```bash
export DOCKER_DEFAULT_PLATFORM=linux/amd64
```

该变量同时影响 Docker Compose 的镜像构建与容器平台选择；无需改动数学题面或降低 Gmsh 版本。x86-64 镜像会在 Apple Silicon 上通过模拟运行，因此其用时不应作为原生 ARM 性能结果。

若日志在拉取 python:3.14-slim 时显示 TLS handshake timeout，属于 Docker Hub 连接问题，Agent 尚未开始；可在连接恢复后先运行 `docker pull --platform linux/amd64 python:3.14-slim`，再重试原 Harbor 命令。LiteLLM 费用表下载警告需与 trial 的 exception.txt 区分，不能据此解释得分。
