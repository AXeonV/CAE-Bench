# CAE Bench OJ

CAE Bench OJ 用于评测 Agent 实现的计算工程求解程序。项目围绕通用数据协议、结构校验、测试数据和独立判分组织，支持持续增加不同物理模型的题目和测试。

通用数据协议见 [CONTRACT.md](docs/CONTRACT.md)，实施规划见 [MVP-PLAN.md](docs/MVP-PLAN.md)。各题目的方程、输入范围、测试设计、依赖和运行说明保存在对应的 `tasks/<task>/` 目录。

## 设计

- **通用数据协议**：Gmsh 存网格，NPZ 存数组，JSON 声明字段和条件；各题目明确方程与输入范围，求解程序按同一协议读写。
- **纠正 Agent I/O**：Agent 在理解输入、编写和调试程序时可随时调用**结构校验器**，根据诊断修改读写实现，减少输入输出理解错误的负担。*校验器只检查格式与引用，不验证或纠正物理结果。*
- **提交后独立评测**：逐例执行提交程序，重新校验输出并按题目误差阈值与标答比较，每点 0/1 分，汇总结果和日志。

当前已实现协议、校验器、SDK、独立判分器与本地测试流程；首个 Harbor 任务已跑通 Agent 执行和独立判分。

## 项目结构

| 路径 | 职责 |
|---|---|
| `docs/` | 通用协议与项目规划 |
| `src/caeoj/problem.schema.json` | JSON 元数据 Schema |
| `src/caeoj/validation.py` | 基于通用数据协议的**结构校验器** |
| `src/caeoj/sdk.py` | 可选的数据读写帮助 |
| `src/caeoj/grading.py` | 与参考输出比较的**独立判分器** |
| `src/caeoj/cli.py` | 校验与判分命令入口 |
| `src/utils/publish_dist.py` | 打包单题的公开解题材料到 dist |
| `src/utils/prepare_harbor.py` | **统一组装** Harbor 临时任务环境 |
| `src/utils/harbor/` | 通用 Harbor 模板与逐例判题逻辑 |
| `tasks/<task>/` | 各题目的题面、数据、标答及出题工具 |
| `tests/` | 协议、校验、判分和题目数据的自动测试 |
| `runs/` | 本地输出、临时 Harbor 任务和运行报告，不纳入版本控制 |

题目的开发材料与判题材料分别组织：开发材料提供题面、输入约定、公开样例及校验工具；判题材料包含测试数据、标答和判分配置。

## 运行

在项目根目录使用指定 Python 环境。下列尖括号内容均为占位符，运行前替换为实际题目、测试点、程序路径或阈值。

准备环境与题目数据，额外依赖和生成参数见题目 README：

```powershell
$caePython = 'C:\Users\Admin\.conda\envs\expr\python.exe'
& $caePython -m pip install -e .
& $caePython 'tasks/<task>/author/generate.py'
& $caePython -m unittest discover -s tests -v
```

检查测试输入与标答的结构：

```powershell
& $caePython -m caeoj validate-input 'tasks/<task>/cases/<case>/problem.json'
& $caePython -m caeoj validate-output --input 'tasks/<task>/cases/<case>/problem.json' --output 'tasks/<task>/reference/<case>/reference.npz'
```

发布解题材料，再统一组装临时 Harbor 任务：

```powershell
& $caePython src/utils/publish_dist.py --task '<task>'
& $caePython src/utils/prepare_harbor.py --task '<task>'
```

公开材料为 `dist/<task>-agent.zip`，组装结果位于 `runs/harbor/tasks/<task>/`。各题可通过 `harbor/requirements.txt` 补充依赖，通过 `harbor/task.toml` 覆盖资源与时限。

启动 Docker 的 Linux containers，先用 Oracle 验收判题链路：

```powershell
$harborExe = 'C:\Users\Admin\.conda\envs\expr\Scripts\harbor.exe'
$env:PYTHONUTF8 = '1'
& $harborExe run -p 'runs/harbor/tasks/<task>' -e docker -a oracle -n 1 -o "$PWD/runs/harbor/jobs"
```

确认 Oracle 全分且无异常后，运行 Codex + Luna：

```powershell
$env:CODEX_AUTH_JSON_PATH = 'C:\Users\Admin\.codex\auth.json'
& $harborExe run -p 'runs/harbor/tasks/<task>' -e docker -a codex `
  -m 'openai/gpt-6-luna' --ak 'reasoning_effort=medium' -n 1 -o "$PWD/runs/harbor/jobs"
```

Harbor 自动逐点运行提交、校验输出并判分。查看轨迹与结果：

```powershell
& $harborExe view 'runs/harbor/jobs'
```

trial 的 `verifier/report.json` 保存逐点得分，`reward.txt` 保存通过率。

提交后也可本地执行并复核单点：

```powershell
& $caePython '<solver.py>' --input 'tasks/<task>/cases/<case>/problem.json' --output 'runs/<task>/<case>/result.npz'
& $caePython -m caeoj validate-output --input 'tasks/<task>/cases/<case>/problem.json' --output 'runs/<task>/<case>/result.npz'
& $caePython -m caeoj grade `
  --input 'tasks/<task>/cases/<case>/problem.json' `
  --output 'runs/<task>/<case>/result.npz' `
  --reference 'tasks/<task>/reference/<case>/reference.npz' `
  --atol '<atol>' --rtol '<rtol>'
```

误差阈值按题目配置填写。校验命令输出 `valid/errors` JSON；判分每点为 0/1 分，退出码 2 表示输入、标答或参数异常。
