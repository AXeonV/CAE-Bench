# Harbor 接入与解题材料发布

当前已实现公开解题材料的 dist 打包；Harbor 任务适配、Docker 构建及 Agent 运行尚未完成。以下是接入步骤和配置模板，完成适配后再执行评测命令。

## 1. 检查本机环境

本机已有 Docker Desktop 和 WSL2（Debian），检查时 Docker daemon 未启动，expr 环境尚未安装 Harbor。

启动 Docker Desktop，确认使用 Linux containers，并启用 `Settings → General → Use WSL 2 based engine`。如需从 Debian 调度，启用 `Resources → WSL Integration` 中的 Debian。[Docker 官方说明](https://docs.docker.com/desktop/features/wsl/)

在 PowerShell 中确认：

```powershell
docker version
docker compose version
docker run --rm hello-world
```

`docker version` 必须能显示 Server 信息。仓库的 Python 操作继续使用指定的 expr 环境：

```powershell
$caePython = 'C:\Users\Admin\.conda\envs\expr\python.exe'
& $caePython -m pip install harbor
$harborExe = 'C:\Users\Admin\.conda\envs\expr\Scripts\harbor.exe'
& $harborExe --version
& $harborExe run --help
```

Harbor 当前要求 Python ≥3.12，expr 的 Python 3.14 满足此要求；依赖兼容性仍以实际安装检查为准。首次验证成功后记录 Harbor 版本并固定。[安装说明](https://docs.harborframework.com/getting-started/installation)、[包要求](https://github.com/harbor-framework/harbor/blob/main/pyproject.toml)

## 2. 发布 Agent 解题材料

在仓库根目录运行（将 `<task>` 替换为题目目录名）：

```powershell
& $caePython src/utils/publish_dist.py --task '<task>'
```

生成 `dist/<task>-agent.zip`。包内保留仓库相对路径，包含题面、可选 DATA.md、通用协议、公开示例输入／正确输出、共享 CLI／SDK 和安装配置。校验命令可在 Agent 做题时随时调用。

采用明确的文件清单打包，不包含题目的 `author/`、`cases/`、`reference/`、解析解清单、项目规划、日志或密钥文件。发布前检查公开示例的输入与输出结构；数值正确性由题目的样例生成／判分流程验证，发布脚本不重复实现物理检查。

ZIP 含 SHA-256 文件清单，同一内容重复发布得到相同 ZIP。构建失败不会替换已有发布包。`--output <directory>` 可改变输出目录；发布只生成本地文件，不上传服务。新增题目须先提供 `instruction.md` 和完整 `samples/<sample>/input/problem.json`、`output/result.npz`，DATA.md 按需提供。

## 3. 添加 Harbor 任务适配

建议在仓库中新增独立目录，保留原有题目和工具：

```text
harbor/<task>/
├── instruction.md       # 引导阅读 /app 中的题面，提交 /app/submission/solve.py
├── task.toml            # 超时、资源、提交目录及 verifier 配置
├── environment/
│   ├── Dockerfile       # 只安装公开解题材料与运行依赖
│   └── agent.zip        # 由 dist 发布包复制而来
├── solution/
│   └── solve.sh         # Oracle 专用：将本地基线准备成提交程序
└── tests/
    ├── test.sh          # verifier 入口
    └── ...              # 判分程序、测试数据、标答及题目配置
```

这部分目前是待添加的适配，不是已经可运行的 Harbor 任务。[Harbor 任务结构](https://docs.harborframework.com/tasks/overview)

Agent 环境的 Dockerfile 可从以下模板开始，运行依赖按题目调整；容器内使用 Linux Python，宿主机仍使用 expr：

```dockerfile
FROM python:3.14-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash git curl ca-certificates libglu1-mesa libgl1 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY agent.zip /tmp/agent.zip
RUN python -m zipfile -e /tmp/agent.zip /app \
    && python -m pip install --no-cache-dir -e /app scipy==1.18.1
```

`task.toml` 配置模板：

```toml
schema_version = "1.3"
artifacts = ["/app/submission"]

[agent]
timeout_sec = 1800.0

[environment]
cpus = 2
memory_mb = 2048

[verifier]
timeout_sec = 1200.0
environment_mode = "separate"
```

Harbor 的 `schema_version` 是其配置格式，与本项目通用数据协议无关。采用 separate verifier，使判题使用干净环境；通过 `artifacts` 传递提交目录，Agent 对开发环境的修改不会自动进入判题环境。[配置说明](https://docs.harborframework.com/tasks/configuration)、[独立 verifier 与文件传递](https://docs.harborframework.com/tasks/separate-verifier)

`tests/test.sh` 应调用判题适配程序，逐点运行提交、结构校验、调用现有 `grading.py`，保留原始 0/1 分数与汇总报告，再把通过率写入 `/logs/verifier/reward.txt`。测试输入或标答异常应作为基础设施错误报告。

提交 solver 运行时只应能读取本次输入和公共依赖；标答与判分日志由可信判题程序持有。separate verifier 隔离开发阶段，但若把 solver 与标答放在同一可读文件系统，仍可直接读取答案。适配时应采用受限用户与目录权限，或独立执行环境，落实这一访问边界；不能直接把本地 `author/check.py` 当作隔离判题器。

## 4. 先 Oracle，再实际 Agent

完成以上适配后，先运行 Oracle，验证环境、提交传递和 verifier：

```powershell
& $harborExe run -p 'harbor/<task>' -e docker -a oracle -n 1 -o 'runs/harbor'
```

Oracle 使用 `solution/solve.sh`，其解法仅用于验收，不进入 Agent 镜像。Oracle 通过后，再设置所选 Agent 的认证环境变量并运行；密钥留在宿主机环境，不写入 dist、题目文件或 Dockerfile：

```powershell
& $harborExe run -p 'harbor/<task>' -e docker -a '<agent>' -m '<model>' -n 1 -o 'runs/harbor'
```

`<agent>`、`<model>` 由实际评测目标选择，不在本次发布时固定。[运行命令](https://docs.harborframework.com/jobs/run-a-job)

验收需要实际看到：Agent 能调用校验器并利用诊断，提交程序完成逐点执行，输出契约和数值判分正确，报告与 Harbor reward 一致。生成 dist 或写好模板不等于完成 Harbor 接入。
