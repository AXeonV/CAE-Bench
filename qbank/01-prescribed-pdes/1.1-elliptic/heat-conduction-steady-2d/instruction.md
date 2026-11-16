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

输入使用 Gmsh 网格、HDF5 数组及 JSON 元数据，遵守[通用数据协议](../../../../docs/CONTRACT.md)。源项为至多二次多项式，边界右端为至多四次多项式；输入给出 NumPy 升幂系数。字段读取和函数定义见[输入说明](DATA.md)，该说明是题目的一部分。

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

对每个请求输出物理量、每个标量分量和每个请求时刻，分别沿空间位置计算加权归一化均方根误差：

`e = sqrt(sum_i(w_i*(a_i-r_i)^2)/sum_i(w_i)) / max(sqrt(sum_i(w_i*r_i^2)/sum_i(w_i)), scale_floor)`。

`a_i` 为提交值，`r_i` 为参考值；采用下述已声明的评分变换或参考尺度偏置时，按对应定义代入。不同物理量、分量或时刻分别计算空间 NRMSE，不拼接原始数值。本例的 `total NRMSE` 定义为全部这些 `e` 的等权均方根 `E=sqrt(sum(e_j^2)/M)`，其中 `M` 为 NRMSE 组数，全部请求时刻均参与，包括初始帧；全部观测位置均参与，包括边界及零值。

每例连续得分：`E <= 0.05` 得 1 分；`0.05 < E < 0.10` 得 `(0.10-E)/0.05` 分；`E >= 0.10` 得 0 分。题目 reward 为全部正式 case 得分的算术平均值，不按字段数量或空间点数量给 case 加权。

空间位置采用等点权重 `w_i=1`；这是对请求观测位置的误差评价，不推断网格体积或积分权重。单个整体观测也使用该规则。

除 DATA 明确声明的评分变换外，候选和参考均按规定表示直接比较，不平移、去均值、拟合比例或对齐场。

`scale_floor` 是与本输出同单位的正数下限，防止零参考或很小的参考导致除零或尺度失控。本题明确采用：

| quantity | scale_floor | 单位 |
|---|---|---|
| `temperature` | 0.01 | `K` |

IDs、时间轴、shape、dtype 和有限值要求仍须严格满足；整数及布尔输出精确比较。程序失败、超时、超资源、缺失或非法输出得 0 分；输入、参考或评价基础设施错误不算考生失分。守恒、低残差和正常退出不替代目标观测准确性。

每例墙钟时间上限 **4 秒**，内存上限 **24 GiB**（按 1 MB=2²⁰ 字节计）。

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

随机格式输出目录：[samples/01/output/](samples/01/output/)，格式文件为 [result.h5](samples/01/output/result.h5)。文件包含以下全部数组：

```text
node_ids    int64   [9]     = [1, 2, 3, 4, 5, 6, 7, 8, 9]
times       float64 [1]     = [0.0]
temperature float64 [1,9,1]，数值为随机数，不是温度解
```

## 示例 2：四种边界条件

完整输入：[samples/02/input/](samples/02/input/)，入口为 [problem.json](samples/02/input/problem.json)。
随机格式输出：[samples/02/output/result.h5](samples/02/output/result.h5)。

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

格式输出只含 `node_ids`、`times`、`temperature`；IDs和时间轴原样复制，`temperature` 为随机 float64 `[1,9,1]` 数组，不表示本例温度解。

## 公开格式样例

`samples/01/`、`samples/02/` 仅展示输入与输出结构。其 `output/result.h5` 为随机生成的格式示例，只保证数组结构、dtype、IDs和时间轴符合输入要求，不保证数值答案正确，也不作为本地数值判分依据。正式case使用独立的隐藏参考判分。

运行资源：8 vCPU；考生 Agent、编译与样例运行共享 24 GiB 内存预算；正式判分时，提交程序及其全部子进程合计内存上限为 24 GiB（25769803776 字节）。逐例墙钟时限和输出限制按本题规定执行，正式求解不联网。
