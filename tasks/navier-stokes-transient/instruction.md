# 二维瞬态有粘不可压缩流

给定矩形域、密度 ρ、动力粘度 μ、体加速度 a、初始速度和边界条件，求指定时刻的速度 **u=(u,v)** 和压力 p：

`ρ(∂u/∂t+(u·∇)u) = −∇p + μΔu + ρa`，`∇·u=0`。

密度、粘度、边界条件和体加速度不随时间变化。初始速度由输入节点场给定。

## 边界条件

| `operator` | 条件 |
|---|---|
| `dirichlet` | t>0 的壁面速度 u=g |
| `periodic` | 配对边的速度、压力及对应导数相等 |
| `mean` | 各时刻域内面积平均压力为零 |

边界为一对相对边周期、另一对壁面给定恒定切向速度，或两对相对边均周期。初始速度不必与突然施加的壁速在 t=0 相容；初始值用于 t=0，壁面条件从 t>0 起实施。

## 输入范围

输入使用 Gmsh 网格、NPZ 数组和 JSON 元数据，遵守[通用数据协议](../../docs/CONTRACT.md)。初始场的连续含义及条件字段见 [DATA.md](DATA.md)，该说明是题目的一部分。

| 项目 | 范围 |
|---|---|
| 矩形 | x0,y0∈[−2,2] m；0.5≤Lx,Ly≤2 m，长短边比≤4；双周期域为正方形 |
| 材料 | 0.5≤ρ≤2 kg/m³；0.005≤μ/ρ≤0.05 m²/s |
| 速度与驱动 | 壁面速度绝对值≤1 m/s；初始速度各分量绝对值≤2 m/s；恒定体加速度各分量绝对值≤0.2 m/s²；Re≤100 |
| 网格 | Gmsh MSH 4.1 ASCII，等距点阵的一阶三角形；单周期 25～4,225 节点，双周期 289～4,225 节点；32～8,192 三角形 |
| 输出时刻 | 6～8 个，float64，含 t=0 且严格递增，末时刻≤100 s |
| 首个正时刻 | 单周期通道 `(μ/ρ)t₁/H²≥0.001`，H 为两壁距离；双周期域 `t₁/L≥0.005 s/m` |

节点 tag 可能不连续，周期对应关系在 `.msh` 的 `$Periodic` 段中。

程序自行选择内部固定或自适应步长、稳定性限制和迭代收敛策略；给定时间轴只规定输出时刻。

## 输出与判分

接口：`python solve.py --input problem.json --output result.npz`。

输出原样复制 `node_ids`、`times`，并提供 float64 `velocity[T,N,2]`（m/s，x/y 顺序）、`pressure[T,N,1]`（Pa）。t=0 的速度为输入给定的初始节点速度；压力由方程约束决定，输入不提供初始压力。

每点全部时刻、节点、速度分量绝对误差≤**0.02 m/s**，压力绝对误差≤**0.02 Pa**，得 1 分，否则 0 分。32 点满分 32；单点限时 **5 秒**，内存 **1,024 MiB**。限时包含提交进程启动、输入读取、计算和输出写入。

## 示例 1

### 示例输入

完整输入目录：[samples/01/input/](samples/01/input/)，入口 [problem.json](samples/01/input/problem.json)。包含 `problem.json`、`mesh.geo`、`mesh.msh`、`input.npz`。

本例为单位正方形，ρ=1、μ=0.01，25 个节点；左右周期、上下静止，初始速度和体加速度全零，`times=[0,0.1,0.3,1,3,10,30]`。

### 示例输出

完整正确输出：[samples/01/output/result.npz](samples/01/output/result.npz)。包含 float64 全零 `velocity[7,25,2]`、`pressure[7,25,1]`，以及原样复制输入的 `node_ids=int64[25]`、`times=float64[7]`。

## 示例 2、3

运动壁面与非零驱动的完整示例：[samples/02/input/](samples/02/input/) 与 [samples/02/output/result.npz](samples/02/output/result.npz)。双周期非零初始场的完整示例：[samples/03/input/](samples/03/input/) 与 [samples/03/output/result.npz](samples/03/output/result.npz)。
