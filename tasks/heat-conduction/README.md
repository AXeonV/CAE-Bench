# 热传导题交付说明

选手题面见 [instruction.md](instruction.md)，仅规定方程、输入范围、数据解释和输出。测试点与逐边解析方程见 [TEST-CASES.md](TEST-CASES.md)，属于出题材料。

32 个测试点覆盖常数、线性、双轴耦合、二至四次多项式，定温、法向导数、向外热流、Robin 及混合条件；还包含纯 Neumann 的域平均温度约束、绝热边、零场、小幅值、域平移、长宽比、不同 k、网格细化、非结构网格、稀疏 tags、binary MSH。

## 文件

| 路径 | 用途 |
|---|---|
| `instruction.md` | 简洁题面 |
| `DATA.md` | 题目必需的字段与连续函数解释 |
| `samples/01/input/`、`samples/01/output/` | 题面引用的完整公开示例输入与正确输出，复用题库第 01 点 |
| `samples/01/verification.json` | 示例答案按本题阈值判分的验证记录 |
| `cases/<case>/problem.json, input.npz, mesh.msh, mesh.geo` | 32 组输入，遵守通用数据协议 |
| `reference/<case>/reference.npz` | 在实际网格节点处代入解析解生成的标答 |
| `reference/<case>/analytic.json` | 解析温度系数、源项和每条边的公式，可审计标答 |
| `TEST-CASES.md` | 全部解析解和逐边条件的可读清单 |
| `judge-config.json` | 冻结的误差阈值及单点时限 |
| `author/catalog.py` | **定义测试点**：记录解析温度函数、边界类型及参数、网格设置。 |
| `author/generate.py` | **生成输入与标答**：生成 Gmsh 网格、源项和边界数据，代入解析解生成标答。 |
| `author/baseline.py` | **求解并验证**：可用的本地 P1 有限元 solver，支持本题当前输入范围；只读取输入，用于验证数据和阈值。 |
| `author/check.py` | **批量执行与判分**：逐点运行指定 solver（默认 baseline），调用判分器并汇总报告。 |

解析解不写入输入。后续接入 Agent 时，开发材料只提供题面及 DATA.md、通用协议、SDK／校验命令和 `samples/` 的完整公开示例；不提供 `author/`、`reference/`、`TEST-CASES.md` 及其余测试输入。目前没有 Agent 或 Harbor 适配。

## 运行

在项目根目录：

```powershell
$caePython = 'C:\Users\Admin\.conda\envs\expr\python.exe'
& $caePython -m pip install -e '.[heat]'
& $caePython 'tasks/heat-conduction/author/generate.py'
& $caePython 'tasks/heat-conduction/author/check.py'
& $caePython -m unittest discover -s tests -v
```

生成程序覆盖同名数据文件，同时生成公开示例并对其正确输出判分，只有通过才生成成功。标答仅由解析函数计算，不调用数值求解器；题目不限定使用有限元、差分或其他求解方法。

`check.py` 默认逐点启动本地有限元基线，报告写入 `runs/heat/report.json`，输出和日志保存在独立运行目录。用 `--program 路径` 检查其他本地 Python 求解程序；接口与题面相同。输入或标答结构错误记为基础设施异常，score 为 null；运行错误、超时、非法输出或超阈值则该点 0 分。退出码 0 全通过、1 有错误答案、2 基础设施异常。

单点判分可直接调用已有判分器，必须传本题阈值：

```powershell
& $caePython -m caeoj grade `
  --input 'tasks/heat-conduction/cases/01-constant-dirichlet/problem.json' `
  --output 'result.npz' `
  --reference 'tasks/heat-conduction/reference/01-constant-dirichlet/reference.npz' `
  --atol 0.01 --rtol 0
```

每例所有节点绝对误差≤0.01 K 得 1 分，否则 0 分，满分 32。该阈值独立于通用判分器的默认阈值；相对误差设为零，避免背景温度影响容差。

## 数据与阈值验证

源项为 `q=-kΔT_exact`；各边 g 由对应边界算子作用于同一个 `T_exact` 得到。因此参考温度精确满足题面定义的连续方程和边界条件。NPZ 存储 NumPy 升幂多项式的系数场，任务规定常系数及归一化自变量；不存在函数采样后插值造成的方程变更。这是已有 `components` 字段的题目语义，没有新增通用协议字段。

出题测试独立检查源项、每条边的方程、纯 Neumann 积分相容性及域平均温度；这些检查只属于出题数据质量测试，结构校验器不增加物理功能。

P1 基线使用三角形弱形式、Gaussian 积分、[SciPy 稀疏线性求解](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.spsolve.html)，纯 Neumann 用域积分约束。32/32 通过，最大绝对误差约 0.00324 K；网格细化的泡形解误差从约 0.00324 降到 0.000360 K。阈值为这套具体测试数据校准，不保证任意允许范围内的粗网格用 P1 都能达到该精度。

自动测试还验证漏掉源项、热流符号写反、忽略 k、错用 Robin 系数或平均温度都会被判错；它们的输出仍可以通过结构检查。完整测试入口为 `tests/test_heat.py`。
