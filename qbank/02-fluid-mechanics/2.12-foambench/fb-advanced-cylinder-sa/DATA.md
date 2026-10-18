# 2.12.126 偏置圆柱 SA 非定常绕流：数据说明

## 文件、引用与采样

通用规则见 [CONTRACT.md](../../../../docs/CONTRACT.md)，任务与评价见 [instruction.md](instruction.md)。本节定义本题全部物理语义；无需原始软件配置。

`problem.json` 使用 `task: "fb-advanced-cylinder-sa"`、`spatial_dimension: 2`、`physics: {"model":"fb-advanced-cylinder-sa","parameters":{...}}`。不使用 `profile`、`contract_version`、`analysis`、`materials`。这里是基于通用 physics 声明的题内模型契约，不将新字段冒充 cfd-2.1 已支持的配置；本次只交付文档，模型尚未绑定领域校验器或 judge。

`data_file` 为单个输入 HDF5；`meshes` 恰有一个 Gmsh MSH 4.1 ASCII 一阶三角形／四边形二维网格，`geometries` 可为空。几何物理边界以输入分片直线网格为准，曲线可细化近似。`locations` 中完整流体域与边界均为 mesh element，dimension 分别为 2、1，IDs 为按 tag 递增的 int64；边界按条件位置精确分区。不得以文件行号代替 tag。不存在未声明的壁、重力或旋转参考系。

所有输入场均 float64；标量 `[T,N,1]`，矢量 `[T,N,2]`，分量 x、y（轴对称时见下文）。场通过 `fields` 对象名、`array` 数据集名引用，二者不必相同。全域初态及边界采用单元平均，`value_kind: "average"`；只允许显式 `sampling={"space":"piecewise_constant","time":"constant","extrapolation":"hold"}`：每个实体内、整个计算区间均保持给定值。T=1 的输入场时间为 0 s，无额外空间平滑。条件中的带单位标量常量表示整个作用位置恒定；矢量即便均匀也必须经 field 引用。初态需覆盖全部流体单元；边界需覆盖全部外边界边。

输出只允许二维流体单元的面积平均；每个量可在非空单元子集上请求。输出元数据逐项给 `array,quantity,location,time_axis,dtype,kind,component_shape,components,unit,value_kind`；value_kind 为 average，标量 kind=scalar、components=["value"]、component_shape=[1]；速度 kind=vector、components=["x","y"]、component_shape=[2]。不输出模型专有湍流变量。每个输出时间轴为下面规定物理时刻的非空子集，float64 严格递增；求解器内部步长自选，必须在给定时刻求值。

## 模型参数

`physics.parameters` 恰包含下表参数，每项为 `{"value":有限数值,"unit":"单位"}`；这些是本题固定工况值，数值必须与表一致。表外数值在下面文字给定，不从名称推断。无隐含缺省。

| 参数 | 固定值 | 单位 | 含义 |
|---|---:|---|---|
| density | 1 | kg/m3 | 恒密度 |
| kinematic_viscosity | 0.01 | m2/s | 常运动黏度 |

## 几何、条件与初态

二维域为 [-5,5]×[-1.5,2.5] m² 去掉中心(0,0)、半径1 m的圆柱截面。曲线以输入网格近似；不是直径0.1 m的其他同名基准。入口 x=−5，u=(1,0)；出口 x=5，p_gauge=0 Pa、∂n u=0；上下墙及圆柱为无滑移静止壁。出口不允许回流，本题模型仅覆盖该阶段。初态 u=(0,0)，压力由动量约束及出口基准确定；入口瞬时启动不相容按非定常启动解释。不可压缩、不求温度、无体力。t∈[0,2] s，输出0,0.05,…,2 s。

采用非定常 Reynolds 平均和 Spalart–Allmaras 一方程涡黏性闭合，使用无转捩、无 trip、无 ft2 的 SA-noft2 版本，不添加旋转／曲率修正。输运量为非负修正运动涡黏度 q，νt=q fv1，χ=q/ν，fv1=χ³/(χ³+7.1³)。

其运动形式为 Dq/Dt=cb1 S̃q + [∇·((ν+q)∇q)+cb2|∇q|²]/σ − cw1 fw(q/d)²。cb1=0.1355、cb2=0.622、σ=2/3、κ=0.41、cw1=cb1/κ²+(1+cb2)/σ、cw2=0.3、cw3=2；d 为到最近固体壁的距离，若本题有明示的滑移固体壁也包括之，不包括入口、出口或对称边。Ω=sqrt(2W:W)，W=(∇u−∇uᵀ)/2，fv2=1−χ/(1+χ fv1)，S̃=max(Ω+q fv2/(κ²d²),0.3Ω)。r=min(q/(max(S̃,10⁻³⁰ s⁻¹)κ²d²),10)，g=r+cw2(r⁶−r)，fw=g[(1+cw3⁶)/(g⁶+cw3⁶)]^(1/6)。壁面 q=0，S̃=0 时按连续极限处理。密度变化时本题仍采用上述物质导数形式，作为明确的移植闭合定义。

黏性应力使用 μeff=ρ(ν+νt)，可压缩时使用去迹应变；本版本不另加模型湍动能对应的各向同性应力。

## 条件编码

每条记录恰含 `role,variable,operator,location,data`。位置名称任意，以实际引用的实体集合识别，不能根据 inlet 等字符串猜条件。

| role / operator | variable | data 完整键 | 含义 |
|---|---|---|---|
| initial / assign | velocity、pressure、气体题temperature 或下列额外状态 | value | 全域物理初态；标量常量或同位置场，矢量只用场 |
| boundary / dirichlet | 同上 | value | 该变量边界迹等于 value |
| boundary / normal_derivative | 同上 | value | 外法向导数等于 value；只允许本题指定的零值，单位为原量单位除以 m |
| boundary / slip | velocity | normal_velocity | 法向速度为给定 0 m/s，切向速度外法向导数为零 |
| boundary / pressure_open | flow | pressure, backflow_velocity | 边界静压为给定 Pa；流出速度外法向导数零；流入只取给定场的切向分量，法向由压力与连续性求解；压力不是总压，也不是总牵引 |
| boundary / advective_open | 下列额外标量状态 | backflow_value | 流出为零外法向导数，流入取给定同位置标量场或带单位常量 |
| source / pressure_mean | pressure | value | 全域平均静压 gauge 固定于 value；仅无压力开口的封闭腔体允许 |

`value`、`pressure` 使用带单位标量或同位置 field，`backflow_velocity` 必须是同位置矢量 field；slip 的 normal_velocity 使用带单位零标量。flow 仅为联合边界变量名，不是输出。其他源项禁止。不同变量的边界可共址，同一变量不得重叠约束；角点不另赋覆盖优先级。下文指定的固定墙 velocity 使用 dirichlet 零矢量场。压力在速度入口／无滑移壁由法向动量约束确定，不额外强制零梯度；仅明确写出的零法向导数出口按该条件处理。所有压力为静压 Pa；gauge 以环境绝对压力 101325 Pa 为参考，且未另外说明时无压力重对齐。

额外状态 `modified_eddy_viscosity` q（m2/s）初态和入口均0.03，墙0，出口零外法向导数。

气体题中pressure与temperature的初态、边界必须成对提供以确定密度；density不作为独立初始约束。不可压题不提供initial/pressure，其压力由动量约束、指定开口或均值规范确定。初始速度为上文投影定义的题，initial/assign的value存原始v，不把其当未经投影的物理初态；除该特殊规则外assign直接给物理初态。初态额外变量均取非负值；输入与表列固定值不符即非法。

## 允许输出

| quantity | 分量 | 单位 |
|---|---|---|
| velocity | x,y | m/s |
| pressure | value | Pa |

输出为求得连续场在给定单元上的物理平均，不是单元中心点值；二维按单位出平面厚度，轴对称例外见本题定义。只写 `outputs` 请求的数组及其 IDs、时间轴，key、dtype、shape、值与顺序按 CONTRACT；不写额外网格、坐标、输入状态或日志到结果文件。所有量使用同一声明的压力基准，判分不做平移、缩放、网格包围盒对齐或重排。
