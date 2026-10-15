# CAE Bench OJ

CAE Bench OJ 用于评测 Agent 实现的计算工程求解程序。项目围绕通用数据协议、结构校验、测试数据和独立判分组织，支持持续增加不同物理模型的题目和测试。

通用数据协议见 [CONTRACT.md](docs/CONTRACT.md)，考生只需本题 instruction.md、DATA.md 和 CONTRACT.md；[CFD-2.1.md](qbank/maintenance/protocols/CFD-2.1.md) 等领域文档仅供维护实现参考，多指标评分配置见 [GRADING.md](docs/GRADING.md)，初版实施规划见 [MVP-PLAN.md](docs/MVP-PLAN.md)，Agent 测试记录见 [AGENT-RESULTS.md](docs/AGENT-RESULTS.md)。题目统一保存在 `qbank/<章>/<节>/<题目>/`，按 [qbank 总体设计](qbank/design/README.md) 建设，第一章已有 [13 道给定 PDE 题](qbank/01-prescribed-pdes/README.md)，第二章已撰写 [65 道题面](qbank/02-fluid-mechanics/README.md)，数值数据后续补充。

## 设计

- **通用数据协议**：Gmsh 存网格，HDF5 存数组，JSON 声明字段和条件；各题目明确物理或数学问题与输入范围，求解程序按同一协议读写。
- **纠正 Agent I/O**：Agent 在理解输入、编写和调试程序时可随时调用**结构校验器**，根据诊断修改读写实现，减少输入输出理解错误的负担。*校验器只检查格式与引用，不验证或纠正物理结果。*
- **提交后独立评测**：逐例执行提交程序，重新校验输出并按题目误差阈值与标答比较，每点 0/1 分，汇总结果和日志。

## 项目结构

| 路径 | 职责 |
|---|---|
| `docs/` | 通用协议与项目规划 |
| `src/caeoj/problem.schema.json` | JSON 元数据 Schema |
| `src/caeoj/validation.py` | 基于通用数据协议的**结构校验器** |
| `src/caeoj/sdk.py` | 常量／字段读取与输出帮助 |
| `src/caeoj/storage.py` | 基于 h5py 的标准 HDF5 数组读写 |
| `src/caeoj/grading.py` | 与参考输出比较的**独立判分器** |
| `src/caeoj/cli.py` | 校验与判分命令入口 |
| `src/utils/publish_dist.py` | 打包单题的公开解题材料到 dist |
| `src/utils/prepare_harbor.py` | **统一组装** Harbor 临时任务环境 |
| `src/utils/harbor/` | 通用 Harbor 模板与逐例判题逻辑 |
| `src/utils/PDEBench/` | PDEBench 数据获取、协议转换与参考审核 |
| `qbank/` | 统一题库设计及按章、节组织的题目；[第 0 章](qbank/00-basic-tests/README.md)包含已迁移的 smoke-test |
| `legacy/` | 已归档的旧题目与回归测试，见 [归档说明](legacy/README.md) |
| `tests/` | 协议、校验、判分和题目数据的自动测试 |
| `runs/` | 本地输出、临时 Harbor 任务和运行报告，不纳入版本控制 |

题目的开发材料与判题材料分别组织：开发材料提供题面、输入约定、公开样例及校验工具；判题材料包含测试数据、标答和判分配置。

## 任务

### 题目列表

题面、输入输出约定、数据生成与验证方法见各题 README。

| 目录 | 问题 | 要求输出 |
|---|---|---|
| [smoke-test](qbank/00-basic-tests/0.1-io/smoke-test/instruction.md) | 简单测试：回传输入场，检查读写与判题链路 | 输入要求回传的场 |
| [heat-conduction-steady-2d](qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d/README.md) | 稳态热传导 | temperature |
| [heat-conduction-transient-2d](qbank/01-prescribed-pdes/1.2-diffusion-reaction/heat-conduction-transient-2d/README.md) | 瞬态热传导 | temperature |
| [advection-1d](qbank/01-prescribed-pdes/1.3-scalar-transport/advection-1d/README.md) | 一维周期线性平流 | state |
| [burgers-1d](qbank/01-prescribed-pdes/1.5-advection-diffusion/burgers-1d/README.md) | 一维周期黏性 Burgers 方程 | state |
| [reaction-diffusion-1d](qbank/01-prescribed-pdes/1.2-diffusion-reaction/reaction-diffusion-1d/README.md) | 一维 logistic 反应扩散 | state |
| [diffusion-sorption-1d](qbank/01-prescribed-pdes/1.2-diffusion-reaction/diffusion-sorption-1d/README.md) | 一维 Freundlich 迟滞扩散 | concentration |
| [reaction-diffusion-2d](qbank/01-prescribed-pdes/1.2-diffusion-reaction/reaction-diffusion-2d/README.md) | 二维 FitzHugh–Nagumo 反应扩散 | activator、inhibitor |
| [darcy-flow-2d](qbank/01-prescribed-pdes/1.1-elliptic/darcy-flow-2d/README.md) | 二维空间变系数 Darcy 型稳态问题 | state |
| [shallow-water-2d](qbank/01-prescribed-pdes/1.4-hyperbolic/shallow-water-2d/README.md) | 二维浅水方程 | depth |
| [compressible-navier-stokes-1d](qbank/01-prescribed-pdes/1.7-coupled-systems/compressible-navier-stokes-1d/README.md) | 一维可压缩 Navier–Stokes | density、velocity、pressure |
| [compressible-navier-stokes-2d](qbank/01-prescribed-pdes/1.7-coupled-systems/compressible-navier-stokes-2d/README.md) | 二维可压缩 Navier–Stokes | density、velocity、pressure |
| [compressible-navier-stokes-3d](qbank/01-prescribed-pdes/1.7-coupled-systems/compressible-navier-stokes-3d/README.md) | 三维可压缩 Navier–Stokes | density、velocity、pressure |
| [incompressible-navier-stokes-2d](qbank/01-prescribed-pdes/1.6-constrained-systems/incompressible-navier-stokes-2d/README.md) | 二维非均匀强迫不可压缩流 | velocity |

## 运行

第 0 章的本地输入输出测试使用 `python -m caeoj smoke`，详见[基础测试说明](qbank/00-basic-tests/README.md)。以下流程适用于已具备真实数据及公开样例的 qbank 题目。题目位置见[第一章目录](qbank/01-prescribed-pdes/README.md)；第二章目前仅完成题面。

`<task>` 是稳定题目标识，例如 `heat-conduction-steady-2d`；`<task-dir>` 是其真实目录，例如 `qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d`。发布器和组装器按标识自动定位，不接受路径作为 `--task`。

选择本地或 HPC 作为执行主机，在该主机的项目根目录运行后续流程。先激活自行配置的 Python 3.11+ 环境；`python`、`harbor` 和 `docker` 应来自该主机，尖括号内容均为待替换的占位符。下述单行命令可在 PowerShell 或 Bash 中执行。

**1. 准备运行环境。** 使用 Docker 的 Linux containers。

Docker、Python 环境和 Agent 认证需先配置好。认证由执行主机的环境变量提供，也可在 Agent 运行命令中追加 `--env-file '<agent-env-file>'`；Codex 的 `CODEX_AUTH_JSON_PATH` 指向自行配置的登录文件。

**2. 准备所选算例的数据。** 使用对应数据生成器或来源适配器，之后共用步骤 3～7。

提供独立生成器的题目沿用“安装依赖 → 生成输入与标答 → 运行测试”的流程。以下安装项覆盖全仓库测试依赖，题目专用依赖与生成参数见对应 README：

```sh
python -m pip install -e '.[heat,pdebench]' harbor
python '<task-dir>/author/generate.py'
python -m unittest discover -s tests -p '<test-file>.py' -v
```

`<test-file>` 取对应题目 README 中的测试文件。全量测试命令 `python -m unittest discover -s tests -v` 需先准备当前题目的数据；归档题目的测试见 [legacy/README.md](legacy/README.md)。

当前部分题目的算例来自 PDEBench；其来源适配器负责获取、转换并审核数据。具体来源、样本索引和参考证据见各题 `reference/`，数据集不作为题目分类或题目 ID：

```sh
python -m pip install -e '.[pdebench]' harbor
python src/utils/PDEBench/prepare.py --tasks '<task>' --budget-gb 60 --no-bootstrap
```

`<task>` 使用通用题目目录名，例如 `advection-1d`；`--tasks all` 准备该适配器当前支持的全部题目。后续加入其他来源时，应复用同一题目契约，并在算例或参考记录中标明来源。

当前配置用于试运行，正式参考误差和资源限制仍需校准，详见[评测说明](src/utils/PDEBench/EVALUATION.md)。

**3. 检查输入与参考输出的结构。**

```sh
python -m caeoj validate-input '<task-dir>/cases/<case>/problem.json'
python -m caeoj validate-output --input '<task-dir>/cases/<case>/problem.json' --output '<task-dir>/reference/<case>/reference.h5'
```

**4. 发布材料并统一组装 Harbor 环境。** 依赖补充放在题目的 `harbor/requirements.txt`，CPU／内存配额与时限放在 `harbor/task.toml`；修改配置后重新组装。

```sh
python src/utils/publish_dist.py --task '<task>'
python src/utils/prepare_harbor.py --task '<task>'
```

公开包位于 `dist/<task>-agent.zip`，临时任务位于 `runs/harbor/tasks/<task>/`。组装结果中的 `oracle_available` 表示是否提供 baseline；隐藏输入和参考仅进入独立判题环境。

**5. 可选 Oracle 检查。** 有 baseline 时可先运行以下命令确认判题链路；没有 baseline 时跳过，直接运行 Agent。

```sh
harbor run -p 'runs/harbor/<task-dir>' -e docker -a oracle -n 1 -o 'runs/harbor/jobs'
```

**6. 运行 Agent 并独立判题。** 例如 Codex + Luna：

```sh
harbor run -p 'runs/harbor/<task-dir>' -e docker -a codex -m 'openai/gpt-6-luna' --ak 'reasoning_effort=medium' -n 1 -o 'runs/harbor/jobs'
```

HPC 运行可追加 `--override-cpus '<cpu-quota>' --override-memory-mb '<memory-mb>'`，值须与组装时声明的资源一致；`-n '<concurrency>'` 控制并发 trial 数，不是单个求解器的线程数。默认模板提供 g++、OpenMP、Open MPI 及 HDF5 开发库（`h5cc`／`h5c++`、`h5dump`），解题与独立判题容器共用该工具链；GPU 需另行配置。

**7. 查看成绩或复核单点。**

```sh
harbor view 'runs/harbor/jobs'
```

trial 的 `verifier/report.json` 保存逐点得分与误差，`reward.txt` 保存通过率。也可单独运行提交并判分：

```sh
python '<solver.py>' --input '<task-dir>/cases/<case>/problem.json' --output 'runs/<task>/<case>/result.h5'
python -m caeoj validate-output --input '<task-dir>/cases/<case>/problem.json' --output 'runs/<task>/<case>/result.h5'
python -m caeoj grade --input '<task-dir>/cases/<case>/problem.json' --output 'runs/<task>/<case>/result.h5' --reference '<task-dir>/reference/<case>/reference.h5' --atol '<atol>' --rtol '<rtol>'
```

新策略使用 `--grading <task-dir>/grading.json` 替代 `--atol/--rtol`；支持按字段的 RMSE、NRMSE、最大误差、超限比例及 AND／OR 条件。旧配置保持原判分行为。

阈值取题目判分配置。校验输出 `valid/errors` JSON；判分每点为 0/1，退出码 2 表示输入、参考或参数异常。

## TODO

1. **协议覆盖与读写便利**：验证通用数据协议能完整、无歧义地表达目标问题的数据与条件；完善文档、读取接口和结构诊断，减少 Agent 理解契约与实现输入输出的成本，使评测更集中于求解能力。
2. **减少对实现选择的隐性引导**：审视题面、示例、SDK 和提交入口带来的偏向，尤其避免 Python 脚本与 `.py` 入口使 Agent 默认用 Python 承担核心计算。逐步提供语言中立的工具与提交约定，让 Agent 根据问题规模和性能要求自主选择语言、库与实现方式。
3. **评测环境声明与资源配置一致**：在 IO Contract 中补充运行环境约定，明确可用 CPU 核数、内存、编译器及 MPI 等并行运行支持，供 Agent 选择实现和并行策略；同步调整 Harbor／Docker 的资源分配与启动配置，确保解题和判题环境的实际可用资源与声明一致，使性能结果可比较、可复现。
