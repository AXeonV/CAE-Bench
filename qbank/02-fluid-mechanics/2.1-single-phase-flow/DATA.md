# 2.1 单相层流分析：公共数据说明

本说明与 [共同要求](COMMON.md)、各题的 `instruction.md` 和 `DATA.md` 共同定义输入输出。文件结构、JSON／HDF5 类型、Gmsh 编码和引用遵循 [通用协议](../../../docs/CONTRACT.md)。下文完整列明本节物理字段和条件；不需要根据题号、文件名、Physical Group 名称推断物理。

## 读取入口与引用

`problem.json` 声明 `contract_version: 2`、`profile: "cfd-2.1"`、本题 `task` 和 `spatial_dimension`，提供 `analysis`、`materials`，不提供 `physics`。`data_file` 指向输入 HDF5；`meshes` 恰有一个网格，位置与连接关系从该网格读取。`geometries` 可为空，附带几何仅辅助说明，无需执行或重新划分。

`locations`、`time_axes`、`fields`、`outputs` 和材料的对象名，以及数组 key 均由清单给出，不固定命名。条件中的 `{ "field": "inlet_velocity" }` 引用 `fields.inlet_velocity`，再通过其 `array` 找到 HDF5 dataset；不能直接以引用字符串查找数组。`time_axes` 将时间轴名映射到 HDF5 key；场的 `location` 引用位置对象，位置的 `ids` 指向 HDF5 编号数组。

HDF5 为无属性、无子组的根 dataset 集合。编号为严格递增的 int64，时间为严格递增的 float64 秒数；tag 可以不连续，不表示数组下标或坐标顺序。所有数值场为 float64，标量 shape `[T,N,1]`，矢量 `[T,N,D]`，其中 D 为 2 或 3，分量顺序 x、y、z（二维只有 x、y）。T、N 分别来自该场引用的时间轴和位置 IDs。所有值有限，单位不自动换算。

`locations` 支持网格节点、网格单元、独立点，以及下述整体观测。网格单元位置声明 `dimension`，通过 `(dimension, tag)` 引用 Physical Groups（若有）；边界 IDs 是边界单元 tag，不能当作节点。独立点坐标在 HDF5 为 `[N,D]`、单位 m。域内点／节点为点值，域单元为面积／体积平均；边界单元为长度／面积平均。材料的 `region` 引用包含全部流体单元的全维位置。观测点由输入保证位于对应流体区域；不要求在不连续边界交点求导或比较多值牵引。

## 分析与压力

`analysis` 包含：

| 路径 | 类型、取值和出现规则 |
|---|---|
| `type` | `steady` 或 `transient`，由各题限定 |
| `compressibility` | `incompressible` 或 `isothermal_compressible`，由各题限定 |
| `flow_regime` | 固定 `laminar` |
| `temperature` | 正的带单位标量，`{"value":300,"unit":"K"}`，恒定温度 |
| `pressure.representation` | `absolute` 或 `gauge`，单位均为 Pa |
| `pressure.reference_pressure` | 仅 gauge 时必有，正的带单位绝对压力；absolute 时禁止 |
| `time_interval` | 仅 transient 时必有，`{"start":0,"end":1}`，秒，start < end；steady 禁止 |
| `pressure_gauge` | 下述不可压缩压力规范，按条件出现；可压缩禁止 |

表压满足 `p_absolute = p + reference_pressure`。所有输入压力、输出压力和压力规范采用同一表示，密度响应用绝对压力。这里的压力为静压，单位 Pa，不是除以密度的运动学压力或去静水压量。

不可压缩流：有外压牵引出口或给定牵引时不加压力规范；否则必须给出一种：

- `{"kind":"mean","location":"domain","value":{"value":0,"unit":"Pa"}}`：全流体域面积／体积平均压力等于 value，location 必须是材料 region。
- `{"kind":"point","location":"pressure_probe","value":{"value":0,"unit":"Pa"}}`：一个独立点处的压力等于 value，location 是含一个点的独立点位置。

上述对象均为 `analysis.pressure_gauge` 的完整值示例，位置名通过清单解析。规范不等于对整个域逐点赋相同压力。可压缩流的绝对压力水平由状态确定，不允许去均值。

## 材料

`materials` 恰有一个具名对象，含 `region`、`density`、`viscosity`；后两者均含 `kind` 和 `parameters`。parameters 每个参数均为 `{ "value":数值, "unit":单位 }`，使用下表全部且仅有的键。除体黏度可为零，参数严格为正；没有缺省材料参数。材料参数不随位置／时间变化，流动导致的密度或有效黏度变化按给定响应计算。

| density.kind | parameters 与单位 | 密度响应 |
|---|---|---|
| constant | density：kg/m3 | 密度常数，用于全部不可压缩题 |
| isothermal_ideal_gas | specific_gas_constant：J/(kg.K) | ρ = p_absolute/(R T) |
| linear_barotropic | reference_density：kg/m3，reference_pressure：Pa，sound_speed：m/s | ρ = ρ_ref + (p_absolute − p_ref)/c² |

可压缩题支持后两种，所给初态、入口及所求状态的绝对压力和密度均正。

令剪切率 g = sqrt(2 D:D)，D 为对称速度梯度。黏性响应是各向同性的，无额外应力历史；g 的单位为 1/s。动力黏度不可替换为运动黏度。

| viscosity.kind | parameters 与单位 | 动力黏度 μ，单位 Pa.s |
|---|---|---|
| newtonian | dynamic_viscosity：Pa.s；仅可压缩题再加 bulk_viscosity：Pa.s | 常数 μ，体黏度非负 |
| power_law | reference_viscosity：Pa.s；reference_shear_rate、minimum_shear_rate、maximum_shear_rate：1/s；power_index：1 | μ_ref [clip(g,g_min,g_max)/g_ref]^(n−1)；g_min ≤ g_ref ≤ g_max |
| cross | zero_shear_viscosity、infinite_shear_viscosity：Pa.s；relaxation_time：s；cross_exponent：1 | μ_inf + (μ_zero−μ_inf)/(1+(λg)^m) |
| carreau | zero_shear_viscosity、infinite_shear_viscosity：Pa.s；relaxation_time：s；power_index：1 | μ_inf + (μ_zero−μ_inf)[1+(λg)²]^((n−1)/2) |
| carreau_yasuda | Carreau 的全部参数及 transition_index：1 | μ_inf + (μ_zero−μ_inf)[1+(λg)^a]^((n−1)/a) |

平台响应均要求 μ_zero ≥ μ_inf > 0，Carreau／Carreau–Yasuda 要求 0 < n ≤ 1；幂律 n > 0，可剪切变稀或增稠。幂律的剪切率截断就是输入材料的一部分，不能另行加未声明的截断。二维使用三维材料的平面运动响应，不改用二维体积黏性约定。体黏度表示纯体积应变的黏性系数，偏应变黏性从三维迹中去除三分之一的体积应变；它不是第二黏度系数。总应力 σ 由各向同性压应力 −pI、上述剪切黏性应力和体积黏性应力相加得到。不可压缩流的体积应变为零。

各题只接收其 DATA.md 指定的材料种类。这里定义响应以便解释输入，不限定内部求解方法。

## 条件结构

`conditions` 的每条记录含 `role`、`variable`、`operator`、`location`、`data`。data 数值项使用带单位标量常量或 `{"field":"场对象名"}`；矢量必须用场引用。类别用 `{"option":"forbid"}`，位置引用用 `{"location":"对侧位置名"}`，不能作为数值解释。下面所有示例均为条件记录片段，并非完整输入包。

### 边界

全部边界使用 `role: "boundary"`、`variable: "flow"`，location 引用域外边界的线／面单元位置。域外边界包括内孔和障碍物表面。每个边／面恰由一条条件覆盖，条件列表顺序不决定优先级。角点可以共享，但不能用多条记录叠加或覆盖同一面上的流动条件。

外法向 n 从流体指向域外，由域连接关系确定，不依赖边界单元节点排序。各题均支持下表，唯可压缩题不支持 traction。

| operator | data 的完整键集合 | 含义 |
|---|---|---|
| no_slip | `{}` | 静止、无穿透、无滑移壁面 |
| moving_wall | velocity | 给定壁面切向速度场 m/s，流体无滑移；几何固定 |
| slip | `{}` | 静止边界，无穿透且切向牵引为零 |
| symmetry | `{}` | 平面镜像对称，无穿透、零切向牵引；工况满足镜像对称 |
| velocity | velocity；可压缩另加 density | 给定流入速度 m/s；可压缩入口同时给密度 kg/m3 |
| pressure_outlet | pressure、backflow | 外压牵引出口：外部储槽静压 Pa，backflow 固定 `{"option":"forbid"}`，算例保证无回流 |
| traction | traction | 外界作用于流体的总牵引矢量，Pa；仅不可压缩题支持 |
| flow_rate | rate、shape；可压缩另加 density | 正的体积流入率 Q 和正的无量纲形状；可压缩另给入口密度 |
| periodic | partner、translation_x、translation_y；三维另加 translation_z | 平移周期配对；partner 为位置引用，平移分量是单位 m 的标量常量 |

pressure 可为标量常量或标量场；density 同样可为常量或标量场。velocity、traction 为矢量场。

pressure_outlet 定义外部储槽压力产生的总牵引 `σn = −p_ext n`，切向总牵引为零；data.pressure 是 p_ext，采用 analysis.pressure 声明的绝对压／表压表示。它不是额外规定域内边界静压恰好等于 p_ext；法向黏性应力存在时两者可以不同。不要再叠加速度零法向梯度、内部静压赋值或人为出口密度条件。出口只允许流出，算例保证无回流；不得通过忽略回流把不满足该条件的解当作答案。

flow_rate 的 rate 是标量常量或空间均匀标量场（可随时间变化），单位二维 m2/s、三维 m3/s；shape 是标量常量或边界标量场；若采用节点分片线性表示，先按给定连接关系重建并求边界实体平均，再作以下归一化。切向速度为零，边界第 i 个单元的法向速度由 `u_i = −Q shape_i n_i / Σ_j(shape_j measure_j)` 定义；measure 为线长／面积。Q 是整个 location 的总流率，不是每个边界单元的流率。

periodic 两侧各写一条记录，相互引用；translation 把本侧点平移到对侧，两侧平移相反。按几何配对，不按数组行号配对。速度、压力、密度周期，压力无跳跃。缺省不产生压差驱动，需驱动时由源项等显式给出。

无滑移条件片段：

```json
{"role":"boundary","variable":"flow","operator":"no_slip","location":"wall","data":{}}
```

给定可压缩入口的片段：

```json
{"role":"boundary","variable":"flow","operator":"velocity","location":"inlet","data":{"velocity":{"field":"inlet_u"},"density":{"value":1.2,"unit":"kg/m3"}}}
```

其他条件的 data 分别按表列键构造，例如 `{"pressure":{"value":101325,"unit":"Pa"},"backflow":{"option":"forbid"}}` 或 `{"rate":{"value":0.001,"unit":"m3/s"},"shape":{"value":1,"unit":"1"}}`。后一个片段用于三维不可压缩流。

### 初态与体加速度

瞬态必须恰有一条 `initial / velocity / assign`；可压缩流另有一条 `initial / density / assign`。location 为完整材料域，data 恰含 value，值为相应单位的标量常量（仅密度）或场引用。初始场只有起点一帧；不独立给初始压力。可压缩初始压力由密度响应反求，不可压缩压力由条件及压力规范确定。稳态禁止 initial 记录。

```json
{"role":"initial","variable":"velocity","operator":"assign","location":"domain","data":{"value":{"field":"initial_u"}}}
```

可选体加速度使用 `source / velocity / acceleration`，location 为完整材料域，data 恰含 `value`，引用 m/s2 矢量场。多个源相加，未给出则为零；它不是单位体积力。不使用 `role: "material"` 重复声明材料。

## 输入场的空间与时间含义

每个 fields 场必须含 `sampling: {"space":...,"time":...,"extrapolation":...}`。条件场可以与作用区域共用单元 location，也可以引用覆盖该区域全部节点的同网格节点 location；必须按节点集合与 tag 匹配，不按行数猜测。

| 项 | 取值及含义 |
|---|---|
| space | uniform：空间行均相同；piecewise_constant：网格实体平均、实体内常值；piecewise_linear：一阶单纯形网格的节点分片线性场 |
| time | constant：起点一帧，区间内恒定；linear：相邻采样线性插值；previous：在 [t_i,t_(i+1)) 取前帧，最后采样时刻取末帧 |
| extrapolation | forbid：不得在采样区间外求值，变化场覆盖整个分析区间；hold：区间外保持最近端值；constant 按定义一直有效 |

稳态所有输入场仅 `[0.0]` 一帧，sampling.time 必须为 constant；瞬态起点为 time_interval.start。初始场仅表示起始状态，不能按 constant 采样将其强制维持到之后。均匀场和单元常值场适用于全部支持的单元；节点分片线性仅用于单纯形网格。输入节点值为 point，条件单元值为 average，不把 integral 当作边界值。形状相同不意味着数据可以互换。未声明任意函数表达式或散点空间插值。

## 输出

每例 outputs 至少请求一个速度场和一个压力场，可另请求下表适用观测，不保证请求所有种类。多个输出可有不同的位置、时间轴和数组 key。无需输出未请求的物理量；不可压缩题的密度为常数，可压缩题的密度为所求状态。非牛顿黏度、剪切率均从当地流动计算，不是另一个独立材料参数。

| quantity | kind | unit | 位置／含义 |
|---|---|---|---|
| velocity | vector | m/s | 流体内速度 |
| pressure | scalar | Pa | 声明表示及基准下的静压 |
| density | scalar | kg/m3 | 流体密度 |
| dynamic_viscosity | scalar | Pa.s | 有效动力黏度 |
| shear_rate | scalar | 1/s | 材料响应中定义的 g |
| traction | vector | Pa | 外边界单元上外界对流体的总牵引 σn |
| force | vector | 2D N/m；3D N | 边界整体积分 −∫σn，流体对边界的力 |
| volume_flow | scalar | 2D m2/s；3D m3/s | 边界整体积分 ∫u·n，向外为正 |
| mass_flow | scalar | 2D kg/(m.s)；3D kg/s | 边界整体积分 ∫ρu·n，向外为正 |

前五类可在流体节点／点取 point、流体或边界单元取 average，或在单元区域取加权整体平均。traction 仅取边界单元 average。用于导数量的采样位置保证相应量有定义；不要求在角点、多值迹或采样不连续处输出点导数。

整体位置形如 `{"kind":"aggregate","source":"outlet_faces","ids":"total_ids","operation":"sum"}`：source 引用网格单元位置，ids 对应一个 int64 观测 ID。不得把它当作带坐标的探针或输入条件区域。sum 对应 value_kind integral；mean 对应 average，即按长度／面积／体积加权平均，不是样本算术平均。整体输出仍为 `[T,1,C]`。force、volume_flow、mass_flow 仅用边界 sum；前五类强度量仅用 mean。不能递归聚合。

应力、牵引及载荷均使用声明的压力表示；表压载荷相对于 reference_pressure，不能混入绝对压力载荷。方向使用全局坐标，不用局部切向／法向分量。瞬态输出时刻位于 time_interval 内；若请求起点，输出给定物理初态及其相容状态，不是预处理前的另一套初值。稳态输出仅一帧，时间轴 `[0.0]` 是存储标记。

结果 HDF5 只写 outputs 声明的 array，以及它们引用的 IDs 和时间数组；共享轴只写一次，按输入原样复制。不写坐标、网格、输入场、JSON 元数据或额外属性。输出 float64 的完整 shape、分量顺序、位置、单位和 value_kind 由各输出声明固定，不得自行重排。

可选 SDK 的读写及校验命令见通用协议；它不替代流动求解，使用与否不影响判分。
