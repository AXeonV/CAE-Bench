# 二维瞬态有粘不可压缩流

含初始速度、非线性对流与压力约束的二维 NS 题。题面见 [instruction.md](instruction.md)，输入语义见 [DATA.md](DATA.md)，解析公式见 [DESIGN.md](DESIGN.md)，逐点设计见 [TEST-CASES.md](TEST-CASES.md)。

32 点包含库埃特／泊肃叶启动、非零初值与驱动叠加、剪切反转、局部正负脉冲、高频初值，以及双周期平移、叠加涡旋和斜向剪切波。空间尺度、材料、网格编码与不等距输出时刻共同变化；全部参考来自连续解析解，Ghia 稳态数据不用于瞬态判分。

## 文件

| 路径 | 用途 |
|---|---|
| `instruction.md` | 简洁题面、范围、输出与完整示例引用 |
| `DATA.md` | 矢量初值、跨壁插值、周期映射、输出时间和压力规范 |
| `DESIGN.md`、`TEST-CASES.md` | 通道级数、二维解析公式与测试点配方，不发布 |
| `cases/<case>/` | Gmsh 网格、JSON 清单和 HDF5 输入 |
| `reference/<case>/reference.h5, analytic.json` | 独立解析参考及参数、截断尾界，不发布 |
| `samples/<sample>/input/, output/` | 零场、非零驱动、双周期初始场的完整公开示例 |
| `judge-config.json` | 固定判分阈值及资源限制 |
| `author/generate.py` | **生成题库**：复用稳态作者工具，生成瞬态输入、解析标答和样例。 |
| `../navier-stokes-steady/author/catalog.py, oracle.py` | **定义数据与解析解**：两题共用的私有参数和参考计算。 |
| `author/baseline.py` | **独立求解**：读取输入、数值积分并计算压力，不读取解析配方或参考值。 |
| `author/check.py` | **运行并判分**：复用作者执行器，逐点记录误差、时间和 RSS。 |
| `harbor/` | 本题 SciPy 依赖及内存限制补充 |

## 出题与验证

沿用[项目 README](../../README.md#运行) 的 Python 环境，在项目根目录执行：

```sh
python legacy/navier-stokes-transient/author/generate.py
python legacy/navier-stokes-transient/author/check.py
```

`generate.py` 覆盖题库及公开样例；`check.py --program <solver.py>` 检查其他求解器。资源与判分报告保存于 `runs/navier-stokes-transient/baseline/`。单文件 baseline 可直接用于独立判题环境。

两题共用的出题侧回归测试见 [legacy/tests/test_navier_stokes.py](../tests/test_navier_stokes.py)，检查初值与边界数据、周期映射、通道级数和二维周期解、压力规范，以及样例判分和公开材料范围。

## 判分与时间

每点所有输出速度绝对误差≤0.02 m/s、压力≤0.02 Pa 得 1 分，rtol=0；单点 5 秒、1,024 MiB，满分 32。

输入时间轴只规定输出时刻，不规定内部步长、CFL 数或每步迭代次数。t=0 速度复用初值，压力仍由方程确定；正时间标答由通道级数或二维周期解析公式生成。
