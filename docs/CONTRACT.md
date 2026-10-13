# 通用数据协议

本文是通用数据协议的规范性说明，与 `src/caeoj/problem.schema.json` 和结构校验器共同定义输入输出契约。

协议描述几何文件、网格、采样位置、时间轴、物理量、场、材料参数以及初始／边界条件的数据关联。它不绑定某个求解器或某道 OJ 题，也不定义求解算法。热传导、流体、结构等任务可以使用同一套数据表示；具体方程、支持的条件和判分规则由任务声明。

“必须”表示协议要求；“任务必须声明”表示通用协议不能代替题目的数学定义。格式合法并不意味着求解结果正确。

## 1. 文件分工与格式选择

| 内容 | 文件 | 职责 |
|---|---|---|
| 问题与元数据 | `problem.json` | 声明文件引用、物理模型、参数、条件、字段含义和输出要求 |
| 几何，可选 | `.geo`、`.step/.stp`、`.brep` | 复用 Gmsh 几何描述或 CAD 文件，不在 JSON 中重新定义 CAD |
| 网格 | Gmsh `.msh` | 节点、坐标、单元、连接关系、几何实体和 Physical Groups |
| 输入数组 | 一个 `.npz` | 实体编号、时间、独立采样点坐标及输入场 |
| 输出数组 | 一个 `.npz` | 必需输出场及固定编号／时间轴，不重复导出网格和元数据 |

场数据选用 NumPy NPZ。NPZ 是多个具名 NPY 数组的标准容器，NPY 已保存 dtype、shape、字节序和存储布局。协议只补充数组语义，不重新定义数值存储格式。[NumPy 格式规范](https://numpy.org/doc/stable/reference/generated/numpy.lib.format.html)

| 候选 | 适用情形 | 当前选择 |
|---|---|---|
| NPZ | 小到中等规模数据，Python 直接读取多维数组 | 唯一场数据载荷格式，易于生成和检查 |
| HDF5 | 大规模场、分块读取、逐步追加及部分 I/O | 确有需求再定义载荷约定，不加入当前流程 |
| VTK/XDMF | 网格与场的交换、可视化 | 可作为后续导出格式，当前不要求提交 |

以上是针对本项目的选择。HDF5 有成熟的分块和部分 I/O 能力；VTK/XDMF 有现成的网格与场表达。当前协议使用固定 Gmsh 网格和简单数组读写，不同时引入多种载荷。[HDF5 分块说明](https://portal.hdfgroup.org/documentation/hdf5/latest/hdf5_chunking.html)、[VTK 格式](https://docs.vtk.org/en/latest/vtk_file_formats/vtkxml_file_format.html)、[XDMF 数据模型](https://www.xdmf.org/index.php/XDMF_Model_and_Format)

数据包示例：

```text
case/
  problem.json
  mesh.msh
  mesh.geo       # 可选
  input.npz
```

文件名没有隐含物理意义，实际名称由 JSON 声明。清单中的路径必须相对 `problem.json` 所在目录，使用 `/` 分隔；禁止绝对路径、盘符、反斜杠、空路径段及 `.`、`..` 路径段。不能通过符号链接引用包外文件。程序改变工作目录不影响引用含义。

## 2. 元数据清单

JSON 必须是 UTF-8、无重复键、无 NaN/Inf 的标准 JSON。整数型元数据必须使用整数，`2.0` 和 `true` 都不是维度整数。未定义字段不允许出现。表中对象名称及 NPZ key 使用 `[A-Za-z][A-Za-z0-9_]*`，区分大小写。

| 顶层字段 | 类型 | 要求与含义 |
|---|---|---|
| `task` | string | 可选，任务标识；通用校验器不按它限制物理模型 |
| `spatial_dimension` | integer | 必填，1、2 或 3；决定独立点坐标和空间场的分量 |
| `data_file` | string | 必填，输入 NPZ 的相对路径 |
| `geometries` | object | 必填，几何文件表，可为 `{}` |
| `meshes` | object | 必填，网格表，可为 `{}`；独立点数据不必有网格 |
| `locations` | object | 必填，采样位置表 |
| `time_axes` | object | 必填，时间轴名到输入 NPZ key 的映射 |
| `fields` | object | 必填，输入场描述表 |
| `outputs` | object | 必填，要求输出的场描述表；不要求存在对应输入场 |
| `physics` | object | 可选，模型标识与全局标量参数 |
| `conditions` | array | 必填，条件记录，可为 `[]` |

例如 `fields.velocity` 是元数据对象名，里面的 `array: "u_values"` 才是 NPZ key。引用场使用对象名，访问数值使用数组 key，二者可以不同。

一个清单可以声明多个网格、多个位置和多个时间轴。不同表中的对象名分别拥有自己的命名空间。NPZ key 不得使用 NumPy 写入接口的保留参数名 `file`、`allow_pickle`。

## 3. 几何与网格

### 3.1 几何文件

```json
{"shape": {"file": "geometry/domain.geo", "format": "gmsh-geo"}}
```

`format` 只允许 `gmsh-geo`、`step`、`brep`，扩展名分别为 `.geo`、`.step/.stp`、`.brep`。Gmsh 负责几何与网格划分。[Gmsh 官方文档](https://gmsh.info/doc/texinfo/gmsh.html)

几何文件保留几何来源；**求解时离散位置和连接关系以提交的 `.msh` 为准**。网格记录可用 `geometry` 引用几何表，但不是必填字段。协议不要求求解器重新划分网格。几何校验只检查引用、扩展名和文件存在，不执行 `.geo`，不解析 CAD，也不验证几何与网格一致性。

### 3.2 网格文件

```json
{"main": {"file": "meshes/domain.msh", "geometry": "shape"}}
```

固定采用 **Gmsh MSH 4.1**，允许官方 ASCII 和 binary 编码。读取和单元节点顺序直接采用 Gmsh 标准，协议不提供另一份单元类型目录或 JSON 连接关系。

- Gmsh 节点 tag、单元 tag 是身份，不是数组下标；必须为正且能由 `int64` 表示。
- 节点和单元各有自己的 tag 空间；不同网格也各有自己的 tag 空间。
- 坐标必须有限，长度采用 m，全局笛卡尔坐标。Gmsh 坐标始终为 XYZ 三列，独立点坐标为 D 列。D=1/2 的任务采用全局 x/xy 表示，未使用的 Gmsh 坐标必须为零；嵌入三维的曲线／曲面采用 D=3。
- 网格拓扑维度不能大于 `spatial_dimension`。二维曲面嵌入三维时，拓扑维度为 2，空间维度为 3。
- 结构化划分同样导出 `.msh`，所有场按 tag 关联，不另定义隐式网格索引。
- 边、面、体通过 Gmsh 单元及其维度表示。未导出的内部边／面没有可引用的单元 tag；需要相关场时，出题方必须导出对应实体或提供独立点。
- Physical Group 由 **`(dimension, tag)`** 唯一标识。名称是辅助说明，不决定边界条件；必须保留所需边界单元和区域单元。

高阶网格节点也沿用 Gmsh tag。节点场表示节点上的采样值，不表示未声明基函数的有限元自由度。

## 4. 采样位置与实体编号

每个场引用一个 `location`，明确哪些实体对应场的 N 轴。

### 4.1 网格节点或节点子集

```json
{
  "nodes": {"kind": "mesh", "mesh": "main", "entity": "node", "ids": "node_ids"},
  "left": {
    "kind": "mesh", "mesh": "main", "entity": "node", "ids": "left_ids",
    "physical_group": {"dimension": 1, "tag": 2}
  }
}
```

`ids` 指向输入 NPZ 中的 `int64[N]`。编号必须非空、唯一且严格递增，必须属于引用网格的节点。没有 `physical_group` 时，数组明确给出所选节点，可以是全部节点或子集，不猜测覆盖范围。

声明 `physical_group` 时，IDs 必须恰好是该组单元涉及的全部节点，按 tag 递增，包括高阶节点。节点 location 不允许写单元 `dimension`；组的 dimension 可以是边界或区域的维度。

### 4.2 单元、边或面

```json
{
  "boundary_edges": {
    "kind": "mesh", "mesh": "main", "entity": "element", "dimension": 1,
    "ids": "edge_ids", "physical_group": {"dimension": 1, "tag": 3}
  },
  "cells": {
    "kind": "mesh", "mesh": "main", "entity": "element", "dimension": 2,
    "ids": "cell_ids"
  }
}
```

`entity: "element"` 必须给出 `dimension`（0～3）；IDs 指向对应维度的 Gmsh 单元 tag，可以混合多种单元类型。声明组时，其维度必须一致，IDs 恰好覆盖该组的单元；没有组时，IDs 定义显式子集。

### 4.3 独立采样点

```json
{"probes": {"kind": "points", "ids": "probe_ids", "coordinates": "probe_coordinates"}}
```

`probe_ids` 为严格递增的非负 `int64[N]`，身份只在该 location 内有效，不引用 Gmsh tag。`probe_coordinates` 为有限的 `float64[N,D]`，单位 m、分量按 x/y/z 顺序。探针、评测点、显式单元中心点均可这样表示；协议不猜测中心或执行插值。

第 i 个场值始终对应 IDs 数组第 i 项。不得按网格文件读取顺序、坐标位置或自行生成的编号解释场。

## 5. 时间轴

```json
{"steady": "times", "transient": "transient_times"}
```

每个 key 引用输入 NPZ 中的非空 `float64[T]`，单位固定为 s，数值有限且严格递增。允许负时间。稳态采用 T=1，通常使用 `[0.0]`；时间值由清单数据确定。

所有场保留时间轴，没有“无时间维”的另一种表示。同一数据包可有不同时间轴，每个场显式引用自己的轴。协议只定义这些时刻上的采样，不自动定义时间插值、外推或迭代步数。

瞬态任务可分别声明 T=1 的初始场时间轴和含多个时刻的输出时间轴。**输出时刻不等于求解器的内部时间步**；固定／自适应步长、稳定性限制及每步迭代策略是否由输入约束，必须由任务明确。当前协议不内置算法控制参数，也不从输出时间轴推断这些参数。

## 6. 场数组与物理量

输入 `fields` 与 `outputs` 使用相同的描述结构：

```json
{
  "array": "velocity", "quantity": "velocity", "location": "nodes",
  "time_axis": "steady", "dtype": "float64", "kind": "vector",
  "component_shape": [2], "components": ["x", "y"],
  "unit": "m/s", "value_kind": "point"
}
```

| 字段 | 规则 |
|---|---|
| `array` | 对应 NPZ key；输入场从输入 NPZ 取值，输出场从结果 NPZ 取值 |
| `quantity` | 物理量名称，由任务定义，例如 temperature、velocity、stress |
| `location` | 已声明的 location 名称 |
| `time_axis` | 已声明的时间轴名称 |
| `dtype` | `float64`、`int64` 或 `bool`，禁止隐式类型转换 |
| `kind` | `scalar`、`vector`、`tensor` 或 `components` |
| `component_shape` | 分量轴形状，每个长度为正整数 |
| `components` | 分量标签，数量等于分量形状乘积，标签唯一 |
| `unit` | 必填、非空的单位代码，见第 7 节 |
| `value_kind` | `point`、`average` 或 `integral`，定义采样含义 |

设时间数为 T、实体数为 N、空间维度为 D。**数组形状统一为 `[T,N,*component_shape]`**：

| kind | component_shape | 数组形状 | 分量标签 |
|---|---|---|---|
| scalar | `[1]` | `[T,N,1]` | 固定 `["value"]` |
| vector | `[D]` | `[T,N,D]` | 全局 `["x", "y", "z"]` 的前 D 项 |
| tensor | `[D,D]` | `[T,N,D,D]` | 全局二阶完整张量；二维固定 xx、xy、yx、yy |
| components | 显式正整数形状 | `[T,N,*shape]` | 按任务声明的顺序，例如多个组分 |

二维速度 `velocity[t,i,0]` 为 u，`velocity[t,i,1]` 为 v；二维张量 `stress[t,i,0,1]` 为 xy 分量。张量标签按最后分量轴变化最快的逻辑索引顺序枚举，与文件的物理存储顺序无关。对称张量也提交完整矩阵，不使用隐含的 Voigt 或工程剪切表示。

非空间分量（多个组分、复数实部／虚部、任务定义的矩阵）使用 `components`，明确 shape、标签和数学含义。`vector`、`tensor` 专用于全局笛卡尔空间量，不暗示局部基。

`value_kind` 的规则：

- `point`：节点或独立采样点的点值。
- `average`：Gmsh 单元所代表实体上的平均值。
- `integral`：该实体上的积分值，单位包含积分后的量纲。

节点和独立点只允许 `point`；单元只允许 `average` 或 `integral`。单元中心点值必须提供独立 point location，避免同一“cell value”被默认为不同含义。

场数组必须是规则数值 ndarray，禁止 object、字符串、复数、结构化 dtype。浮点值必须有限。整数／布尔场也使用相同的时间、实体、分量轴。不得省略轴、展平或隐式广播。

输入 NPZ 必须恰好包含 locations 的 IDs／点坐标、time_axes 的时间数组、fields 的输入场数组；不允许未引用数组。一个 key 不能同时代表不同角色。不同位置显式引用同一个 IDs 数组、不同时间轴引用同一时间数组是允许的。

## 7. 单位、参数与物理模型

坐标固定 m，时间固定 s。其他物理量用大小写敏感的 [UCUM 单位代码](https://ucum.org/ucum) 声明，采用 SI 单位，例如：

| 物理量 | unit |
|---|---|
| 无量纲量 | `1` |
| 温度 | `K` |
| 速度 | `m/s` |
| 压力或应力 | `Pa` |
| 导热系数 | `W/(m.K)` |
| 热流密度 | `W/m2` |
| 体热源 | `W/m3` |

同一任务为每个物理量选定一种代码，禁止隐式换算和默认归一化。无量纲问题使用 `1`，题目明确尺度和数学定义。

简单校验器只检查单位存在且非空，不解析 UCUM、不判断量纲或比较物理单位相容性。代码有效性和单位选用由任务编制时固定。输出不重新声明单位，直接继承 `outputs`。

全局标量参数直接存 JSON：

```json
{
  "model": "steady_heat",
  "parameters": {"conductivity": {"value": 1.5, "unit": "W/(m.K)"}}
}
```

`physics.model` 标识模型，对应方程必须由题目明确给出。每个参数是带单位的有限标量，不在 JSON 中存大数组。空间变化材料系数、源项等使用输入场，由条件记录引用。协议不内置全部物理量名称，也不根据名称猜测方程或数值范围。

## 8. 边界条件、初始条件、源项与材料

每个条件明确 role、作用变量、位置、算子及数据来源：

```json
{
  "role": "boundary", "variable": "temperature", "location": "left",
  "operator": "dirichlet", "data": {"value": {"value": 100.0, "unit": "K"}}
}
```

| 字段 | 含义 |
|---|---|
| `role` | `boundary`、`initial`、`source`、`material` |
| `variable` | 作用的变量／物理量，可以是尚未求出的变量 |
| `location` | 已声明的位置，不由组名称猜测 |
| `operator` | 数学操作名称，任务必须列出允许名称和精确定义 |
| `data` | 参数名到带单位常数或输入场引用的映射，不得为空 |

数据来源只有两种表示：

```json
{"value": 100.0, "unit": "K"}
```

表示在该 location 上均匀且不随时间变化的标量。它是明确的常量类型，不是对场数组的隐式广播。

```json
{"field": "left_temperature"}
```

引用 `fields.left_temperature`，其 location 必须与条件完全一致，单位、时间、分量从场描述继承。变化的边界数据、矢量和张量条件统一存 NPZ；均匀矢量也用显式场表示，不增加内联数组格式。

边界位置存 `.msh` 实体／Physical Groups，条件类型存 JSON，变化数值存 NPZ。初始场数值存 NPZ，用 `role: "initial"` 引用；均匀标量初值可写带单位常数。

推荐任务采用以下名称，并写出完整数学定义：

| role / operator | 含义 |
|---|---|
| initial / assign | 起始时刻赋值；任务指定时刻，通常引用 T=1 初始场 |
| boundary / dirichlet | 指定变量值，例如 `T=g` |
| boundary / normal_derivative | 指定计算域向外单位法向导数，例如 `∂T/∂n=g` |
| boundary / normal_flux | 指定向外通量，例如热传导 `-k∇T·n=g` |
| boundary / robin | 例如 `αT+β∂T/∂n=g`，data 提供 alpha、beta、value |
| source / assign | 方程源项赋值，任务明确其在方程中的符号 |
| material / assign | 区域材料系数赋值 |

这是数据约定，不要求求解器实现全部算子。自定义算子可使用，但任务必须定义其数学含义及参数名。条件列表顺序不代表优先级，多条记录同时声明约束；角点重合、材料界面、作用时间范围等规则由题目明确，校验器不推断或消解冲突。

离散场仅定义指定实体／点和时刻上的值。若求解需要其他位置或时刻，题目必须说明使用方法或插值规则，不能把采样自动当成解析函数。当前协议不接受可执行函数、任意代码或未定义表达式字符串。

## 9. 输出与唯一性

`outputs` 是完整输出语义声明，由输入清单固定。结果 NPZ 仅包含：

1. 每个输出场 `array` 指定的数值数组。
2. 每个输出场 location 的 IDs 数组，与输入的 dtype、shape、值和顺序一致。
3. 每个输出场 time_axis 的时间数组，同样与输入完全一致。

共享的 IDs／时间 key 只存一份。不重复输出点坐标、网格、无关输入场或字段元数据。所有额外或缺失 key 均不合法。字段 key 不能同时代表 ID、时间或坐标；同一方向的两个场不能共享 array key。

唯一性体现为：每个字段只有一个位置、时间、单位、分量和 dtype 声明；IDs 递增且输出使用给定轴；稳态、标量、张量只有一种逻辑形状；组由 `(dimension, tag)` 标识。校验器不接受重排、不同编号或另一张等价网格。

**不要求文件字节唯一。**NPZ 压缩、ZIP 元数据、NPY 大小端及正确标记的 C/F 存储顺序可不同，标准读取器恢复同一逻辑数组即可。校验器不自己实施格式归一化或数据重排。

校验器能发现错误 shape、轴长度、dtype、编号／时间及引用。它不能发现合法结构中的内容错误：shape 没变的转置、交换 u/v、使用正确 IDs 却填入其他节点的值。这些属于答案内容，由判分器处理。

## 10. 完整二维速度回传示例

下面清单对应 `mesh.msh` 节点场。其他任务可改变输入场、物理条件和输出要求；协议没有 echo 专属 Schema。

```json
{
  "task": "echo-field",
  "spatial_dimension": 2,
  "data_file": "input.npz",
  "geometries": {},
  "meshes": {"main": {"file": "mesh.msh"}},
  "locations": {
    "nodes": {"kind": "mesh", "mesh": "main", "entity": "node", "ids": "node_ids"}
  },
  "time_axes": {"steady": "times"},
  "fields": {
    "velocity": {
      "array": "velocity", "quantity": "velocity", "location": "nodes",
      "time_axis": "steady", "dtype": "float64", "kind": "vector",
      "component_shape": [2], "components": ["x", "y"],
      "unit": "m/s", "value_kind": "point"
    }
  },
  "outputs": {
    "velocity": {
      "array": "velocity", "quantity": "velocity", "location": "nodes",
      "time_axis": "steady", "dtype": "float64", "kind": "vector",
      "component_shape": [2], "components": ["x", "y"],
      "unit": "m/s", "value_kind": "point"
    }
  },
  "conditions": []
}
```

若网格节点 tag 为 `[10,20,30]`，输入数组可这样生成。该代码演示场写入，不生成网格，IDs 必须来自真实 `.msh`：

```python
import numpy as np

np.savez(
    "input.npz",
    node_ids=np.array([10, 20, 30], dtype=np.int64),
    times=np.array([0.0], dtype=np.float64),
    velocity=np.array([[[1.0, 101.0], [2.0, 202.0], [-3.0, 303.0]]], dtype=np.float64),
)
```

`velocity[0,1,1] == 202.0` 表示 t=0 s、tag=20 节点的 y 方向速度为 202 m/s。

直接读取和写入，无需 SDK：

```python
from pathlib import Path
import json
import numpy as np

input_path = Path("case/problem.json")
metadata = json.loads(input_path.read_text(encoding="utf-8"))
with np.load(input_path.parent / metadata["data_file"], allow_pickle=False) as data:
    np.savez("result.npz", node_ids=data["node_ids"], times=data["times"], velocity=data["velocity"])
```

SDK 是可选帮助：

```python
from caeoj.sdk import load_problem, read_constant, read_field, write_result

problem = load_problem("case/problem.json")
# problem.manifest 为元数据，problem.arrays 为 key -> ndarray。
# SDK 不执行转置、dtype 转换或数值纠正。
velocity = read_field(problem, {"field": "velocity"})
write_result("result.npz", problem, {"velocity": velocity.copy()})
```

| 读取接口 | 输入与返回值 |
|---|---|
| `read_constant(data)` | 接收 `{"value": 100.0, "unit": "K"}`，返回其中的数值；单位字符串保留在 data 中，不换算单位 |
| `read_field(problem, reference)` | 接收 `{"field": "velocity"}`，按 `fields.velocity.array` 找到 NPZ 数组并返回；保留完整时间、位置、分量轴与 dtype |

读取接口用于 `load_problem` 已校验的元数据，数据来源类型不符会报错。
返回的场数组与输入共享数据，修改前可调用 `.copy()`。SDK 不求值边界函数、不插值、不修正数值。

SDK 写入时复制必需的 IDs／时间轴；判分时仍独立重新校验文件，不信任程序是否调用 SDK。

## 11. 校验与判分的边界

激活自行配置的 Python 环境后运行；路径按实际输入文件填写。

```sh
python -m caeoj validate-input 'problem.json'
python -m caeoj validate-output --input 'problem.json' --output 'result.npz'
```

校验返回纯 JSON，退出码 0 合法、1 不合法，CLI 参数错误为 2：

```json
{
  "valid": false,
  "errors": [{
    "code": "E_SHAPE", "path": "$npz.velocity",
    "expected": [1, 9, 2], "actual": [1, 2, 9],
    "message": "Does not match the declared contract."
  }]
}
```

| 错误码 | 检查内容 |
|---|---|
| E_JSON / E_DUPLICATE_KEY | JSON 读取及重复键 |
| E_SCHEMA | 元数据字段、类型和枚举 |
| E_FILE / E_MESH / E_NPZ | 文件引用及标准载荷能否读取 |
| E_REFERENCE | 网格、位置、时间轴、条件场、tag、组等引用 |
| E_ARRAY / E_ARRAYS | 单数组引用、别名冲突及整体 key 集合 |
| E_SHAPE / E_DTYPE / E_COMPONENTS | 数组形状、dtype、分量约定 |
| E_ID / E_TIME / E_ORDER | 编号唯一性／顺序、时间顺序及固定输出轴 |
| E_FINITE | 非有限数值 |
| E_DIMENSION / E_METADATA | 维度或跨字段声明不一致 |

校验器检查结构和声明，不修改数据，不重排或匹配等价网格，不验证 CAD、网格质量、PDE、守恒、材料正负、条件物理相容性或解误差。

判分由独立模块 `src/caeoj/grading.py` 实现。判分器接收输出和参考 NPZ，二者都满足同一个输出契约。浮点场逐分量使用：

`|result-reference| ≤ atol + rtol·|reference|`

默认 `atol=1e-6`、`rtol=1e-5`，等号包含在内，每例所有输出场的全部分量都满足阈值才得 1 分，否则 0 分。整数／布尔场必须完全一致；IDs 和时间轴仍由契约校验要求精确一致。报告包含浮点字段最大绝对误差及错误分量数。物理题可在判题前明确并冻结自己的阈值，这些参数不进入通用数据协议。

```sh
python -m caeoj grade --input 'problem.json' --output 'result.npz' --reference 'reference.npz'
```

`grade` 退出码为 0（通过）、1（答案错误或非法输出）、2（输入／参考数据错误或命令参数错误）。参考文件是出题方提供的权威输出数组，包括必要的 IDs 和时间轴，不要求与输入场相同。

判分与结构诊断分开：`validate-output` 不比较参考值。参考数据错误不能算作选手失分，报告 score 为 null。

## 12. 支持范围与扩展规则

当前支持固定网格与固定采样位置下的 Gmsh 网格／分组、NPZ 场数组、时间轴、带单位参数及条件记录。网格运动、自适应拓扑、局部坐标基、额外自由度／积分点和通用连续表达式求值尚未定义。周期等专用条件可由题目通过已有条件记录定义，并明确网格中的配对关系；通用协议尚未统一其物理语义。

**边界条件的表达仍需后续仔细设计，并通过实际求解器验证支持范围。** 重点包括边界函数的表示、坐标／法向约定、算子参数和条件组合。现有条件记录与题目约定是初步方案，不代表已支持任意边界条件；协议的目标是统一求解器程序的数据接口，校验器仍只检查结构。

题目必须明确字段和条件的数学含义，不能将离散场样本隐式视为连续函数。新增通用数据结构须同步更新文档、Schema、校验器及样例，并验证程序能按声明读取和处理。
