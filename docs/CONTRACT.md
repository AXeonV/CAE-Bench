# 通用数据协议

本文定义通用存储与引用规则。每题的 instruction.md 给出任务、资源和评分，DATA.md 完整定义本题物理字段、条件、采样及观测；考生只需阅读这三份文件。Schema 和校验工具用于检查实现，不作为补足题意的阅读前提。

协议描述几何文件、网格、采样位置、时间轴、物理量、场、材料参数以及初始／边界条件的数据关联。它不绑定某个求解器或某道 OJ 题，也不定义求解算法。热传导、流体、结构等任务可以使用同一套数据表示；具体物理或数学问题、支持的条件和判分规则由任务声明。

“必须”表示协议要求；“任务必须声明”表示通用协议不能代替题目的数学定义。格式合法并不意味着求解结果正确。

## 协议版本与物理配置

既有输入省略版本字段，继续使用其题目约定。使用 `contract_version: 2`、`profile: "cfd-2.1"` 的输入必须同时提供 analysis、materials；四键成组出现且禁止 physics。各题 DATA.md 就地定义所需的分析与材料结构、合法参数和条件，不要求阅读额外领域规范。

使用 physics 的领域输入通过 physics.model 显式声明模型；准确标识、parameters 的全部参数、条件及相容性在本题 DATA.md 列明。第二章的 fluid-energy-、fluid-multiphase-、fluid-reduced- 版本化模型禁止同时出现 contract_version、profile、analysis、materials。模型不由 task 或文件名推断；复用通用结构不表示忽略领域声明检查。

新增结构须通过 Schema 声明，不能自行添加未知字段。通用检查与物理配置检查分别报告结构错误和声明相容性错误；均不证明物理解或数值结果正确。

## 1. 文件分工与格式选择

| 内容 | 文件 | 职责 |
|---|---|---|
| 问题与元数据 | `problem.json` | 声明文件引用、物理模型、参数、条件、字段含义和输出要求 |
| 几何，可选 | `.geo`、`.step/.stp`、`.brep` | 复用 Gmsh 几何描述或 CAD 文件，不在 JSON 中重新定义 CAD |
| 网格 | Gmsh `.msh` | 节点、坐标、单元、连接关系、几何实体和 Physical Groups |
| 输入数组 | 一个 `.h5` | 实体编号、时间、独立采样点坐标及输入场 |
| 输出数组 | 一个 `.h5` | 必需输出场及固定编号／时间轴，不重复导出网格和元数据 |

场数据固定使用标准 HDF5，文件扩展名为 `.h5`。每个数组对应根组 `/` 下的一个 dataset，例如 key `velocity` 对应 `/velocity`；JSON 中只写 `velocity`，不带 `/`。使用 HDF5 官方 C/C++ 库或 Python h5py 即可读写，无需专用二进制编码器。[HDF5 数据集接口](https://docs.h5py.org/en/stable/high/dataset.html)

文件必须自包含且为扁平结构：只允许根组中的具名 dataset，不允许子组、软链接、外部链接、多个名称指向同一 dataset、外部存储或虚拟 dataset。根组和 dataset 不带属性，物理量、单位、轴含义和条件只由 `problem.json` 声明。dataset 的实际 shape 就是数组逻辑 shape，不以一维缓冲区加额外元数据代替。

协议中的 `float64` 对应 IEEE 754 双精度浮点，`int64` 对应有符号 64 位整数，`bool` 对应 HDF5 枚举（底层有符号 8 位整数，`FALSE=0`、`TRUE=1`，即 h5py 的 NumPy `bool` dataset），不能用整数 0/1 dataset 代替 bool。大小端均可。字符串、复合类型、变长类型、对象及引用不属于协议数组；其他数值 dtype 也不能替代声明的 dtype。

可使用连续存储或分块存储；压缩只允许 HDF5 标准 gzip（deflate），可附加无损 shuffle 和 Fletcher32 校验。不得使用有损 scale-offset 或额外插件过滤器。分块大小、压缩级别和文件内部布局不影响语义；提交前须完成写入并关闭文件。

数据包示例：

```text
case/
  problem.json
  mesh.msh
  mesh.geo       # 可选
  input.h5
```

文件名没有隐含物理意义，实际名称由 JSON 声明。清单中的路径必须相对 `problem.json` 所在目录，使用 `/` 分隔；禁止绝对路径、盘符、反斜杠、空路径段及 `.`、`..` 路径段。不能通过符号链接引用包外文件。程序改变工作目录不影响引用含义。

## 2. 元数据清单

JSON 必须是 UTF-8、无重复键、无 NaN/Inf 的标准 JSON。整数型元数据必须使用整数，`2.0` 和 `true` 都不是维度整数。

顶层及各记录对象只允许 Schema 定义的字段。`geometries`、`meshes`、`locations`、`time_axes`、`fields`、`outputs` 的条目名，以及 `physics.parameters` 的参数名和条件 `data` 的参数名，由任务定义，使用 `[A-Za-z][A-Za-z0-9_]*`，区分大小写。HDF5 key 也遵守该命名规则。`task`、`physics.model`、`quantity`、`variable`、`operator` 是任务定义的非空字符串，不是通用校验器内置的物理名称枚举。

| 顶层字段 | 类型 | 要求与含义 |
|---|---|---|
| `task` | string | 可选，任务标识；通用校验器不按它限制物理模型 |
| `spatial_dimension` | integer | 必填，1、2 或 3；决定独立点坐标和空间场的分量 |
| `data_file` | string | 必填，输入 HDF5 的相对路径 |
| `geometries` | object | 必填，几何文件表，可为 `{}` |
| `meshes` | object | 必填，网格表，可为 `{}`；独立点数据不必有网格 |
| `locations` | object | 必填，采样位置表 |
| `time_axes` | object | 必填，时间轴名到输入 HDF5 key 的映射 |
| `fields` | object | 必填，输入场描述表 |
| `outputs` | object | 必填，要求输出的场描述表；不要求存在对应输入场 |
| `physics` | object | 任务模型标识与全局标量参数；CFD 配置使用 analysis/materials |
| `contract_version`、`profile` | integer、string | CFD 配置显式启用标记，见版本说明 |
| `analysis` | object | CFD 分析类型、等温约束、压力表示及物理时间范围 |
| `materials` | object | CFD 区域材料、密度与流变响应 |
| `conditions` | array | 必填，条件记录，可为 `[]` |

例如 `fields.velocity` 是元数据对象名，里面的 `array: "u_values"` 才是 HDF5 key。引用场使用对象名，访问数值使用数组 key，二者可以不同。

一个清单可以声明多个网格、多个位置和多个时间轴。不同表中的对象名分别拥有自己的命名空间。

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

固定采用 **Gmsh MSH 4.1 ASCII**，`$MeshFormat` 下一行必须为 `4.1 0 8`（版本 4.1、ASCII 编码、数据尺寸 8 字节）。所有题目使用这一种网格编码；校验器拒绝其他版本、binary 编码或数据尺寸，不做自动转换。Gmsh 导出时设置 `Mesh.MshFileVersion=4.1`、`Mesh.Binary=0`。读取和单元节点顺序直接采用 Gmsh 标准，协议不提供另一份单元类型目录或 JSON 连接关系。

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

`ids` 指向输入 HDF5 中的 `int64[N]`。编号必须非空、唯一且严格递增，必须属于引用网格的节点。没有 `physical_group` 时，数组明确给出所选节点，可以是全部节点或子集，不猜测覆盖范围。

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

`probe_ids` 为非空、严格递增的非负 `int64[N]`，身份只在该 location 内有效，不引用 Gmsh tag。`probe_coordinates` 为有限的 `float64[N,D]`，单位 m、分量按 x/y/z 顺序。探针、评测点、显式单元中心点均可这样表示；协议不猜测中心或执行插值。

第 i 个场值始终对应 IDs 数组第 i 项。不得按网格文件读取顺序、坐标位置或自行生成的编号解释场。

### 4.4 区域整体观测

`{"kind":"aggregate","source":"boundary_faces","ids":"observation_ids","operation":"sum"}` 声明一个整体观测。source 必须引用 mesh element location，不能循环引用或指向另一聚合位置；ids 是恰含一项的 int64 观测编号。sum 对应 integral，mean 对应 average；输出仍为 `[T,1,*component_shape]`，不使用伪造的采样点坐标。聚合位置不用于条件。物理积分、平均的定义由本题 DATA.md 说明，协议校验器不自动计算结果。

### 4.5 离散实体身份

`{"kind":"entities","ids":"body_ids"}` 表示没有固定空间采样坐标的离散对象表，例如刚体、关节、有限维模态系统；不是网格节点、空间探针或区域聚合。记录恰含kind、ids，不能携带coordinates、mesh、entity、source或其他键。ids为非空、非负、严格递增int64[N]，身份仅在该location内有效。字段仍为[T,N,*component_shape]，value_kind固定point，表示该对象自身的状态或属性，不表示连续空间点值、区域平均或积分。不同实体间没有默认插值、距离或邻接关系。

每题DATA必须明确对象含义、跨location引用、状态分量及离散参数解释；数值位置若是物理未知量，使用有明确单位的字段。此类型不自动赋予任意广义坐标或物理模型语义，也不能替代已有网格区域聚合。结果和SDK沿用相同ID／时间复制规则，不导出伪坐标。该表示为向后兼容的新增分支，不改变既有mesh、points、aggregate含义。

## 5. 时间轴

```json
{"steady": "times", "transient": "transient_times"}
```

每个 key 引用输入 HDF5 中的非空 `float64[T]`，单位固定为 s，数值有限且严格递增。允许负时间。稳态采用 T=1，通常使用 `[0.0]`；时间值由清单数据确定。

所有场保留时间轴，没有“无时间维”的另一种表示。同一数据包可有不同时间轴，每个场显式引用自己的轴。协议只定义这些时刻上的采样，不自动定义时间插值、外推或迭代步数。

瞬态任务可分别声明 T=1 的初始场时间轴和含多个时刻的输出时间轴。**输出时刻不等于求解器的内部时间步**；固定／自适应步长、稳定性限制及每步迭代策略是否由输入约束，必须由任务明确。当前协议不内置算法控制参数，也不从输出时间轴推断这些参数。

## 6. 场数组与物理量

输入 `fields` 与 `outputs` 使用相同的描述结构，下列字段均必填：

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
| `array` | 对应 HDF5 key；输入场从输入 HDF5 取值，输出场从结果 HDF5 取值 |
| `quantity` | 物理量名称，由任务定义，例如 temperature、velocity、stress |
| `location` | 已声明的 location 名称 |
| `time_axis` | 已声明的时间轴名称 |
| `dtype` | `float64`、`int64` 或 `bool`，禁止隐式类型转换 |
| `kind` | `scalar`、`vector`、`tensor` 或 `components` |
| `component_shape` | 分量轴形状，每个长度为正整数 |
| `components` | 分量标签，数量等于分量形状乘积，标签唯一 |
| `unit` | 必填、非空的单位代码，见第 7 节 |
| `value_kind` | `point`、`average` 或 `integral`，定义采样含义 |

输入场可声明 `sampling`，其结构为 `{ "space": "uniform", "time": "constant", "extrapolation": "forbid" }`。space 可取 uniform、piecewise_constant、piecewise_linear；time 可取 constant、linear、previous；extrapolation 可取 forbid、hold。具体允许组合、空间重建、时间重建和外推的物理含义由本题 DATA.md 完整定义；不能只按枚举名推断。题目要求显式 sampling 时不得省略；旧任务没有该字段时按本题 DATA.md 的连续解释，不由 SDK 猜测。

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

节点、独立点和离散实体只允许 `point`；单元只允许 `average` 或 `integral`。整体观测使用 4.4 节约定的 average／integral。单元中心点值必须提供独立 point location，避免同一“cell value”被默认为不同含义。

场数组必须是规则数值 ndarray，禁止 object、字符串、复数、结构化 dtype。浮点值必须有限。整数／布尔场也使用相同的时间、实体、分量轴。不得省略轴、展平或隐式广播。

输入 HDF5 必须恰好包含 locations 的 IDs／点坐标、time_axes 的时间数组、fields 的输入场数组；不允许未引用数组。一个 key 不能同时代表不同角色。不同位置显式引用同一个 IDs 数组、不同时间轴引用同一时间数组是允许的。

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

`physics.model` 是显式任务模型标识。给定 PDE 的题目须明确其数学模型；以物理描述定义的 CAE 题目须明确物理与方法要求及 Agent 的建模责任，不默认要求预先列出方程。CFD 配置通过 analysis/materials 区分分析要求和物理材料信息，不与 physics 重复声明。每个参数是带单位的有限标量，不在 JSON 中存大数组。空间变化材料系数、源项等使用输入场，由条件记录引用。协议不内置全部物理量名称，也不根据名称猜测方程或数值范围。

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
| `operator` | 条件类型名称，任务或物理配置必须列出允许名称和精确的物理／数学含义 |
| `data` | 参数到类型化数据的映射。旧格式不得为空；CFD 配置的无参数条件允许空对象 |

通用数值数据使用以下两种表示：

```json
{"value": 100.0, "unit": "K"}
```

表示在该 location 上均匀且不随时间变化的标量。它是明确的常量类型，不是对场数组的隐式广播。

```json
{"field": "left_temperature"}
```

引用 `fields.left_temperature`，旧格式中其 location 必须与条件完全一致，单位、时间、分量从场描述继承。CFD 配置还允许引用同网格上恰好覆盖条件实体区域的节点集合，按其显式 sampling 重建并求实体平均，不以节点数相等代替几何覆盖。变化的边界数据、矢量和张量条件统一存 HDF5；均匀矢量也用显式场表示，不增加内联数组格式。

还可用 `{"option":"forbid"}` 表达类别选项，或 `{"location":"partner"}` 引用另一已声明位置。二者不能代替数值或携带可执行表达式；允许的参数、选项及位置关系必须由条件规范声明。类别值不能塞入带单位的数值参数。

边界条件通过 `location` 指定作用位置：网格位置引用 `.msh` 实体／Physical Groups，独立点位置引用 HDF5 坐标。条件类型存 JSON，变化数值存 HDF5。初始场用 `role: "initial"` 引用；均匀标量初值可写带单位常数。

以下是算子名称及数学含义的示例。**通用协议不按 `operator` 固定 `data` 内的参数名**；每道题必须在自己的 DATA.md 中完整列出允许条件、物理／数学含义、全部必需／可选参数及其数据表示，不能要求考生追踪章节共享说明或领域配置文档。

| role / operator | 含义 |
|---|---|
| initial / assign | 起始时刻赋值；任务指定时刻，通常引用 T=1 初始场 |
| boundary / dirichlet | 指定变量值，例如 `T=g` |
| boundary / normal_derivative | 指定计算域向外单位法向导数，例如 `∂T/∂n=g` |
| boundary / normal_flux | 指定向外通量，例如热传导 `-k∇T·n=g` |
| boundary / robin | 例如 `αT+β∂T/∂n=g`；α、β、g 的表示和参数名由任务定义 |
| source / assign | 方程源项赋值，任务明确其在方程中的符号 |
| material / assign | 区域材料系数赋值 |

求解器需支持该题声明的算子及数据表示。上面的 `dirichlet` JSON 仅演示均匀标量常量，不规定所有题目都使用 `data.value`。自定义算子也必须由任务定义精确含义及参数名。条件列表顺序不代表优先级，多条记录同时声明约束；角点重合、材料界面、作用时间范围等规则由题目明确，校验器不推断或消解冲突。

离散场仅定义指定实体／点和时刻上的值。若求解需要其他位置或时刻，题目必须说明使用方法或插值规则，不能把采样自动当成解析函数。当前协议不接受可执行函数、任意代码或未定义表达式字符串。

## 9. 输出与唯一性

`outputs` 是完整输出语义声明，由输入清单固定。结果 HDF5 仅包含：

1. 每个输出场 `array` 指定的数值数组。
2. 每个输出场 location 的 IDs 数组，与输入的 dtype、shape、值和顺序一致。
3. 每个输出场 time_axis 的时间数组，同样与输入完全一致。

共享的 IDs／时间 key 只存一份。不重复输出点坐标、网格、无关输入场或字段元数据。所有额外或缺失 key 均不合法。字段 key 不能同时代表 ID、时间或坐标；`fields` 表内各场的 `array` 必须互不相同，`outputs` 表内亦然。输入 HDF5 和结果 HDF5 是不同文件，两者可以使用相同的场数组 key。

唯一性体现为：每个字段只有一个位置、时间、单位、分量和 dtype 声明；IDs 递增且输出使用给定轴；稳态、标量、张量只有一种逻辑形状；组由 `(dimension, tag)` 标识。校验器不接受重排、不同编号或另一张等价网格。

**不要求文件字节唯一。**HDF5 分块、允许的无损压缩、字节序和文件内部布局可不同，标准读取器恢复同一 dtype、shape 和索引值即可。HDF5 不声明 NumPy 的 C/F 内存顺序；写入时必须让 dataset 的各轴符合协议，不能靠内存布局改变轴含义。校验器不实施转置或数据重排。形状相同而数值放错位置属于数值错误，结构校验不能推断其原意。

校验器能发现错误 shape、轴长度、dtype、编号／时间及引用。它不能发现合法结构中的内容错误：shape 没变的转置、交换 u/v、使用正确 IDs 却填入其他节点的值。这些属于答案内容，由判分器处理。

## 10. 完整二维速度回传示例

下面清单对应 `mesh.msh` 节点场。其他任务可改变输入场、物理条件和输出要求；协议没有 echo 专属 Schema。

```json
{
  "task": "smoke-test",
  "spatial_dimension": 2,
  "data_file": "input.h5",
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
import h5py

with h5py.File("input.h5", "w") as data:
    data.create_dataset("node_ids", data=np.array([10, 20, 30], dtype=np.int64))
    data.create_dataset("times", data=np.array([0.0], dtype=np.float64))
    data.create_dataset("velocity", data=np.array(
        [[[1.0, 101.0], [2.0, 202.0], [-3.0, 303.0]]], dtype=np.float64))
```

`velocity[0,1,1] == 202.0` 表示 t=0 s、tag=20 节点的 y 方向速度为 202 m/s。

直接读取和写入，无需 SDK：

```python
from pathlib import Path
import json
import h5py

input_path = Path("case/problem.json")
metadata = json.loads(input_path.read_text(encoding="utf-8"))
with h5py.File(input_path.parent / metadata["data_file"], "r") as data, h5py.File("result.h5", "w") as result:
    for key in ("node_ids", "times", "velocity"):
        result.create_dataset(key, data=data[key][()])
```

SDK 是可选帮助：

```python
from caeoj.sdk import load_problem, read_field, write_result

problem = load_problem("case/problem.json")
# problem.manifest 为元数据，problem.arrays 为 key -> ndarray。
# SDK 不执行转置、dtype 转换或数值纠正。
velocity = read_field(problem, {"field": "velocity"})
output_key = problem.manifest["outputs"]["velocity"]["array"]
write_result("result.h5", problem, {output_key: velocity.copy()})
```

| SDK 接口 | 输入与返回值 |
|---|---|
| `read_constant(data)` | 接收 `{"value": 100.0, "unit": "K"}`，返回其中的数值；单位字符串保留在 data 中，不换算单位 |
| `read_field(problem, reference)` | 接收 `{"field": "velocity"}`，按 `fields.velocity.array` 找到 HDF5 数组并返回；保留完整时间、位置、分量轴与 dtype |
| `write_result(path, problem, fields)` | `fields` 为输出 HDF5 key → ndarray 的映射，key 必须取自 `outputs.<名称>.array`，不使用输出对象名代替；自动复制必需 IDs／时间轴并校验输出 |

读取接口用于 `load_problem` 已校验的元数据，数据来源类型不符会报错。
`load_problem` 和 `load_result` 完整读取并关闭 HDF5 文件，返回内存中的 NumPy 数组；`read_field` 返回其中的原数组，修改前可调用 `.copy()`。需要按片读取输入或逐时刻写入结果时，可直接使用 h5py 的 dataset 切片／HDF5 hyperslab，仍须遵守同一 dataset 名称、dtype 和完整 shape。SDK 不求值边界函数、不插值、不修正数值。

C/C++ 程序同样使用 HDF5 dataset：例如创建 rank=3、dims=`{T,N,2}` 的 `H5T_IEEE_F64LE` dataset，再按 `[t,i,c]` 写入速度；IDs 使用 `H5T_STD_I64LE`。镜像提供 `libhdf5-dev`、`h5cc`／`h5c++` 和 `h5dump`。当前 Python h5py 使用串行 HDF5；MPI 计算不要求并行写文件，可由一个 rank 汇总写入。MPI 并行 HDF5 I/O 不在当前环境的保证范围内。

SDK 写入时复制必需的 IDs／时间轴；判分时仍独立重新校验文件，不信任程序是否调用 SDK。

## 11. 校验与判分的边界

激活自行配置的 Python 环境后运行；路径按实际输入文件填写。

```sh
python -m caeoj validate-input 'problem.json'
python -m caeoj validate-output --input 'problem.json' --output 'result.h5'
```

校验返回纯 JSON，退出码 0 合法、1 不合法，CLI 参数错误为 2：

```json
{
  "valid": false,
  "errors": [{
    "code": "E_SHAPE", "path": "$h5.velocity",
    "expected": [1, 9, 2], "actual": [1, 2, 9],
    "message": "Does not match the declared contract."
  }]
}
```

| 错误码 | 检查内容 |
|---|---|
| E_JSON / E_DUPLICATE_KEY | JSON 读取及重复键 |
| E_SCHEMA | 元数据字段、类型和枚举 |
| E_FILE / E_MESH / E_HDF5 | 文件引用及标准载荷能否读取 |
| E_REFERENCE | 网格、位置、时间轴、条件场、tag、组等引用 |
| E_ARRAY / E_ARRAYS | 单数组引用、别名冲突及整体 key 集合 |
| E_SHAPE / E_DTYPE / E_COMPONENTS | 数组形状、dtype、分量约定 |
| E_ID / E_TIME / E_ORDER | 编号唯一性／顺序、时间顺序及固定输出轴 |
| E_FINITE | 非有限数值 |
| E_DIMENSION / E_METADATA | 维度或跨字段声明不一致 |
| E_FLUID | 第二章显式领域配置的参数、单位、状态、采样及条件相容性 |
| E_CFD | 显式 CFD 配置的单位、范围、条件、材料及跨字段声明不相容 |

通用校验器检查结构和声明，不修改数据，不重排或匹配等价网格。显式 CFD 配置另检查规定的单位、材料范围、条件覆盖和声明相容性。它们不验证 CAD、网格质量、PDE、守恒、完整物理适用性或解误差。

判分由独立模块 `src/caeoj/grading.py` 实现，输出与参考 HDF5 必须满足同一个输出契约。可通过公开 `grading.json` 配置按字段的逐值容差、RMSE、NRMSE、最大误差和超限比例，并用 AND／OR 组合条件。本题 instruction.md 必须完整给出实际采用的指标、聚合范围、阈值和任何固定偏置；不需要考生另读评分规范来补足判据。grading.json 是对应的机器配置，这些评分参数不进入 problem.json 物理输入。

未提供评分策略时，浮点场逐分量使用：

`|result-reference| ≤ atol + rtol·|reference|`

`atol`、`rtol` 由题目明确并在评测前固定，全部值通过才得 1 分。整数／布尔场必须完全一致；IDs 和时间轴必须与输入精确一致，评分策略不能放宽这些要求。

使用评分策略：

```sh
python -m caeoj grade --input 'problem.json' --output 'result.h5' --reference 'reference.h5' --grading 'grading.json'
```

使用逐值容差：

```sh
python -m caeoj grade --input 'problem.json' --output 'result.h5' --reference 'reference.h5' --atol '<atol>' --rtol '<rtol>'
```

不提供 `--grading` 时仍可使用 `--atol`、`--rtol`；两种方式不能同时指定。`grade` 退出码为 0（通过）、1（答案错误或非法输出）、2（输入／参考数据错误或配置、命令参数错误）。参考输出由出题方提供，不要求与输入场相同。

判分与结构诊断分开：`validate-output` 不比较参考值。参考数据错误不能算作选手失分，报告 score 为 null。

## 12. 支持范围与扩展规则

当前支持固定网格与固定采样位置下的 Gmsh 网格／分组、HDF5 场数组、时间轴、带单位参数及条件记录。网格运动、自适应拓扑、局部坐标基、连续体额外自由度／积分点和通用连续表达式求值尚未定义；离散对象状态可用4.5节entities及任务定义的components表示。周期等专用条件可由题目通过已有条件记录定义，并明确网格中的配对关系；通用协议尚未统一其物理语义。

**通用条件机制不等于全部边界语义都已定义。** 各题 DATA.md 必须就地说明边界函数表示、坐标／法向、算子参数和条件组合；不得依靠额外协议引用补足。同一存储结构不代表支持任意物理或边界组合。校验器检查通用结构及已实现的领域声明相容性，不验证数值解。

题目必须明确字段和条件的物理／数学含义，不能将离散场样本隐式视为连续函数。新增通用数据结构须同步更新文档、Schema、校验器及样例，并验证程序能按声明读取和处理。
