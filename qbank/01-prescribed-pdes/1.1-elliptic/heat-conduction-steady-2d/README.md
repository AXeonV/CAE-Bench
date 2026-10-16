# 热传导题

二维稳态热传导题。题面见 [instruction.md](instruction.md)，字段与边界条件解释见 [DATA.md](DATA.md)，测试点与解析方程见 [TEST-CASES.md](TEST-CASES.md)。

题面提供常温样例和四种边界条件的混合样例，均包含完整输入与已验证的正确输出。

32 个测试点覆盖常数至四次多项式解，定温、法向导数、向外热流、Robin、混合条件与纯 Neumann 的域平均温度约束；同时变化温度幅值、区域、导热系数、网格密度及存储形式。

## 文件

| 路径 | 用途 |
|---|---|
| `instruction.md` | 简洁题面 |
| `DATA.md` | 题目必需的字段与连续函数解释 |
| `samples/01/input/`、`samples/01/output/` | 题面引用的完整公开示例输入与正确输出，复用题库第 01 点 |
| `samples/01/verification.json` | 示例答案按本题阈值判分的验证记录 |
| `cases/<case>/problem.json, input.h5, mesh.msh, mesh.geo` | 32 组输入，遵守通用数据协议 |
| `reference/<case>/reference.h5` | 在实际网格节点处代入解析解生成的标答 |
| `reference/<case>/analytic.json` | 解析温度系数、源项和每条边的公式，可审计标答 |
| `TEST-CASES.md` | 全部解析解和逐边条件的可读清单 |
| `judge-config.json` | 冻结的误差阈值及单点时限 |
| `author/catalog.py` | **定义测试点**：记录解析温度函数、边界类型及参数、网格设置。 |
| `author/generate.py` | **生成输入与标答**：生成 Gmsh 网格、源项和边界数据，代入解析解生成标答。 |
| `author/baseline.py` | **求解并验证**：可用的本地 P1 有限元 solver，支持本题当前输入范围；只读取输入，用于验证数据和阈值。 |
| `author/check.py` | **批量执行与判分**：逐点运行指定 solver（默认 baseline），调用判分器并汇总报告。 |
| `harbor/` | 本题 SciPy 依赖及内存限制补充 |

## 出题与验证

HF 题内数据池管理输入与参考，包括 JSON；本题 `data-manifest.json` 选择池条目并绑定本地测试与样例编号。首次使用按[数据获取与维护](../../../maintenance/DATA-SYNC.md)拉取、核验并装配 `cases/`、`reference/`、`samples/`。以下命令用于制作或修订数据；重新生成后需更新池与选样绑定。

在项目根目录，激活 Python 环境后运行：

```sh
python -m pip install -e '.[heat]'
python 'qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d/author/generate.py'
python 'qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d/author/check.py'
```

`generate.py` 生成网格、输入、解析标答及已通过判分的公开样例，覆盖同名数据文件。`check.py` 默认逐点运行 P1 有限元基线，报告写入 `runs/heat/report.json`；用 `--program <solver.py>` 检查其他求解程序。

## 数据与判分

源项 `q=-kΔT_exact` 和各边条件由同一解析温度函数推导，标答为该函数在网格节点处的值，解析解不写入输入。源项与边界数据存为多项式系数，具体解释见 DATA.md。

每点限时 **1 秒**、内存上限 **1024 MB**；所有节点绝对误差 **≤0.01 K** 得 1 分，否则 0 分，满分 **32 分**。相对容差为零，以 `grading.json` 为准；逐例时限见 `judge-config.json`；Harbor 内存配置见 `harbor/task.toml`。

基线只读取输入，用 P1 有限元独立求解；当前 32/32 通过，最大绝对误差约 **0.00324 K**。该结果验证当前数据与阈值，题目不限定求解方法。

`tests/test_heat.py` 检查解析源项、逐边条件、纯 Neumann 相容性与域平均温度，并验证常见物理错误会被判错。
