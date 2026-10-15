# CFD 2.1 输入输出配置（通用协议版本 2）

本规范为题库第 2 章 2.1 节的 12 道题提供共同的物理输入和观测语义，不是这些题目的完整题面，也不承诺通用求解器已实现。它建立在 [通用数据协议](CONTRACT.md) 上。每题还必须声明几何、材料、条件、参数、精度与资源的具体支持范围。

## 启用与兼容

新输入显式声明 `contract_version: 2`、`profile: "cfd-2.1"`，并提供 `analysis` 和 `materials`。四者成组出现。既有输入省略这些键，继续使用旧行为；不迁移或改写旧题的模型。

CFD 输入不再声明 `physics`，避免与 `analysis`、`materials` 两套定义冲突。分析与材料描述规定物理对象；`profile` 不指定求解方程实现、软件或数值方法。材料响应已经给定时，考生不能以模型选择自由改变该响应。

本配置覆盖二维平面／三维、稳态／瞬态、单相层流、不可压缩牛顿／广义牛顿流体、等温可压缩常黏度牛顿流体。一个按单元公共面连通的固定流体域，允许内孔和多个障碍物，静止或给定切向运动壁面。暂不涵盖湍流、能量预测、相变、轴对称、变形域或流固反馈。

## 分析声明

```json
{
  "contract_version": 2,
  "profile": "cfd-2.1",
  "analysis": {
    "type": "transient",
    "compressibility": "incompressible",
    "flow_regime": "laminar",
    "temperature": {"value": 300, "unit": "K"},
    "pressure": {
      "representation": "gauge",
      "reference_pressure": {"value": 101325, "unit": "Pa"}
    },
    "time_interval": {"start": 0, "end": 1},
    "pressure_gauge": {
      "kind": "mean", "location": "domain",
      "value": {"value": 0, "unit": "Pa"}
    }
  }
}
```

- `type` 为 `steady` 或 `transient`，不从帧数、文件名或 task ID 推断。稳态禁止 `time_interval`，输出时间轴固定 `[0.0]`，只是存储标记；瞬态必须给出 start < end（秒），输出时刻在区间内，不规定内部时间步。
- `compressibility` 为 `incompressible` 或 `isothermal_compressible`；`flow_regime` 固定 `laminar`。温度为严格正的固定物理温度，不是待求温度或迭代初值。
- 压力统一用 Pa。`absolute` 不带 `reference_pressure`；`gauge` 必须带正的绝对参考压力，`p_absolute = p + reference_pressure`。所有输入压力、输出压力及压力规范使用同一表示；密度响应始终使用绝对压力。
- 不可压缩流若有压力出口或给定牵引，不得再加压力规范；否则必须提供 `pressure_gauge`。`mean` 是完整材料域的面积／体积平均；`point` 引用一个独立点 location（其物理有效性由出题方核查）。它是全局唯一性约束，不是对区域中每个点指定压力。
- 可压缩流禁止 `pressure_gauge`，压力的绝对水平由材料与物理状态确定；不得以任意零均值消除。

## 材料响应

`materials` 是具名对象表，本配置恰好一个材料。`region` 引用覆盖完整流体域的全维单元 location。

```json
{"materials": {"fluid": {
  "region": "domain",
  "density": {"kind": "constant", "parameters": {
    "density": {"value": 1000, "unit": "kg/m3"}
  }},
  "viscosity": {"kind": "newtonian", "parameters": {
    "dynamic_viscosity": {"value": 0.01, "unit": "Pa.s"}
  }}
}}}
```

每种响应使用下面完整且唯一的参数集合；参数均为带单位标量。除可压缩牛顿材料的体黏度允许为零外，所有表列参数严格为正。不能用运动黏度替换动力黏度。

| 密度 kind | parameters | 响应与限制 |
|---|---|---|
| `constant` | `density`：kg/m3 | 不可压缩，ρ 固定 |
| `isothermal_ideal_gas` | `specific_gas_constant`：J/(kg.K) | ρ = p_absolute/(R_specific T) |
| `linear_barotropic` | `reference_density`：kg/m3；`reference_pressure`：Pa；`sound_speed`：m/s | ρ = ρ_ref + (p_absolute − p_ref)/c²；使用范围内绝对压力、密度必须正 |

可压缩材料必须用后两种响应，且黏性为 `newtonian`。不可压缩材料必须用常密度响应。

令 γ̇ = sqrt(2 D:D)，D 为对称速度梯度，γ̇ 单位 1/s。二维平面流表示三维材料的平面运动，未参与运动的方向速度与导数为零，不把材料改成另一种二维本构。

| 黏性 kind | parameters | 动力黏度 μ（Pa.s） |
|---|---|---|
| `newtonian` | `dynamic_viscosity`：Pa.s | μ 固定；可压缩材料还必须给 `bulk_viscosity`：Pa.s，非负，表示体积黏性响应 |
| `power_law` | `reference_viscosity`：Pa.s；`reference_shear_rate`、`minimum_shear_rate`、`maximum_shear_rate`：1/s；`power_index`：1 | μ = μ_ref [clip(γ̇, γ̇_min, γ̇_max)/γ̇_ref]^(n−1)，min ≤ reference ≤ max |
| `cross` | `zero_shear_viscosity`、`infinite_shear_viscosity`：Pa.s；`relaxation_time`：s；`cross_exponent`：1 | μ = μ_inf + (μ_zero−μ_inf)/[1+(λγ̇)^m] |
| `carreau` | 同上，但将 `cross_exponent` 换为 `power_index`：1 | μ = μ_inf + (μ_zero−μ_inf)[1+(λγ̇)²]^((n−1)/2) |
| `carreau_yasuda` | Carreau 参数再加 `transition_index`：1 | μ = μ_inf + (μ_zero−μ_inf)[1+(λγ̇)^a]^((n−1)/a) |

平台型响应要求 μ_zero ≥ μ_inf，Carreau／Carreau–Yasuda 还要求 0 < n ≤ 1。这些标签定义输入材料响应，不要求求解器采用某种离散形式。屈服、黏弹性、触变和空间变化的材料参数尚不在本配置中；若题目需要，须先扩展声明和验证范围，不得只在题面暗示支持。

## 条件与连续数据

所有 CFD 边界统一写 `role: "boundary"`、`variable: "flow"`。每个 location 必须为流体域外边界的线／面单元集合；边界记录应不重不漏地覆盖外边界。角点可共享，边／面不可重叠。外法向从流体指向域外，不依赖表面单元节点的顺逆序。

| operator | data（键集合固定） | 物理含义 |
|---|---|---|
| `no_slip` | `{}` | 静止无滑移壁面 |
| `moving_wall` | `velocity`：m/s 矢量场 | 给定切向壁面速度，无穿透；不移动几何 |
| `slip` | `{}` | 静止不穿透、零切向牵引边界 |
| `symmetry` | `{}` | 平面镜像对称；相关法向通量为零，须由出题方保证几何及工况相容 |
| `velocity` | `velocity`：m/s 矢量场 | 给定流入速度；可压缩流还必须给 `density`：kg/m3 |
| `pressure_outlet` | `pressure`：Pa 标量；`backflow: {"option":"forbid"}` | 给定出口静压，只支持无回流工况。出题方保证出口物理适用性，程序和判分验证不得把实际回流忽略为合法结果；速度外推等数值处理由方法决定 |
| `traction` | `traction`：Pa 矢量场 | 外界施加在流体上的总牵引 σn；本配置仅用于不可压缩流 |
| `flow_rate` | `rate`：严格正的标量常量／空间均匀场；`shape`：正的无量纲标量常量／边界单元场 | 指定体积流入率，切向速度为零。按 `u_i = −Q shape_i n_i / sum_j(shape_j measure_j)` 定义该采样边界上的速度；2D Q 单位 m2/s，3D 为 m3/s。可压缩流还给 `density` |
| `periodic` | `partner: {"location":"other"}`；`translation_x/y[/z]`：m 常量 | 成对互引，平移把本侧映射到对侧，反向平移相反。压力、速度及密度周期，不包含压力跳跃；不按数组行号配对 |

数值数据使用通用常量或 `{field: name}`。场可直接位于条件的单元 location，也可位于覆盖该区域全部节点的同网格 node location；后者必须按实际节点集合匹配，不能按数量或行号猜测。数值采用平均／点值，不接受把实体积分当作边界值。矢量一律引用 HDF5 场；无参数条件使用空 data，无需伪造数值参数。新增 `{option: string}` 表达类别选项、`{location: name}` 表达位置引用，均有结构／引用检查。

- 瞬态必须有 `initial / velocity / assign`，可压缩流还必须有 `initial / density / assign`，data 均为 `value`，覆盖完整材料域。初始密度严格正并满足材料状态范围。初始压力由响应确定，不再独立指定。不可压缩压力也不作为独立物理初值。
- 稳态不接受物理初始条件；求解器的迭代初始化是方法选择，不是待求物理状态。
- `source / velocity / acceleration` 的 `data.value` 引用全域矢量加速度场（m/s2）。多个这样的源项相加；不与单位体积力混用。
- 同一边界只写一个完整流动条件，不通过多条记录隐式覆盖；入口状态、壁面运动和源项的相容性仍需出题方核查。

每个输入场必须有 `sampling: {space, time, extrapolation}`：

| 项 | 值与含义 |
|---|---|
| space | `uniform`：各空间行完全相同，表示均匀场；`piecewise_constant`：网格实体上的平均与实体内常值；`piecewise_linear`：一阶单纯形网格的节点分片线性场 |
| time | `constant`：仅在分析起点给一帧，在整个区间有效；`linear`：相邻样本线性插值；`previous`：在 [t_i,t_(i+1)) 取前值，最后样本时刻取最后值 |
| extrapolation | `forbid`：不允许在采样区间外求值，变化的边界数据须覆盖整个分析区间；`hold`：区间外取最近端值。constant 的单帧按其定义始终有效 |

稳态起点标记为 0；瞬态起点由 time_interval.start 确定。初值仅一帧且在起点。输出时间不控制边界采样时间或内部积分步长。当前不支持任意函数代码、表达式求值或从散点自动推断空间插值。

## 观测与输出

节点／探针点值、单元平均等继续使用通用字段结构。新增整体观测 location：

```json
{"outlet_total": {
  "kind": "aggregate", "source": "outlet_faces",
  "ids": "outlet_total_ids", "operation": "sum"
}}
```

source 引用已有网格单元 location；ids 是一项 int64 观测 ID，不是假探针坐标。输出仍为 `[T,1,*component_shape]`，附带该 ID 和时间轴。`sum` 使用 integral，`mean` 使用 average；平均是 source 所代表区域的面积／体积加权平均。此位置只承载观测，不承载输入条件。

| quantity | kind | unit 与含义 |
|---|---|---|
| `velocity` | vector | m/s |
| `pressure` | scalar | Pa，按 analysis.pressure 表示及规范 |
| `density` | scalar | kg/m3 |
| `dynamic_viscosity` | scalar | Pa.s |
| `shear_rate` | scalar | 1/s，定义同材料响应 |
| `traction` | vector | Pa，外界对流体的 σn，位于外边界单元 |
| `force` | vector | −∫σn，即流体作用于所选边界的力；2D 为 N/m，3D 为 N；只用于边界 sum aggregate |
| `volume_flow` | scalar | ∫u·n，向域外为正；2D 为 m2/s，3D 为 m3/s；只用于边界 sum aggregate |
| `mass_flow` | scalar | ∫ρu·n，向域外为正；2D 为 kg/(m.s)，3D 为 kg/s；只用于边界 sum aggregate |

牵引和载荷中的压力采用声明的压力表示。因此表压结果是相对 reference_pressure 的载荷；若要与外部环境比较，任务须说明环境基准，不能将表压载荷与绝对压力载荷混比。二维量默认每单位出平面厚度，不隐式乘厚度。

强度量可以在 mean aggregate 输出，积分量必须在外边界 sum aggregate 输出。压力差可由两个明确的压力观测在判分端计算，不引入任意输出表达式。每题自行选择必需输出，不强制统一字段名、数组 key 或输出组合。

## 实现与检查范围

`validate-input` 对显式启用的配置自动进行结构及声明相容性检查：材料参数、单位、范围、初始状态、时间覆盖、完整且不重叠的外边界、压力锚定、周期几何配对等。CFD 声明错误返回 `E_CFD`；通用结构错误仍使用原错误码。

支持一阶三角形、四边形、四面体、六面体、棱柱与金字塔流体单元；边界为一阶线段、三角形或平面四边形。分片线性输入场限定单纯形网格，非单纯形可用均匀或实体常值数据。检查不证明网格质量、初值与边界动力学相容、无回流、层流假设、稳态存在、连续问题适定或参考精度。

SDK 提供 `sample_field`、`absolute_pressure`、`fluid_material`、`density_at_pressure`、`dynamic_viscosity`、`boundary_geometry`、`boundary_integral`、`condition_values`、`periodic_face_pairs`。采样助手只做声明的时间重建，不偷偷重建空间场；空间重建按本规范由求解器实现；`condition_values` 可将匹配区域的一阶节点数据精确转换为条件实体平均值。边界积分助手积分的是给定实体平均值，不替代应力、通量的物理计算。

## 可再生示例

```sh
python src/utils/make_cfd_examples.py --output runs/cfd-contract-examples
python -m caeoj validate-input runs/cfd-contract-examples/compressible-3d/problem.json
python -m caeoj validate-output --input runs/cfd-contract-examples/compressible-3d/problem.json --output runs/cfd-contract-examples/compressible-3d/reference.h5
```

四个数据包分别演示二维稳态、三维瞬态、非牛顿及等温可压缩输入，包含静止均匀流的解析参考。它们用于协议验证，不是这 12 道题的覆盖测试，也不验证一般 CFD 数值求解能力。工具只写入不存在或空目录，拒绝覆盖已有数据。
