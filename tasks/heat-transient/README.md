# 二维瞬态热传导题

题面见 [instruction.md](instruction.md)，数据定义见 [DATA.md](DATA.md)。本题采用无源扩散、四类齐次边界和网格上的分片线性初始温度，输出多个指定时刻的节点温度。

24 点变化初始温度形状、正负分布、边界组合、导热系数、热容、输出间隔、网格密度、非结构网格及编号／编码。出题设计与时间／资源约束分析见 [DESIGN.md](DESIGN.md)，逐点记录见 [TEST-CASES.md](TEST-CASES.md)。这些文件属于出题材料。

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

在项目根目录使用指定 expr 环境，沿用项目 README 的 `$caePython`：

```powershell
& $caePython -m pip install -e '.[heat]'
& $caePython -m pip install -r tasks/heat-transient/author/requirements.txt
& $caePython tasks/heat-transient/author/generate.py
& $caePython tasks/heat-transient/author/check.py
& $caePython tasks/heat-transient/author/check.py --time-mode adaptive
```

报告分别写入 `runs/heat-transient/fixed/report.json` 和 `runs/heat-transient/adaptive/report.json`。

baseline 可用 `--dt <seconds>` 设置固定名义步长（到输出时刻时缩短最后一步），或自适应模式的初始试探步；自适应局部误差控制为 `--atol <K> --rtol <number>`。这些是 baseline 的运行选项，题目不要求选手使用它们。

## 本地验收

当前机器、expr 环境、单线程线性代数的逐例结果：

| baseline 时间策略 | 得分 | 最大绝对误差 K | 最慢单点 s | 采样峰值 RSS MiB |
|---|---|---|---|---|
| 固定名义步长 | 24/24 | 0.007284 | 1.53 | 112.2 |
| 自适应步长 | 24/24 | 0.007464 | 4.44 | 117.6 |

单点限额为 5 秒、1,024 MB。上述结果用于验收当前网格与阈值；自适应模式时间余量较小，平台变化后需重新测量。公开材料不含本文件、解析公式、标答生成程序或 baseline。当前未运行解题 Agent。
