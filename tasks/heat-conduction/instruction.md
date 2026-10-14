# 二维稳态热传导

给定矩形域、常数导热系数 k、热源 q 和四条边的边界条件，求所有网格节点的温度 T：

\[
-k\left(T_{xx}+T_{yy}\right)=q(x,y).
\]

本题为稳态，无初始条件，不考虑相变或辐射。温度为线性方程中的数值场，允许零值和负值。

## 边界条件

每条边给出下表的一种条件，n 为**向外单位法向**：

| `operator` | 方程 | g 的单位 |
|---|---|---|
| `dirichlet` | T=g | K |
| `normal_derivative` | ∂T/∂n=g | K/m |
| `normal_flux` | −k∂T/∂n=g | W/m² |
| `robin` | αT+β∂T/∂n=g | W/m² |

四边全为法向导数／热流时，输入另给域平均温度。输入保证边界条件相容且解唯一。

## 输入范围

输入使用 Gmsh 网格、HDF5 数组及 JSON 元数据，遵守[通用数据协议](../../docs/CONTRACT.md)。源项为至多二次多项式，边界右端为至多四次多项式；输入给出 NumPy 升幂系数。字段读取和函数定义见[输入说明](DATA.md)，该说明是题目的一部分。

| 项目 | 范围 |
|---|---|
| 矩形 | x0,y0∈[−5,5] m；Lx,Ly∈[0.5,3] m |
| 导热系数 | 0.05≤k≤20 W/(m·K) |
| 网格 | MSH 4.1 ASCII；一阶三角形及边界线段；节点数 3～20,000，三角形数 1～40,000 |
| 编号 | 正的 int64 tag，可不连续 |
| 系数 | float64；各源项／边界系数绝对值≤10,000（对应字段单位） |
| Robin 参数 | 0.1≤α≤20 W/(m²·K)，0.01≤β≤100 W/(m·K) |
| 平均温度 | [−20,20] K |
| 时间轴 | `times=float64([0.0])` |

网格、矩形参数和边界分组保证一致，输入通过结构校验。

## 输出与判分

程序接口：`python solve.py --input problem.json --output result.h5`。

输出 HDF5 包含原样复制的 `node_ids`、`times`，及 float64 `temperature`，shape `[1,节点数,1]`，按节点 IDs 行序，单位 K。

每测试点所有节点满足 `|T−Tref|≤0.01 K` 得 1 分，否则 0 分。32 个测试点满分 32，单点时间上限 **1 秒**，内存上限 **1024 MB**（按 1 MB=2²⁰ 字节计）。

## 示例 1

### 示例输入

完整输入目录：[samples/01/input/](samples/01/input/)，入口为 [problem.json](samples/01/input/problem.json)。目录包含全部输入文件，无需额外数据：

```text
samples/01/input/
├── problem.json
├── mesh.msh
├── mesh.geo
└── input.h5
```

该输入为单位正方形、k=1、q=0，四边均为 T=4 K；网格有 9 个节点、8 个三角形。

### 示例输出

完整正确输出目录：[samples/01/output/](samples/01/output/)，答案文件为 [result.h5](samples/01/output/result.h5)。文件包含以下全部数组：

```text
node_ids    int64   [9]     = [1, 2, 3, 4, 5, 6, 7, 8, 9]
times       float64 [1]     = [0.0]
temperature float64 [1,9,1] = [[[4.0], [4.0], [4.0], [4.0], [4.0], [4.0], [4.0], [4.0], [4.0]]]
```

## 示例 2：四种边界条件

完整输入：[samples/02/input/](samples/02/input/)，入口为 [problem.json](samples/02/input/problem.json)。
完整正确输出：[samples/02/output/result.h5](samples/02/output/result.h5)。

单位正方形、k=1、q=0，仍为 9 个节点、8 个三角形。四条边分别为：

| 边 | `operator` | 边界方程 | HDF5 中的升幂系数 c |
|---|---|---|---|
| left | `dirichlet` | T=1+y | `[1,1,0,0,0]` |
| right | `normal_derivative` | ∂T/∂n=1 | `[1,0,0,0,0]` |
| bottom | `normal_flux` | −k∂T/∂n=1 | `[1,0,0,0,0]` |
| top | `robin` | T+∂T/∂n=3+x | `[3,1,0,0,0]` |

top 的条件数据为：

```json
{
  "coefficients": {"field": "top_coefficients"},
  "alpha": {"value": 1.0, "unit": "W/(m2.K)"},
  "beta": {"value": 1.0, "unit": "W/(m.K)"}
}
```

输出仍只含 `node_ids`、`times`、`temperature`；按 tag 1～9，温度约为
`[1,2,3,2,1.5,2.5,2.5,1.5,2]` K，完整精度见 HDF5。
