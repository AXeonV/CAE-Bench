# CAE Bench OJ

CAE Bench OJ 用于评测 Agent 实现的计算工程求解程序。项目围绕通用数据协议、结构校验、测试数据和独立判分组织，支持持续增加不同物理模型的题目和测试。

完整协议见 [CONTRACT.md](docs/CONTRACT.md)，实施规划见 [MVP-PLAN.md](docs/MVP-PLAN.md)。各题目的方程、输入范围、测试设计、依赖和运行说明保存在对应的 `tasks/<task>/` 目录。

## 设计

评测流程为：**文字题面与输入约定 → 编写求解程序 → 逐例执行 → 检查输出结构 → 与标答比较 → 汇总分数**。

- **通用数据协议**：几何／网格采用 Gmsh 等已有格式，数值数组采用 NumPy NPZ，JSON 声明文件引用、位置、字段、单位、参数和条件。实体编号、数组轴和分量含义明确，详见协议文档。
- **结构校验器**：检查字段、引用、shape、dtype、编号和时间轴，帮助解决读写格式问题。它不验证物理方程，不修改、重排或纠正数据。
- **题目与测试数据**：各题目定义物理模型、输入范围和连续／离散数据的数学含义，并提供测试输入、参考输出及判分参数。标答的生成方法由题目确定。
- **独立判分器**：结构合法后，按该题冻结的误差阈值比较结果与参考值。每测试点全部满足要求得 1 分，否则 0 分；输入或参考数据异常作为基础设施错误单独报告。
- **执行与汇总**：按题目配置启动提交程序，保存逐例输出、日志和判分报告。Agent／Harbor 负责后续开发与执行接入。

当前已实现协议、校验器、SDK、独立判分器和本地测试流程；Agent／Harbor 接入留待后续。

## 项目结构

| 路径 | 职责 |
|---|---|
| `docs/` | 通用协议与项目规划 |
| `src/caeoj/problem.schema.json` | JSON 元数据 Schema |
| `src/caeoj/validation.py` | 标准格式读取及跨文件结构检查 |
| `src/caeoj/sdk.py` | 可选的数据读写帮助 |
| `src/caeoj/grading.py` | 与参考输出比较的独立判分器 |
| `src/caeoj/cli.py` | 校验与判分命令入口 |
| `tasks/<task>/` | 各题目的题面、数据、标答及出题工具 |
| `tests/` | 协议、校验、判分和题目数据的自动测试 |
| `runs/<task>/` | 本地执行输出、日志和报告，不纳入版本控制 |

题目的开发材料与判题材料分别组织：开发材料提供题面、输入约定、公开样例及校验工具；判题材料包含测试数据、标答和判分配置。

## 运行

在项目根目录使用指定 Python 环境。以下 `<task>`、`<case>`、`<solver.py>`、`<atol>` 和 `<rtol>` 均为占位符，运行前替换为实际题目、测试点、程序路径和阈值。

安装项目并运行自动测试：

```powershell
$caePython = 'C:\Users\Admin\.conda\envs\expr\python.exe'
& $caePython -m pip install -e .
& $caePython -m unittest discover -s tests -v
```

各题目需要的额外依赖、数据生成及批量执行命令见其 README。

检查输入、运行求解程序并检查输出：

```powershell
& $caePython -m caeoj validate-input 'tasks/<task>/cases/<case>/problem.json'
& $caePython '<solver.py>' --input 'tasks/<task>/cases/<case>/problem.json' --output 'runs/<task>/<case>/result.npz'
& $caePython -m caeoj validate-output --input 'tasks/<task>/cases/<case>/problem.json' --output 'runs/<task>/<case>/result.npz'
```

按题目指定阈值对单点判分：

```powershell
& $caePython -m caeoj grade `
  --input 'tasks/<task>/cases/<case>/problem.json' `
  --output 'runs/<task>/<case>/result.npz' `
  --reference 'tasks/<task>/reference/<case>/reference.npz' `
  --atol '<atol>' --rtol '<rtol>'
```

参考 NPZ 与提交结果满足相同的输出契约，包含结果场、固定 IDs 和时间轴。浮点分量使用 `|结果−参考| ≤ atol + rtol×|参考|`；整数和布尔值精确比较。阈值属于题目配置，不属于通用数据协议。

校验命令输出 `valid/errors` JSON，退出码 0 为合法、1 为不合法、2 为参数错误。判分退出码 0 为通过、1 为答案错误或非法输出、2 为输入／参考数据或参数错误。结构校验与数值判分独立。
