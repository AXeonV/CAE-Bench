# CAE Bench OJ

CAE Bench OJ 用于评测 Agent 实现的计算工程求解程序。项目围绕通用数据协议、结构校验、测试数据和独立判分组织，支持持续增加不同物理模型的题目和测试。

通用数据协议见 [CONTRACT.md](docs/CONTRACT.md)，初版实施规划见 [MVP-PLAN.md](docs/MVP-PLAN.md)，Agent 测试记录见 [AGENT-RESULTS.md](docs/AGENT-RESULTS.md)。各题目的方程、输入范围、测试设计、依赖和运行说明保存在对应的 `tasks/<task>/` 目录。

## 设计

- **通用数据协议**：Gmsh 存网格，NPZ 存数组，JSON 声明字段和条件；各题目明确方程与输入范围，求解程序按同一协议读写。
- **纠正 Agent I/O**：Agent 在理解输入、编写和调试程序时可随时调用**结构校验器**，根据诊断修改读写实现，减少输入输出理解错误的负担。*校验器只检查格式与引用，不验证或纠正物理结果。*
- **提交后独立评测**：逐例执行提交程序，重新校验输出并按题目误差阈值与标答比较，每点 0/1 分，汇总结果和日志。

## 项目结构

| 路径 | 职责 |
|---|---|
| `docs/` | 通用协议与项目规划 |
| `src/caeoj/problem.schema.json` | JSON 元数据 Schema |
| `src/caeoj/validation.py` | 基于通用数据协议的**结构校验器** |
| `src/caeoj/sdk.py` | 常量／字段读取与输出帮助 |
| `src/caeoj/grading.py` | 与参考输出比较的**独立判分器** |
| `src/caeoj/cli.py` | 校验与判分命令入口 |
| `src/utils/publish_dist.py` | 打包单题的公开解题材料到 dist |
| `src/utils/prepare_harbor.py` | **统一组装** Harbor 临时任务环境 |
| `src/utils/harbor/` | 通用 Harbor 模板与逐例判题逻辑 |
| `src/utils/PDEBench/` | PDEBench 数据获取、协议转换与参考审核 |
| `tasks/<task>/` | 各题目的题面、数据、标答及出题工具 |
| `tests/` | 协议、校验、判分和题目数据的自动测试 |
| `runs/` | 本地输出、临时 Harbor 任务和运行报告，不纳入版本控制 |

题目的开发材料与判题材料分别组织：开发材料提供题面、输入约定、公开样例及校验工具；判题材料包含测试数据、标答和判分配置。

## 任务

### 自主设计题目

题面、输入输出约定、数据生成与验证方法见各题 README。

| 目录 | 问题 | 要求输出 |
|---|---|---|
| [echo-field](tasks/echo-field/instruction.md) | 输入场回传，检查协议与校验链路 | 输入要求回传的场 |
| [heat-conduction](tasks/heat-conduction/README.md) | 稳态热传导 | temperature |
| [heat-transient](tasks/heat-transient/README.md) | 瞬态热传导 | temperature |
| [navier-stokes-steady](tasks/navier-stokes-steady/README.md) | 稳态不可压缩 Navier–Stokes | velocity、pressure |
| [navier-stokes-transient](tasks/navier-stokes-transient/README.md) | 瞬态不可压缩 Navier–Stokes | velocity、pressure |

### PDEBench

以下为 PDEBench 方程族题目。每个目录包含 instruction.md、DATA.md、DESIGN.md 和 README.md。样例与隐藏测试分组已规划；[PDEBench 数据准备工具](src/utils/PDEBench/README.md)支持克隆后一条命令获取所需源片段并转换输入，问题定义 problem.json、冻结清单和参考证书 JSON 纳入 Git；数值数组及网格不进入 Git，由工具补齐。默认逐例审核源对齐的官方数值轨迹并补齐答案；二维反应扩散恢复完整细网格初值，Darcy 修正未收敛快照至源算子稳态，一维反应扩散重算存在非物理停滞的官方轨迹。数值参考并非未经误差审核的精确连续真解。现已提供[宽松试运行评测配置](src/utils/PDEBench/EVALUATION.md)，无 baseline 也可组装并运行 Agent。正式误差阈值、资源限制和参考精度仍待校准，试运行成绩不作为正式 Benchmark 结论。

| 目录 | 问题 | 要求输出 |
|---|---|---|
| [PDEBench_1D_Advection](tasks/PDEBench_1D_Advection/README.md) | 一维周期线性平流 | state |
| [PDEBench_1D_Burgers](tasks/PDEBench_1D_Burgers/README.md) | 一维周期黏性 Burgers 方程 | state |
| [PDEBench_1D_ReactionDiffusion](tasks/PDEBench_1D_ReactionDiffusion/README.md) | 一维 logistic 反应扩散 | state |
| [PDEBench_1D_DiffusionSorption](tasks/PDEBench_1D_DiffusionSorption/README.md) | 一维 Freundlich 迟滞扩散 | concentration |
| [PDEBench_2D_ReactionDiffusion](tasks/PDEBench_2D_ReactionDiffusion/README.md) | 二维 FitzHugh–Nagumo 反应扩散 | activator、inhibitor |
| [PDEBench_2D_DarcyFlow](tasks/PDEBench_2D_DarcyFlow/README.md) | 二维空间变系数 Darcy 型稳态问题 | state |
| [PDEBench_2D_ShallowWater](tasks/PDEBench_2D_ShallowWater/README.md) | 二维浅水径向溃坝 | depth |
| [PDEBench_1D_CompressibleNavierStokes](tasks/PDEBench_1D_CompressibleNavierStokes/README.md) | 一维可压缩 Navier–Stokes | density、velocity、pressure |
| [PDEBench_2D_CompressibleNavierStokes](tasks/PDEBench_2D_CompressibleNavierStokes/README.md) | 二维可压缩 Navier–Stokes | density、velocity、pressure |
| [PDEBench_3D_CompressibleNavierStokes](tasks/PDEBench_3D_CompressibleNavierStokes/README.md) | 三维可压缩 Navier–Stokes | density、velocity、pressure |
| [PDEBench_2D_IncompressibleNavierStokes](tasks/PDEBench_2D_IncompressibleNavierStokes/README.md) | 二维非均匀强迫不可压缩流 | velocity |

## 运行

选择本地或 HPC 作为执行主机，在该主机的项目根目录运行后续流程。先激活自行配置的 Python 3.11+ 环境；`python`、`harbor` 和 `docker` 应来自该主机，尖括号内容均为待替换的占位符。下述单行命令可在 PowerShell 或 Bash 中执行。

**1. 准备运行环境。** 使用 Docker 的 Linux containers。

Docker、Python 环境和 Agent 认证需先配置好。认证由执行主机的环境变量提供，也可在 Agent 运行命令中追加 `--env-file '<agent-env-file>'`；Codex 的 `CODEX_AUTH_JSON_PATH` 指向自行配置的登录文件。

**2. 按题目来源准备数据。** 两类入口任选其一，之后共用步骤 3～7。

自主设计题目沿用“安装依赖 → 生成输入与标答 → 运行测试”的流程。以下安装项覆盖全仓库测试依赖，题目专用依赖与生成参数见对应 README：

```sh
python -m pip install -e '.[heat,pdebench]' harbor
python 'tasks/<task>/author/generate.py'
python -m unittest discover -s tests -p '<test-file>.py' -v
```

`<test-file>` 取对应题目 README 中的测试文件；NS 的测试同时依赖稳态与瞬态两题数据。全量测试命令 `python -m unittest discover -s tests -v` 需先准备全部自主设计题目及单文件平流适配题的数据。

PDEBench 方程族任务通过统一工具获取、转换并审核外部数据，不要求另写 generator 或 baseline：

```sh
python -m pip install -e '.[pdebench]' harbor
python src/utils/PDEBench/prepare.py --tasks '<task>' --budget-gb 60 --no-bootstrap
```

`<task>` 使用 `PDEBench_*` 目录名，准备全部方程族可用 `--tasks all`。单文件适配题 `1D_Advection_Sols_beta0.4` 使用其 README 中的数据转换入口。

**3. 检查输入与参考输出的结构。**

```sh
python -m caeoj validate-input 'tasks/<task>/cases/<case>/problem.json'
python -m caeoj validate-output --input 'tasks/<task>/cases/<case>/problem.json' --output 'tasks/<task>/reference/<case>/reference.npz'
```

**4. 发布材料并统一组装 Harbor 环境。** 依赖补充放在题目的 `harbor/requirements.txt`，CPU／内存配额与时限放在 `harbor/task.toml`；修改配置后重新组装。

```sh
python src/utils/publish_dist.py --task '<task>'
python src/utils/prepare_harbor.py --task '<task>'
```

公开包位于 `dist/<task>-agent.zip`，临时任务位于 `runs/harbor/tasks/<task>/`。组装结果中的 `oracle_available` 表示是否提供 baseline；隐藏输入和参考仅进入独立判题环境。

**5. 可选 Oracle 检查。** 有 baseline 时可先运行以下命令确认判题链路；没有 baseline 时跳过，直接运行 Agent。

```sh
harbor run -p 'runs/harbor/tasks/<task>' -e docker -a oracle -n 1 -o 'runs/harbor/jobs'
```

**6. 运行 Agent 并独立判题。** 例如 Codex + Luna：

```sh
harbor run -p 'runs/harbor/tasks/<task>' -e docker -a codex -m 'openai/gpt-6-luna' --ak 'reasoning_effort=medium' -n 1 -o 'runs/harbor/jobs'
```

HPC 运行可追加 `--override-cpus '<cpu-quota>' --override-memory-mb '<memory-mb>'`，值须与组装时声明的资源一致；`-n '<concurrency>'` 控制并发 trial 数，不是单个求解器的线程数。GPU／MPI 需统一配置解题与独立判题容器的工具链、运行库和设备映射；默认模板提供 CPU 环境。

**7. 查看成绩或复核单点。**

```sh
harbor view 'runs/harbor/jobs'
```

trial 的 `verifier/report.json` 保存逐点得分与误差，`reward.txt` 保存通过率。也可单独运行提交并判分：

```sh
python '<solver.py>' --input 'tasks/<task>/cases/<case>/problem.json' --output 'runs/<task>/<case>/result.npz'
python -m caeoj validate-output --input 'tasks/<task>/cases/<case>/problem.json' --output 'runs/<task>/<case>/result.npz'
python -m caeoj grade --input 'tasks/<task>/cases/<case>/problem.json' --output 'runs/<task>/<case>/result.npz' --reference 'tasks/<task>/reference/<case>/reference.npz' --atol '<atol>' --rtol '<rtol>'
```

阈值取题目判分配置。校验输出 `valid/errors` JSON；判分每点为 0/1，退出码 2 表示输入、参考或参数异常。

## TODO

1. **协议覆盖与读写便利**：验证通用数据协议能完整、无歧义地表达目标问题的数据与条件；完善文档、读取接口和结构诊断，减少 Agent 理解契约与实现输入输出的成本，使评测更集中于求解能力。
2. **减少对实现选择的隐性引导**：审视题面、示例、SDK 和提交入口带来的偏向，尤其避免 Python 脚本与 `.py` 入口使 Agent 默认用 Python 承担核心计算。逐步提供语言中立的工具与提交约定，让 Agent 根据问题规模和性能要求自主选择语言、库与实现方式。
3. **评测环境声明与资源配置一致**：在 IO Contract 中补充运行环境约定，明确可用 CPU 核数、内存、编译器及 MPI 等并行运行支持，供 Agent 选择实现和并行策略；同步调整 Harbor／Docker 的资源分配与启动配置，确保解题和判题环境的实际可用资源与声明一致，使性能结果可比较、可复现。
