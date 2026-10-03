# CAE Bench OJ

当前实现 通用数据协议、结构校验器和 12 点本地回传 smoke。几何／网格使用 Gmsh，数值数组使用 NumPy NPZ，JSON 只保存元数据和条件声明。不接入 Agent 或 Harbor。

完整协议见 [CONTRACT.md](docs/CONTRACT.md)，任务规划见 [MVP-PLAN.md](docs/MVP-PLAN.md)。

## 运行

在项目目录使用指定 Python 环境：

```powershell
$caePython = 'C:\Users\Admin\.conda\envs\expr\python.exe'
& $caePython -m pip install -e .
& $caePython -m caeoj smoke
& $caePython -m unittest discover -s tests -v
```

12 个样例在 `tasks/echo-field/cases/`，每例包含 `problem.json`、真实 Gmsh `mesh.msh`、`input.npz`，部分附带 `mesh.geo`。重新生成时运行 `& $caePython -m caeoj make-cases`；生成程序调用官方 Gmsh API。

默认报告为 `runs/smoke/report.json`，每次运行创建独立目录，逐例启动本地程序并保存 `result.npz` 和日志。

## 检查与回传

```powershell
& $caePython -m caeoj validate-input 'tasks/echo-field/cases/09-vector-2d/problem.json'
& $caePython 'tasks/echo-field/solve.py' --input 'tasks/echo-field/cases/09-vector-2d/problem.json' --output 'runs/example/result.npz'
& $caePython -m caeoj validate-output --input 'tasks/echo-field/cases/09-vector-2d/problem.json' --output 'runs/example/result.npz'
```

校验命令输出 `valid/errors` JSON，退出码 0 合法、1 不合法；参数错误返回 2。Smoke 退出码 0 全通过、1 存在程序／答案错误、2 测试输入或执行基础设施错误。

结构校验与判分独立。校验器不检查物理正确性，不纠正、转置或重排数据。结构合法但交换速度分量的输出能通过校验，在 smoke 判分中得零分。

## 主要文件

- `src/caeoj/problem.schema.json`：单一的 JSON 元数据 Schema，使用文件内部引用。
- `src/caeoj/validation.py`：Gmsh／NPZ 读取和跨文件结构检查。
- `src/caeoj/sdk.py`：可选读写帮助；输出时复制固定实体／时间轴。
- `src/caeoj/examples.py`：Gmsh 样例生成。
- `src/caeoj/grading.py`：独立的参考值／误差阈值判分器。
- `src/caeoj/smoke.py`：逐例执行并调用判分器汇总。
- `tasks/echo-field/solve.py`：本地回传程序。
- `tests/test_contract.py`：格式、引用、数组、SDK、CLI、执行流程及校验／判分边界测试。

## 独立判分

```powershell
& $caePython -m caeoj grade --input 'problem.json' --output 'result.npz' --reference 'reference.npz'
```

参考 NPZ 须满足输入清单的输出要求，包含结果场、固定 IDs 和时间轴。浮点分量满足 `|结果−参考| ≤ 1e-6 + 1e-5×|参考|` 即通过；每例全通过得 1 分，否则 0 分。整数和布尔值精确比较。可用 `--atol`、`--rtol` 明确指定题目阈值。

判分退出码 0 为通过、1 为答案错误或非法输出、2 为输入／参考数据或参数错误。校验命令只检查结构，不包含判分功能。

依赖为 NumPy、Gmsh 和 jsonschema，安装在 expr 环境。结果只有 NPZ，不再有结果 JSON 或自定义 JSON 网格／场数组。
