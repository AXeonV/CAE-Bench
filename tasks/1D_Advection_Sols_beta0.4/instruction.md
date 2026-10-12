# 一维周期平流

在区间 `[0,1] m` 上求无量纲标量状态 u：

`∂u/∂t + c ∂u/∂x = 0`，`c = 0.8 m/s`。

两端周期连接。输入给出等距单元上的初值；初始时刻每个单元内 u 为给定常数。求指定时刻各单元的平均值。输入遵守[通用数据协议](../../docs/CONTRACT.md)，具体字段与条件见 [DATA.md](DATA.md)。

## 输入范围

| 项目 | 范围 |
|---|---|
| 网格 | Gmsh MSH 4.1，一阶线单元，1024 个等长单元覆盖 `[0,1]` |
| 初值 | float64 标量单元场 `[1,1024,1]`，绝对值不超过 5 |
| 边界 | 周期边界，周期长度 1 m，在整个时间区间生效 |
| 输出时刻 | 201 个 float64 时刻，从 0 到 2 s，间隔约 0.01 s，以输入数组为准 |

内部时间步与求解方法由程序选择。编号只表示实体身份，不表示几何次序。

## 输出与判分

接口：`python solve.py --input problem.json --output result.npz`。

输出 float64 单元平均场 `state[201,1024,1]`，原样附带输入中的 `cell_ids` 和 `times`。t=0 的结果为初值。

每点所有要求值的绝对误差均不超过 **0.08** 得 1 分，否则 0 分。12 点满分 12。

单点限时 **5 秒**，包括启动、读写及计算。容器 CPU 和内存由评测环境默认分配，无额外固定配额。

## 示例

完整输入：[samples/01/input/](samples/01/input/)，入口 [problem.json](samples/01/input/problem.json)。完整正确输出：[samples/01/output/result.npz](samples/01/output/result.npz)。

另一组完整初值与输出：[samples/02/input/](samples/02/input/) 和 [samples/02/output/result.npz](samples/02/output/result.npz)。两组均包含全部 1024 个单元与 201 个时刻。

