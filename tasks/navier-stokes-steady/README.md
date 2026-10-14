# 二维稳态有粘不可压缩流

保留对流项的常密度、常粘度 NS 题。题面见 [instruction.md](instruction.md)，程序数据接口见 [DATA.md](DATA.md)，公式与基准来源见 [DESIGN.md](DESIGN.md)，逐点设置见 [TEST-CASES.md](TEST-CASES.md)。

32 点包含库埃特、泊肃叶、反向／组合驱动和 Re=100 方腔；覆盖零净流量、内部回流、四侧壁正反向运动，以及材料、网格、原点、尺度与 MSH 编码变化。通道比较节点速度和周期压力，方腔比较经坐标与矢量变换的 Ghia 1982 中线分量。

## 文件

| 路径 | 用途 |
|---|---|
| `instruction.md` | 简洁题面、范围、输出与完整示例引用 |
| `DATA.md` | 材料、矢量条件、周期映射、压力规范和采样点的程序语义 |
| `DESIGN.md`、`TEST-CASES.md` | 出题公式、Ghia 来源、逐点参数与覆盖范围，不发布 |
| `cases/<case>/` | Gmsh 网格、JSON 清单和 HDF5 输入 |
| `reference/<case>/reference.h5, analytic.json` | 独立参考输出及解析／论文数据来源，不发布 |
| `samples/<sample>/input/, output/` | 完整公开输入与已按本题阈值验证的正确输出 |
| `judge-config.json` | 判分阈值、单点时限与内存限制 |
| `author/catalog.py` | **定义测试点**：稳态、瞬态的私有参数配方。 |
| `author/mesh.py` | **生成网格**：等距 Gmsh 三角形、Physical Groups 和原生周期映射。 |
| `author/oracle.py`、`ghia.py` | **生成标答**：连续解析解及核对后的 Re=100 论文中线数据。 |
| `author/generate.py` | **生成题库**：组装输入、标答、样例和测试清单。 |
| `author/baseline.py` | **独立求解**：只读输入的有限差分／流函数涡量 baseline，不读取标答。 |
| `author/check.py` | **运行并判分**：逐点执行程序，检查误差并记录时间、RSS。 |
| `harbor/` | 本题的 SciPy 依赖和资源限制补充 |

## 出题与验证

沿用[项目 README](../../README.md#运行) 的 Python 环境，在项目根目录执行：

```sh
python tasks/navier-stokes-steady/author/generate.py
python tasks/navier-stokes-steady/author/check.py
```

`generate.py` 覆盖生成题库及样例；`check.py --program <solver.py>` 可检查其他提交，报告位于 `runs/navier-stokes-steady/baseline/`。作者生成工具由瞬态题复用；两题的 baseline 均为可独立部署的单文件。

两题共用的出题侧回归测试见 [tests/test_navier_stokes.py](../../tests/test_navier_stokes.py)，检查题库范围、边界数据与周期映射、解析解与 Ghia 中线变换、baseline 对数据引用的适配，以及样例判分和公开材料范围。

## 判分

每点要求的速度、压力分别使用 0.02 m/s、0.02 Pa 绝对误差，rtol=0；全部通过得 1 分。单点 5 秒、1,024 MiB，满分 32。方腔论文没有全场和压力参考，因此只要求其已发表的中线分量。
