# 2.1.11 3D 常黏度牛顿流体等温可压缩流动稳态分析：数据说明

本文件完整定义本题物理输入与输出；仅依赖[通用存储协议 CONTRACT.md](../../../../docs/CONTRACT.md)，任务、资源和评分见[题面](instruction.md)。

## 清单与数组

`problem.json` 必须声明 `task: "newtonian-isothermal-compressible-steady-3d"`、`spatial_dimension: 3`、`contract_version: 2`、`profile: "cfd-2.1"`，同时提供 `analysis`、`materials`，禁止 `physics`。`data_file` 引用一个 HDF5，`meshes` 恰有一个固定 Gmsh MSH 4.1 ASCII 网格，`geometries` 可为空；不要求执行几何文件或重划网格。

对象名、数组 key、location 名与时间轴名不固定。条件的 `{"field":"u_in"}` 引用 `fields.u_in`，再通过其 `array` 读取 HDF5；`location` 引用位置记录，`ids` 引用 int64 编号数组，`time_axis` 通过 `time_axes` 找到秒数数组。标量 `[T,N,1]`，矢量 `[T,N,3]`，分量为 x、y、z；数值场均为 float64。T、N 由引用的轴确定，IDs 与行一一对应，tag 不是行号。

位置可为网格节点、网格单元、独立点或下述 aggregate。材料 region 引用完整流体域的全维单元。边界位置引用真实外边界单元（包括孔洞和障碍物表面），不是边界节点。点／节点为 point，实体为 average；内域单元平均按体积加权，边界单元平均按面积加权。点观测保证在流体内且所求量有唯一有限迹，不请求交角处多值导数。

## 分析声明

| analysis 路径 | 本题要求 |
|---|---|
| type | `steady` |
| compressibility | `isothermal_compressible` |
| flow_regime | `laminar` |
| temperature | 正的带单位标量，例如 `{"value":300,"unit":"K"}`，空间及时间均恒定，不求温度 |
| pressure.representation | `absolute` 或 `gauge`；均为静压 Pa，不是运动学压力或去静水压 |
| pressure.reference_pressure | gauge 时必有正的绝对参考压力常量 Pa；absolute 时禁止 |
| time_interval | 禁止；稳态仅使用时间标记 `[0.0]` |

所有输入压力、输出压力、牵引与载荷使用同一 pressure 表示；表压满足 `p_absolute = p + reference_pressure`。
密度响应始终使用绝对压力，不能将可压缩压力去均值。禁止 pressure_gauge。
有 pressure_outlet 或 velocity／flow_rate 的密度边界时禁止 mean_density。否则必须给 `analysis.mean_density={"value":1.2,"unit":"kg/m3"}` 这样的严格正常量，表示完整域总质量除以体积，不是逐点密度。库存与状态响应确定压力水平；线性密度响应下库存必须对应正的平均绝对压力。

## 材料参数与响应

`materials` 恰有一个具名对象，含 `region`、`density` 和 `viscosity`。后两者各含 kind 和 parameters；parameters 使用下表全部且仅有的参数，每项为 `{"value":数值,"unit":"单位"}`。参数空间均匀且时间恒定；除体黏度可为零外，全部严格为正，无隐含缺省值。

| density.kind | parameters 及单位 | 密度响应 |
|---|---|---|
| isothermal_ideal_gas | specific_gas_constant：J/(kg.K) | ρ=p_absolute/(R T) |
| linear_barotropic | reference_density：kg/m3；reference_pressure：Pa；sound_speed：m/s | ρ=ρ_ref+(p_absolute−p_ref)/c² |

两种响应均须支持，输入及所求状态的绝对压力、密度均正。

令剪切率 `g=sqrt(2 D:D)`，D 是对称速度梯度，g 单位 1/s。动力黏度单位 Pa.s，不是运动黏度。

| viscosity.kind | parameters 及单位 | 动力黏度 μ |
|---|---|---|
| newtonian | dynamic_viscosity：Pa.s；bulk_viscosity：Pa.s，非负 | μ 为常数 |

总应力 `σ=−pI+2μ(D−tr(D)I/3)+ζ tr(D)I`，ζ 为 bulk_viscosity（纯体积应变黏度，不是第二黏度）。二维仍用三维材料的平面运动响应，去迹系数为 1/3。

输入 fields.quantity 必须为非空字符串；本题不对输入标签追加枚举约束。输入用途由引用它的条件 role／variable／operator 及 data 键决定，不能仅凭标签猜测用途。例如源加速度可标为 acceleration、流率形状可标为 shape，仍以条件声明和单位为准。未被条件引用的已声明输入场亦须满足本题采样规则，不承担隐含物理作用。输出 quantity 则严格使用下文表列集合。

## 条件

每条 conditions 记录包含 role、variable、operator、location、data。标量数值可用带单位常量或 `{"field":"场对象名"}`；矢量必须引用 HDF5 场，不内联数组。类别用 `{"option":"forbid"}`，位置引用用 `{"location":"partner"}`。以下 JSON 只是格式片段。

### 边界

全部边界 role=boundary、variable=flow，location 为域外边界单元集合。每个边／面恰被一条完整条件覆盖，不重不漏；共享角点允许，列表顺序不表示优先级。外法向 n 从流体指向域外，由流体连接关系决定，不依赖边界节点顺序。

| operator | data 的完整键集合 | 定义 |
|---|---|---|
| no_slip | `{}` | 静止、无穿透、无滑移 |
| moving_wall | velocity：m/s 矢量场 | 给定切向速度、无滑移且不移动几何 |
| slip | `{}` | 无穿透、零切向牵引 |
| symmetry | `{}` | 平面镜像对称，无穿透、零切向牵引；算例保证对称相容 |
| velocity | velocity：m/s 矢量场；density：kg/m3 标量 | 给定流入速度与入口密度 |
| pressure_outlet | pressure：Pa 标量；backflow 固定 `{"option":"forbid"}` | 外部储槽压力 p_ext 产生总牵引 `σn=−p_ext n`，切向总牵引零 |
| flow_rate | rate：正标量；shape：正无量纲标量；density：kg/m3 标量 | 正的总流入体积率，切向速度零 |
| periodic | partner：位置引用；translation_x、translation_y、translation_z：m 标量常量 | 双侧互引、反向平移相反；速度、压力和密度周期，压力无跳跃 |

pressure_outlet 的 pressure 是储槽压力，使用声明的压力表示，不另外强制域内静压恰等于 p_ext、速度零法向梯度或人为出口密度。正式算例保证无回流，不能忽略实际回流。pressure、density 可用常量或标量场。

flow_rate 的 rate 单位 m3/s，为常量或空间 uniform 标量场，本题保持恒定。shape 为常量或边界标量场；节点分片线性数据先重建并取边界实体平均。第 i 个边界实体速度定义为 `u_i=−Q shape_i n_i/Σ_j(shape_j measure_j)`；measure 是面积，Q 是整个 location 的流入率，不是逐实体流率。

periodic 通过平移把本侧映射到对侧，按几何双射配对，不按数组行号。周期无隐含压差驱动。

```json
{"role":"boundary","variable":"flow","operator":"no_slip","location":"wall","data":{}}
```

### 初态及体加速度

禁止 initial 记录；迭代初始化由程序选择，不是物理输入。

可选 source／velocity／acceleration 作用于完整材料域，data 恰含 value，引用 m/s2 矢量场。多个源相加，省略表示零；它是加速度，不是单位体积力。禁止用 role=material 再声明材料。

## 输入场采样

每个 fields 场必须有 sampling，包含 space、time、extrapolation：

| 项 | 支持值与定义 |
|---|---|
| space | uniform：空间行完全相同；piecewise_constant：实体平均且实体内常值；piecewise_linear：一阶单纯形网格节点分片线性 |
| time | 只能 constant，时间轴恰为 `[0.0]` |
| extrapolation | forbid：禁止区间外取值；hold 亦可用于恒定场；constant 单帧按定义有效 |

条件场可直接使用条件单元 location，也可使用恰好覆盖该区域全部节点的同网格 node location，按实际 tag 集合匹配。节点取 point、条件实体取 average，不接受 integral。uniform 与实体常值适用全部支持单元，piecewise_linear 只适用单纯形网格。禁止未声明的散点插值或任意函数求值。

## 输出与整体观测

每例至少请求 velocity、pressure，可另请求下表观测；仅输出实际请求字段。各字段的 location、time_axis、array、value_kind 从 outputs 读取，不保证名称或位置相同。

| quantity | kind | unit | 含义 |
|---|---|---|---|
| velocity | vector | m/s | 流体速度 |
| pressure | scalar | Pa | 声明表示及基准下的流体静压 |
| density | scalar | kg/m3 | 所求状态密度 |
| dynamic_viscosity | scalar | Pa.s | 给定常动力黏度 |
| shear_rate | scalar | 1/s | 上述 g |
| traction | vector | Pa | 外界对流体总牵引 σn，边界单元 average |
| force | vector | N | 流体对所选边界力 −∫σn |
| volume_flow | scalar | m3/s | ∫u·n，向域外正 |
| mass_flow | scalar | kg/s | ∫ρu·n，向域外正 |

前五类可在点／节点取 point、单元取 average，或在单元区域取 mean aggregate。导数观测位置保证有限唯一；不要求在不连续采样或交角处输出多值导数。

整体位置完整示例 `{"kind":"aggregate","source":"outlet_faces","ids":"total_ids","operation":"sum"}`：source 引用网格单元位置，ids 指向恰一项 int64 观测 ID。它不是探针，不带坐标，不用于条件，不可递归。sum 使用 value_kind=integral；mean 使用 average，按实体长度／面积／体积加权，不是样本算术平均。整体 shape 为 `[T,1,C]`。force、volume_flow、mass_flow 仅用外边界 sum；前五类强度量仅用 mean。

表压应力与载荷相对于 reference_pressure，不与绝对载荷混用；所有分量用全局坐标。稳态输出只有 `[0.0]` 一帧，它是存储标记。

输出 HDF5 恰含 outputs 指定的 array 及对应 IDs、时间数组；共享轴只写一份并原样复制，不重排，不附坐标、网格、输入场、额外 dataset 或属性。标量始终 `[T,N,1]`，矢量为上述 D 分量。
