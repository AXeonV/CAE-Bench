# 稳态热传导输入与输出说明

本说明是题目的一部分，采用[通用数据协议](../../../../docs/CONTRACT.md)，规定本题的字段、引用关系和数学含义。取值范围与判分要求见[题面](instruction.md)。

## 文件与入口

程序接收 `problem.json` 的路径。清单通过 `meshes.main.file` 引用网格，通过 `data_file` 引用 HDF5；路径相对于清单所在目录解析。输入使用 `mesh.msh`、`input.h5`，可附 `mesh.geo`。

`task="heat-conduction-steady-2d"`、`spatial_dimension=2`、`physics.model="steady_heat_conduction"`。网格固定为 MSH 4.1 ASCII，一阶三角形和边界线段；连接关系以 `.msh` 为准。`mesh.geo` 仅为可选几何文件，无需重新划分网格。

附带几何文件时，`geometries.rectangle={"file":"mesh.geo","format":"gmsh-geo"}`，并由 `meshes.main.geometry="rectangle"` 引用。

## 参数与平均温度

以下参数均位于 **`physics.parameters`**，每项都是 `{"value": 数值, "unit": 单位字符串}` 对象；不是裸数，也不存放在 HDF5 或 `conditions` 中。

| 参数名 | 含义 | `unit` | 出现条件 |
|---|---|---|---|
| `conductivity` | 常数导热系数 k | `W/(m.K)` | 必有 |
| `x0`、`y0` | 矩形左下角坐标 | `m` | 必有 |
| `length_x`、`length_y` | 沿 x、y 的长度 Lx、Ly | `m` | 必有 |
| `mean_temperature` | 域平均温度 `∫Ω T dΩ / (Lx·Ly)` | `K` | 当且仅当四边的 `operator` 均属于 `normal_derivative`、`normal_flux` 时必有 |

`mean_temperature` 的结构例如以下清单片段；其余必有参数仍需同时提供：

```json
{
  "physics": {
    "model": "steady_heat_conduction",
    "parameters": {
      "mean_temperature": {"value": 2.3, "unit": "K"}
    }
  }
}
```

四边可以混合法向导数和热流。只要任意一边为 `dirichlet` 或 `robin`，输入就**不含** `mean_temperature`；字段缺省不表示平均温度为零。该参数约束域积分平均，不是网格节点值的算术平均。

## 网格位置、编号与时间轴

所有 `locations` 项均为 `kind="mesh"`、`mesh="main"`；`nodes` 不声明 `dimension`，其他位置声明下表中的单元维度。记 N 为全部节点数、E 为域三角形数，M_side 为某条边的线段数。

| `locations` 名称 | `entity` | 维度 | Physical Group `(dimension, tag)` | HDF5 中的 `ids` |
|---|---|---|---|---|
| `nodes` | `node` | — | 不指定；包含全部节点 | `node_ids` |
| `domain` | `element` | 2 | `(2,1)` | `domain_ids` |
| `left` | `element` | 1 | `(1,2)` | `left_ids` |
| `right` | `element` | 1 | `(1,3)` | `right_ids` |
| `bottom` | `element` | 1 | `(1,4)` | `bottom_ids` |
| `top` | `element` | 1 | `(1,5)` | `top_ids` |

边界的 `*_ids` 是**线段单元 tag，不是边界节点 tag**。坐标和单元的节点连接关系从 MSH 读取；tag 可以不连续，不等于数组下标。每个 IDs 数组均为 int64、严格递增；场的位置轴按其引用的 IDs 排列。

`time_axes={"steady":"times"}`，HDF5 中 `times=float64([0.0])`。本题没有初始条件，所有输入场与输出场均引用 `steady`，保留长度为 1 的时间轴。

## HDF5 数组与字段描述

下表中的 `<side>` 分别替换为 `left`、`right`、`bottom`、`top`；例如 `left_ids`、`left_coefficients`，输入中不存在字面名称 `<side>_ids`。

| HDF5 key | dtype | shape | 含义 |
|---|---|---|---|
| `node_ids` | int64 | `[N]` | 全部节点 tag |
| `domain_ids` | int64 | `[E]` | 域三角形 tag |
| 四个 `<side>_ids` | int64 | `[M_side]` | 各边的全部线段 tag |
| `times` | float64 | `[1]` | `[0.0]` |
| `source_coefficients` | float64 | `[1,E,3,3]` | 源项多项式系数 |
| 四个 `<side>_coefficients` | float64 | `[1,M_side,5]` | 各边右端函数 g 的多项式系数 |

`fields` 声明五个系数字段。字段名、`array` 和 `quantity` 均使用相同的 `source_coefficients` 或 `<side>_coefficients` 名称。条件中的 `{"field": 名称}` 引用 **`fields` 中的字段名**，再通过该字段的 `array` 找到 HDF5 key。

| 字段 | `location` | `component_shape` | `components` | `unit` |
|---|---|---|---|---|
| `source_coefficients` | `domain` | `[3,3]` | `c00,c01,c02,c10,c11,c12,c20,c21,c22` | `W/m3` |
| 四个 `<side>_coefficients` | 对应边 | `[5]` | `c0,c1,c2,c3,c4` | 由该边的算子决定，见下表 |

五个字段均为 `time_axis="steady"`、`dtype="float64"`、`kind="components"`、`value_kind="average"`。这些是**系数的字段描述**：所有域三角形的系数矩阵相同，同一边所有线段的系数向量相同；数组中不是 q 或 g 的采样值、积分值或单元平均值。常系数在单元上的平均值就是该系数本身。

## 源项条件与函数

`conditions` 是无序列表，包含一条源项记录和四条边界记录。所有记录的 `variable` 均为 `temperature`；不能用列表下标推断记录角色或边界位置。

源项记录完整结构为：

```json
{
  "role": "source",
  "variable": "temperature",
  "location": "domain",
  "operator": "polynomial",
  "data": {"coefficients": {"field": "source_coefficients"}}
}
```

令 `u=(x−x0)/Lx`、`v=(y−y0)/Ly`。`source_coefficients[0,e,i,j]` 是第 e 个域单元上的 `u^i v^j` 系数，定义连续函数：

`q(x,y)=Σ C[i,j]u^i v^j`，i,j=0,1,2，i+j>2 的系数为零；方程为 `−k(Txx+Tyy)=q`。

两个分量轴分别对应 u、v 的幂，按 NumPy `numpy.polynomial.polynomial.polyval2d` 的升幂约定。例如 `C[0,0]=2`、`C[1,0]=3`、`C[0,1]=−1`，其余为零，表示 `q=2+3u−v`。

## 四种边界条件及字段

每条边恰有一条边界记录，公共字段为 `role="boundary"`、`variable="temperature"`、`location=边的位置名`、`operator=算子名`、`data=该算子的数据对象`。下面列出各算子的全部 `data` 字段；`alpha`、`beta` 位于 `data` 内，不在条件顶层或 `physics.parameters` 中。

| `operator` | 边界方程 | `data` 中的字段 | 被引用系数字段的 `unit` |
|---|---|---|---|
| `dirichlet` | `T=g` | `coefficients={"field":"<side>_coefficients"}` | `K` |
| `normal_derivative` | `∂T/∂n=g` | `coefficients={"field":"<side>_coefficients"}` | `K/m` |
| `normal_flux` | `−k∂T/∂n=g` | `coefficients={"field":"<side>_coefficients"}` | `W/m2` |
| `robin` | `αT+β∂T/∂n=g` | `coefficients={"field":"<side>_coefficients"}`、`alpha`、`beta` | `W/m2` |

Robin 的 `alpha`、`beta` 均为正的常量对象，分别为 `{"value": 数值, "unit": "W/(m2.K)"}`、`{"value": 数值, "unit": "W/(m.K)"}`。其他三种算子的 `data` 不含这两项。本题边界右端统一通过 `coefficients` 提供，没有 `data.value`；即使 g 是常数或零，也使用五个多项式系数。

下面是分别作用于四条边的完整边界记录示例，也对应公开样例 02 的 JSON 结构。任一边均可采用四种算子之一；更换边时须同时更换 `location` 和系数字段引用，并按算子设置系数字段单位。

```json
[
  {
    "role": "boundary",
    "variable": "temperature",
    "location": "left",
    "operator": "dirichlet",
    "data": {"coefficients": {"field": "left_coefficients"}}
  },
  {
    "role": "boundary",
    "variable": "temperature",
    "location": "right",
    "operator": "normal_derivative",
    "data": {"coefficients": {"field": "right_coefficients"}}
  },
  {
    "role": "boundary",
    "variable": "temperature",
    "location": "bottom",
    "operator": "normal_flux",
    "data": {"coefficients": {"field": "bottom_coefficients"}}
  },
  {
    "role": "boundary",
    "variable": "temperature",
    "location": "top",
    "operator": "robin",
    "data": {
      "coefficients": {"field": "top_coefficients"},
      "alpha": {"value": 1.0, "unit": "W/(m2.K)"},
      "beta": {"value": 1.0, "unit": "W/(m.K)"}
    }
  }
]
```

`<side>_coefficients[0,e,i]` 是该边第 e 条线段上 s 的 i 次幂系数，定义 `g(s)=Σ c[i]s^i`，i=0,…,4。例如 `[1,2,0,0,0]` 表示 `g=1+2s`。

多项式自变量 s 在左右边取 v，在上下边取 u，均是沿**整条边**的归一化坐标，与线段局部坐标、节点连接方向无关。向外单位法向分别为 left=(−1,0)、right=(1,0)、bottom=(0,−1)、top=(0,1)。各算子中的导数均为对物理坐标 x、y 的导数。

Dirichlet 角点值保证一致。角点邻接 Dirichlet 和其他边时，节点温度取 Dirichlet 值；其他条件施加于对应边的内部，不额外施加角点方程。

## SDK 读取示例

下面只展示数据读取；接口不求值多项式或选择求解方法，返回数组保留完整 shape：

```python
from caeoj.sdk import load_problem, read_constant, read_field

problem = load_problem("problem.json")
manifest = problem.manifest
parameters = manifest["physics"]["parameters"]
k = read_constant(parameters["conductivity"])

source = next(c for c in manifest["conditions"] if c["role"] == "source")
source_coefficients = read_field(problem, source["data"]["coefficients"])

boundaries = {c["location"]: c for c in manifest["conditions"]
              if c["role"] == "boundary"}
for side, condition in boundaries.items():
    coefficients = read_field(problem, condition["data"]["coefficients"])
    if condition["operator"] == "robin":
        alpha = read_constant(condition["data"]["alpha"])
        beta = read_constant(condition["data"]["beta"])

if "mean_temperature" in parameters:
    mean_temperature = read_constant(parameters["mean_temperature"])
```

## 输出与诊断

`outputs.temperature` 声明 `array="temperature"`、`quantity="temperature"`、`location="nodes"`、`time_axis="steady"`、`dtype="float64"`、`kind="scalar"`、`component_shape=[1]`、`components=["value"]`、`unit="K"`、`value_kind="point"`。

输出 HDF5 只包含 `node_ids`、`times`、`temperature`。前两者原样复制输入；温度 shape 为 `[1,N,1]`，`temperature[0,i,0]` 对应 tag=`node_ids[i]` 的节点温度。无需输出系数、边界 IDs、平均温度或额外诊断数组。

可用 `caeoj validate-input problem.json` 和 `caeoj validate-output --input problem.json --output result.h5` 检查读写格式。它们只检查通用数据协议结构，不验证本题的参数范围、边界组合、方程、条件相容性或数值正确性，不纠正答案。
