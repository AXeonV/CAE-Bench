# CAE Bench OJ

CAE Bench OJ 用于评测 Agent 实现的计算工程求解程序。项目围绕通用数据协议、结构校验、测试数据和独立判分组织，支持持续增加不同物理模型的题目和测试。

完整协议见 [CONTRACT.md](docs/CONTRACT.md)，实施规划见 [MVP-PLAN.md](docs/MVP-PLAN.md)。各题目的方程、输入范围、测试设计、依赖和运行说明保存在对应的 `tasks/<task>/` 目录。

## 设计

- **通用数据协议**：Gmsh 存网格，NPZ 存数组，JSON 声明字段和条件；各题目明确方程与输入范围，求解程序按同一协议读写。
- **纠正 Agent 的 I/O 负担**：Agent 在理解输入、编写和调试程序时可随时调用**结构校验器**，根据诊断修改读写实现，减少输入输出理解错误的负担。*校验器只检查格式与引用，不验证或纠正物理结果。*
- **提交后独立评测**：逐例执行提交程序，重新校验输出并按题目误差阈值与标答比较，每点 0/1 分，汇总结果和日志。

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
