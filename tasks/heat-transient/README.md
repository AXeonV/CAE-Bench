# 二维瞬态热传导题

二维无源瞬态热传导题，求解矩形域上的 `C ∂T/∂t = kΔT`，输出指定时刻的节点温度。题面见 [instruction.md](instruction.md)，字段与边界条件解释见 [DATA.md](DATA.md)，测试点与解析解入口见 [TEST-CASES.md](TEST-CASES.md)。

题面提供全零初始场样例和四种边界条件的混合样例，均包含完整输入与正确输出。

24 个测试点覆盖定温、法向导数、向外热流、Robin 及混合条件；初始场包含常温、平滑分布、局部热斑、短波长、正负变化和边界层。同时变化导热系数、热容、区域位置与长宽比、输出间隔、网格密度、非结构网格及编号／编码。解析标答、时间策略与网格资源设计见 [DESIGN.md](DESIGN.md)。

## 文件

| 路径 | 用途 |
|---|---|
| `instruction.md`、`DATA.md` | 公开题面与必需输入约定 |
| `samples/01/`、`samples/02/` | 完整公开输入与正确输出；验证记录留在出题端 |
| `cases/<case>/` | Gmsh 网格、元数据和初始节点场 |
| `reference/<case>/reference.npz` | 连续方程级数解在指定节点／时刻的标答 |
| `reference/<case>/analytic.json` | 积分收敛、级数尾界及网格规模记录 |
| `author/catalog.py` | **定义测试点**：初始节点值配方、边界和网格配置 |
| `author/mesh.py` | **生成网格**：Gmsh 划分与 tag 关联 |
| `author/oracle.py` | **计算标答**：初始场数值积分与特征函数级数求和 |
| `author/generate.py` | **生成数据**：组装输入、标答和公开样例 |
| `author/baseline.py` | **独立求解**：P1 有限元与固定／自适应隐式时间推进，只读输入 |
| `author/check.py` | **逐例验证**：独立判分并记录时间、采样峰值内存和积分步数 |
| `judge-config.json` | 判分阈值、单点时间与内存限额 |
| `harbor/` | 本题依赖和资源配置补充 |

## 出题与验证

在项目根目录，沿用[项目 README](../../README.md#运行) 中的 `$caePython`：

```powershell
& $caePython -m pip install -e '.[heat]'
& $caePython -m pip install -r tasks/heat-transient/author/requirements.txt
& $caePython 'tasks/heat-transient/author/generate.py'
& $caePython 'tasks/heat-transient/author/check.py'
& $caePython 'tasks/heat-transient/author/check.py' --time-mode adaptive
```

`generate.py` 生成网格、初始场、解析标答与公开样例，覆盖同名数据文件。`check.py` 默认逐点运行 baseline，调用独立判分器并检查时间与内存；用 `--program <solver.py>` 检查其他求解程序。运行产物保存在 `runs/heat-transient/`。

## 数据与判分

初始条件是输入节点温度在给定三角网格上的连续分片线性场；生成节点值的配方仅用于出题，不作为另一套连续初值。四条边的条件恒定且齐次，Robin 系数由输入给出。

标答采用连续方程的特征函数级数：对实际分片线性初值数值积分得到展开系数，再在指定节点和正时间求和；零时刻直接复制初始节点值。标答生成检查积分收敛与级数尾界，目标误差为 `1e-8 K`；公式与细节见 DESIGN.md。baseline 独立读取输入求解，不参与生成标答。

每点全部输出时刻、全部节点的绝对误差不超过 0.02 K 得 1 分，否则得 0 分；24 点满分 24。单点限时 5 秒、内存 1,024 MB，配置见 `judge-config.json`。

## 时间策略与基线

输入时间轴只规定输出时刻，求解程序自行选择内部固定或自适应时间步、迭代和收敛策略。CFL／扩散稳定性条件取决于具体离散方法，本题不统一规定 CFL 数或每步迭代次数。

baseline 使用一致质量矩阵 P1 有限元与稀疏 LU。固定模式采用 Crank–Nicolson，起始使用两个 backward Euler 半步；自适应模式通过一步与两个半步的差异估计局部误差。它用于出题端检查网格、精度与资源要求，题目不限定求解方法。

baseline 的 `--dt <seconds>` 设置固定名义步长或自适应初始试探步；`--atol <K> --rtol <number>` 设置自适应局部误差容差，与题目判分容差分别解释。

`tests/test_transient.py` 检查初始／输出时间轴、边界特征函数、独立已知级数、积分与截断收敛、时间积分及公开样例，并验证错误的热容或 Robin 处理会被判错。

本文件、DESIGN.md、TEST-CASES.md、解析公式、标答生成程序和 baseline 均为出题材料，不进入公开解题包。
