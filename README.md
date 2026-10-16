# CAE Bench OJ

CAE Bench OJ 用于评测 Agent 实现的计算工程求解程序。项目围绕通用数据协议、结构校验、测试数据和独立判分组织，支持持续增加不同物理模型的题目和测试。

考生阅读本题 `instruction.md`、`DATA.md` 和[通用数据协议](docs/CONTRACT.md)即可确定任务与数据规则。维护方可查阅[题库设计](qbank/design/README.md)、[运行装配](qbank/maintenance/RUNTIME.md)、[评分配置](docs/GRADING.md)及 [Agent 测试记录](docs/AGENT-RESULTS.md)。

## 设计

- **通用数据协议**：Gmsh 存网格，HDF5 存数组，JSON 声明字段和条件；各题目明确物理或数学问题与输入范围，求解程序按同一协议读写。
- **纠正 Agent I/O**：Agent 在理解输入、编写和调试程序时可随时调用**结构校验器**，根据诊断修改读写实现，减少输入输出理解错误的负担。*校验器检查格式、引用及声明约束，不验证或纠正物理结果。*
- **提交后独立评测**：逐例执行提交程序，重新校验输出并按题目误差阈值与标答比较，每点 0/1 分，汇总结果和日志。

## 项目结构

主要目录与入口如下；题目内的作者工具、环境补充及专用扩展按需提供。

```text
.
├── docs/                         通用协议、评分规则与 Agent 测试记录
├── .agents/skills/               出题、数据设计、审核、配置与评测工作流
├── src/
│   ├── caeoj/                    通用运行核心，供考生工具和判分器共用
│   │   ├── cli.py                校验、判分及工具信息命令
│   │   ├── sdk.py storage.py     数据读取与 HDF5 写入
│   │   ├── validation.py         结构校验；problem.schema.json 定义元数据
│   │   ├── grading*.py           评分策略与指标；grading.schema.json 定义配置
│   │   └── runtime.py            加载装配描述、组合 Schema 与声明检查
│   ├── caeoj_tools/              维护工具，不进入考生包
│   │   ├── task_paths.py author.py      题目定位与作者工具加载
│   │   ├── grading_policy.py            读取题目评分配置
│   │   └── assembly.py dependencies.py  公开运行装配与依赖锁定
│   └── utils/
│       ├── publish_dist.py       打包单题或题集的公开材料及工具
│       ├── prepare_harbor.py     统一组装 Harbor 临时任务环境
│       ├── harbor/               通用模板与逐例判题逻辑
│       └── PDEBench/             来源数据获取、协议转换与参考审核
├── qbank/
│   ├── <章>/<节>/<题目>/          题面、DATA、样例、测试与本题配置
│   │   ├── author/               本题数据与参考制作、基线及本地验证
│   │   ├── cases/ reference/     隐藏输入与私有参考
│   │   ├── samples/              完整公开样例
│   │   ├── harbor/               本题环境与依赖补充
│   │   └── extension/            按需提供本题专用的公开契约检查
│   ├── design/                   题库规划、出题原则与架构
│   │   └── reviews/              历史实施与审阅记录
│   ├── maintenance/              维护实现说明、领域规范及可复用作者工具
│   │   ├── protocols/            内部领域说明，不作为额外考生契约
│   │   ├── authoring/            按物理能力复用的题面／DATA 构建工具
│   │   └── RUNTIME.md、EVALUATION.md  当前运行装配与评测配置说明
│   └── extensions/
│       ├── caeoj_ext/            共享领域声明检查与辅助函数
│       └── caeoj_bundle/         题目绑定、扩展依赖及公开文件白名单
├── tests/                        协议、校验、评分、装配及题目回归测试
├── dist/                         生成的公开材料包，不纳入版本控制
└── runs/                         本地输出、Harbor 任务与报告，不纳入版本控制
```

题目的开发材料与判题材料分别组织：开发材料提供题面、输入约定、公开样例及校验工具；判题材料包含测试数据、标答和判分配置。

## 任务

题目位于 `qbank/<章>/<节>/<题目>/`，具体题面、数据要求与准备方法见各题 README。

| 目录 | 内容 |
|---|---|
| [第 0 章](qbank/00-basic-tests/README.md) | 输入输出 smoke test |
| [第 1 章](qbank/01-prescribed-pdes/README.md) | 给定 PDE，包括自主设计题目与 PDEBench 数据适配 |
| [第 2 章](qbank/02-fluid-mechanics/README.md) | 流体力学 |
| [第 3 章](qbank/03-solid-mechanics/README.md) | 固体与结构力学 |
| [第 4 章](qbank/04-multibody-mechanics/README.md) | 多体力学 |
| [第 5 章](qbank/05-heat-transfer/README.md) | 传热与热过程 |
| [第 6 章](qbank/06-acoustics/README.md) | 声学分析 |
| [第 7 章](qbank/07-electromagnetics/README.md) | 电磁场与电路 |
| [第 8 章](qbank/08-optics/README.md) | 光学与光子学 |

第 2～8 章已完成题面、DATA 和评测配置；正式数值数据、参考及评测发布仍待完成。

## 维护技能

Skill 是供维护 Agent 使用的工作流，位于 `.agents/skills/`，可在请求中指定技能名和目标，例如“使用 `$caeoj-design-data` 为 `<task>` 设计 DATA.md”。技能与引用说明随协议、工具和流程变更同步维护，不进入考生材料。

| 技能 | 用途 |
|---|---|
| [caeoj-author-section](.agents/skills/caeoj-author-section/SKILL.md) | 补齐章节规划，撰写题面并组织独立考生审阅 |
| [caeoj-design-data](.agents/skills/caeoj-design-data/SKILL.md) | 设计自包含 DATA.md，按需补足协议及工具支持 |
| [caeoj-audit-data](.agents/skills/caeoj-audit-data/SKILL.md) | 对照题面、协议和全部实际数据，审核 I/O 定义与读取分支 |
| [caeoj-configure-judge](.agents/skills/caeoj-configure-judge/SKILL.md) | 配置评分与执行资源，核查判题实现并验证配置生效 |
| [caeoj-run-benchmark](.agents/skills/caeoj-run-benchmark/SKILL.md) | 准备并运行 Agent 评测，管理监控、冻结条件与结果汇总 |

## 运行

以下流程适用于具备真实数据及完整公开样例的题目。第 0 章的本地读写测试使用 `python -m caeoj_tools.cli smoke`，详见[基础测试说明](qbank/00-basic-tests/README.md)。

`<task>` 是稳定题目标识，例如 `heat-conduction-steady-2d`；`<task-dir>` 是其真实目录，例如 `qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d`。发布器和组装器按标识自动定位，不接受路径作为 `--task`。

选择本地或 HPC 作为执行主机，在该主机的项目根目录运行后续流程。先激活自行配置的 Python 3.11+ 环境；`python`、`harbor` 和 `docker` 应来自该主机，尖括号内容均为待替换的占位符。下述单行命令可在 PowerShell 或 Bash 中执行。

**1. 准备运行环境。** 使用 Docker 的 Linux containers。

Docker、Python 环境和 Agent 认证需先配置好。认证由执行主机的环境变量提供，也可在 Agent 运行命令中追加 `--env-file '<agent-env-file>'`；Codex 的 `CODEX_AUTH_JSON_PATH` 指向自行配置的登录文件。

```sh
python -m pip install -e '.[maint,heat,pdebench]' -e qbank/extensions harbor
```

**2. 准备所选算例的数据。** 使用对应数据生成器或来源适配器，之后共用步骤 3～7。

提供独立生成器的题目生成输入与参考后运行相关测试；专用依赖与生成参数见对应 README：

```sh
python '<task-dir>/author/generate.py'
python -m unittest discover -s tests -p '<test-file>.py' -v
```

`<test-file>` 取对应题目 README 中的测试文件。全量测试命令 `python -m unittest discover -s tests -v` 需先准备当前题目的数据。

当前部分题目的算例来自 PDEBench；其来源适配器负责获取、转换并审核数据。具体来源、样本索引和参考证据见各题 `reference/`，数据集不作为题目分类或题目 ID：

```sh
python src/utils/PDEBench/prepare.py --tasks '<task>' --budget-gb 60 --no-bootstrap
```

`<task>` 使用通用题目目录名，例如 `advection-1d`；`--tasks all` 准备该适配器当前支持的全部题目。后续加入其他来源时，应复用同一题目契约，并在算例或参考记录中标明来源。

当前配置用于试运行，正式参考误差和资源限制仍需校准，详见[评测说明](src/utils/PDEBench/EVALUATION.md)。

**3. 检查输入与参考输出的结构。**

```sh
python -m caeoj validate-input '<task-dir>/cases/<case>/problem.json'
python -m caeoj validate-output --input '<task-dir>/cases/<case>/problem.json' --output '<task-dir>/reference/<case>/reference.h5'
```

**4. 发布材料并统一组装 Harbor 环境。** 评分放在 `grading.json`，逐例时限放在 `judge-config.json`，CPU／内存等容器资源放在 `harbor/task.toml`，依赖补充放在 `harbor/requirements.txt`；修改后重新打包并组装。

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

HPC 运行可追加 `--override-cpus '<cpu-quota>' --override-memory-mb '<memory-mb>'`，值须与组装时声明的资源一致；`-n '<concurrency>'` 控制并发 trial 数，不是单个求解器的线程数。默认模板提供 g++、OpenMP、Open MPI 及 HDF5 开发库（`h5cc`／`h5c++`、`h5dump`），解题与独立判题容器共用该工具链；GPU 需另行配置。

**7. 查看成绩或复核单点。**

```sh
harbor view 'runs/harbor/jobs' --jobs --host 0.0.0.0 --port 8080
```

trial 的 `verifier/report.json` 保存逐点得分与误差，`reward.txt` 保存通过率。也可单独运行提交并判分：

```sh
python '<solver.py>' --input '<task-dir>/cases/<case>/problem.json' --output 'runs/<task>/<case>/result.h5'
python -m caeoj validate-output --input '<task-dir>/cases/<case>/problem.json' --output 'runs/<task>/<case>/result.h5'
python -m caeoj grade --input '<task-dir>/cases/<case>/problem.json' --output 'runs/<task>/<case>/result.h5' --reference '<task-dir>/reference/<case>/reference.h5' --grading '<task-dir>/grading.json'
```

使用题目提供的 `grading.json`，支持的评分方式见 [GRADING.md](docs/GRADING.md)。

配置消费点、总预算计算与数据就绪边界见[维护说明](qbank/maintenance/EVALUATION.md)；配置完成不代表正式数据或评测发布完成。

阈值取题目判分配置。校验输出 `valid/errors` JSON；判分每点为 0/1，退出码 2 表示输入、参考或参数异常。

## TODO

1. **协议覆盖与读写便利**：验证通用数据协议能完整、无歧义地表达目标问题的数据与条件；完善文档、读取接口和结构诊断，减少 Agent 理解契约与实现输入输出的成本，使评测更集中于求解能力。
2. **减少对实现选择的隐性引导**：审视题面、示例、SDK 和提交入口带来的偏向，尤其避免 Python 脚本与 `.py` 入口使 Agent 默认用 Python 承担核心计算。逐步提供语言中立的工具与提交约定，让 Agent 根据问题规模和性能要求自主选择语言、库与实现方式。
3. **评测环境声明与资源配置一致**：在 IO Contract 中补充运行环境约定，明确可用 CPU 核数、内存、编译器及 MPI 等并行运行支持，供 Agent 选择实现和并行策略；同步调整 Harbor／Docker 的资源分配与启动配置，确保解题和判题环境的实际可用资源与声明一致，使性能结果可比较、可复现。
