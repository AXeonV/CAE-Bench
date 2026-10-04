# 二维瞬态热传导

给定矩形域、常数导热系数 k、常数体积热容 C、初始温度和四条边的条件，求指定时刻所有网格节点的温度 T：

`C ∂T/∂t = k(Txx + Tyy)`，t > 0，无热源。

初始温度由网格节点值给出，在每个三角形内按线性函数解释。边界条件随时间不变，n 为向外单位法向：

| `operator` | 边界方程 |
|---|---|
| `dirichlet` | T=0 |
| `normal_derivative` | ∂T/∂n=0 |
| `normal_flux` | −k∂T/∂n=0 |
| `robin` | αT+β∂T/∂n=0 |

Dirichlet 边界的初始节点温度为零。其他条件要求在 t>0 满足，不要求初始场在边界上的法向导数相容。初始温度可以为负。

## 输入范围

输入遵守[通用数据协议](../../docs/CONTRACT.md)，字段含义见 [DATA.md](DATA.md)。

| 项目 | 范围 |
|---|---|
| 矩形 | x0,y0∈[−5,5] m；Lx,Ly∈[0.5,3] m，长短边比≤3 |
| 材料 | 0.05≤k≤20 W/(m·K)；0.5≤C≤20 J/(m³·K) |
| 网格 | Gmsh MSH 4.1 ASCII 或 binary，一阶三角形和边界线段；9～8,000 节点，8～16,000 三角形 |
| 初始温度 | float64 节点值，绝对值≤10 K |
| Robin | 0.1≤α≤10 W/(m²·K)，0.05≤β≤20 W/(m·K) |
| 输出时刻 | float64，6～12 个，含 t=0，严格递增，末时刻≤4,000 s |
| 首个正输出时刻 | `(k/C)t₁ / max(Lx,Ly)² ≥ 0.003` |

网格和边界分组保证一致，无孤立或退化单元。输入给出的时间轴只规定输出时刻；程序自行选择内部固定或自适应时间步、迭代和收敛策略，满足精度与资源要求。

## 输出与判分

接口：`python solve.py --input problem.json --output result.npz`。

输出包含原样复制的 `node_ids`、`times`，以及 float64 `temperature`，shape `[输出时刻数,节点数,1]`，单位 K。第一个时间层必须是输入初始节点温度。

每点全部时刻、全部节点绝对误差≤**0.02 K** 得 1 分，否则 0 分。24 点满分 24；单点限时 **5 秒**，内存 **1,024 MB**（按 1 MB=2²⁰ 字节计）。

## 示例

完整输入：[samples/01/input/](samples/01/input/)，入口 [problem.json](samples/01/input/problem.json)。
完整正确输出：[samples/01/output/result.npz](samples/01/output/result.npz)。

本例为单位正方形、k=C=1，9 个节点，四边定温为零，初始温度全零。
输出 `node_ids=int64([1,2,3,4,5,6,7,8,9])`，`times=float64([0,0.003,0.007,0.016,0.035,0.08])`，`temperature` 为全零的 float64 `[6,9,1]` 数组。

另有包含初始温度及四种边界条件的完整示例：[samples/02/input/](samples/02/input/) 和 [samples/02/output/result.npz](samples/02/output/result.npz)。
