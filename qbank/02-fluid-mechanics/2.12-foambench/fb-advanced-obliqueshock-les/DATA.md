# 2.12.117 斜激波二维滤波流动：数据说明

## 文件、引用与采样

通用规则见 [CONTRACT.md](../../../../docs/CONTRACT.md)，任务与评价见 [instruction.md](instruction.md)。本节定义本题全部物理语义；无需原始软件配置。

`problem.json` 使用 `task: "fb-advanced-obliqueshock-les"`、`spatial_dimension: 2`、`physics: {"model":"fb-advanced-obliqueshock-les","parameters":{...}}`。不使用 `profile`、`contract_version`、`analysis`、`materials`。这里是基于通用 physics 声明的题内模型契约，不将新字段冒充 cfd-2.1 已支持的配置；本次只交付文档，模型尚未绑定领域校验器或 judge。

`data_file` 为单个输入 HDF5；`meshes` 恰有一个 Gmsh MSH 4.1 ASCII 一阶三角形／四边形二维网格，`geometries` 可为空。几何物理边界以输入分片直线网格为准，曲线可细化近似。`locations` 中完整流体域与边界均为 mesh element，dimension 分别为 2、1，IDs 为按 tag 递增的 int64；边界按条件位置精确分区。不得以文件行号代替 tag。不存在未声明的壁、重力或旋转参考系。

所有输入场均 float64；标量 `[T,N,1]`，矢量 `[T,N,2]`，分量 x、y（轴对称时见下文）。场通过 `fields` 对象名、`array` 数据集名引用，二者不必相同。全域初态及边界采用单元平均，`value_kind: "average"`；只允许显式 `sampling={"space":"piecewise_constant","time":"constant","extrapolation":"hold"}`：每个实体内、整个计算区间均保持给定值。T=1 的输入场时间为 0 s，无额外空间平滑。条件中的带单位标量常量表示整个作用位置恒定；矢量即便均匀也必须经 field 引用。初态需覆盖全部流体单元；边界需覆盖全部外边界边。

输出只允许二维流体单元的面积平均；每个量可在非空单元子集上请求。输出元数据逐项给 `array,quantity,location,time_axis,dtype,kind,component_shape,components,unit,value_kind`；value_kind 为 average，标量 kind=scalar、components=["value"]、component_shape=[1]；速度 kind=vector、components=["x","y"]、component_shape=[2]。不输出模型专有湍流变量。每个输出时间轴为下面规定物理时刻的非空子集，float64 严格递增；求解器内部步长自选，必须在给定时刻求值。

## 模型参数

`physics.parameters` 恰包含下表参数，每项为 `{"value":有限数值,"unit":"单位"}`；这些是本题固定工况值，数值必须与表一致。表外数值在下面文字给定，不从名称推断。无隐含缺省。

| 参数 | 固定值 | 单位 | 含义 |
|---|---:|---|---|
| gas_constant | 0.7143 | J/(kg.K) | 明确采用prompt给定R，消除分子量四舍五入歧义 |
| specific_heat_cp | 2.5 | J/(kg.K) | 常比热 |
| dynamic_viscosity | 0.00016646 | Pa.s | 常动力黏度 |
| prandtl_number | 1 | 1 | 分子Pr |
| turbulent_prandtl_number | 0.85 | 1 | 移植补足湍流Pr |
| filter_width | 0.05 | m | 明确固定的滤波长度 |

## 几何、条件与初态

二维矩形 [0,4.1]×[0,1] m²，入口x=0给u=(2.9,0) m/s、p=1 Pa、T=1 K；顶边给u=(2.61933,−0.50632)、T=1.25853 K且p零外法向导数；底边对称，无穿透，p,T零法向导数；右边为超声速流出，u,p,T零法向导数。初态u=(2.9,0)、p=1、T=1，密度由状态方程得。计算区间[0,10] s，输出0,1,…,10 s。理想气体 p=ρRT，cv=cp−R，e=cvT，γ=cp/cv；数值上γ略异于1.4，以该闭合为准。求质量、动量、总能量守恒，Stokes体黏度约定；热导率λ=μcp/Pr，加湍流热扩散ρνt cp/Prt；绝对静压，无重力。

采用二维可压缩 Favre 滤波的代数 Smagorinsky 闭合，Cs=0.17，Δ=parameters.filter_width，二者不随内部网格改变。三维嵌入的无迹应变 S=dev((∇u+∇uᵀ)/2)，νt=(CsΔ)²sqrt(2S:S)，模型黏性应力为2ρνt S。忽略亚格子各向同性应力与独立亚格子能量，压力直接为状态方程的热力学静压；不把已有k文件当成必须输运的未知量。velocity 为该模型的Favre速度，输出是其单元平均，不另施可选空间或时间滤波。热扩散含ρνt cp/Prt；采用气体总能量 E=cvT+|u|²/2，不附加独立k能量。守恒通量及模型耗散保持总能量一致；不使用额外压缩修正。

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

本题无独立亚格子能量初态或边界，Smagorinsky涡黏度由当前解析应变代数计算。

气体题中pressure与temperature的初态、边界必须成对提供以确定密度；density不作为独立初始约束。不可压题不提供initial/pressure，其压力由动量约束、指定开口或均值规范确定。初始速度为上文投影定义的题，initial/assign的value存原始v，不把其当未经投影的物理初态；除该特殊规则外assign直接给物理初态。初态额外变量均取非负值；输入与表列固定值不符即非法。

## 允许输出

| quantity | 分量 | 单位 |
|---|---|---|
| velocity | x,y | m/s |
| pressure | value | Pa |
| temperature | value | K |
| density | value | kg/m3 |

输出为求得连续场在给定单元上的物理平均，不是单元中心点值；二维按单位出平面厚度，轴对称例外见本题定义。只写 `outputs` 请求的数组及其 IDs、时间轴，key、dtype、shape、值与顺序按 CONTRACT；不写额外网格、坐标、输入状态或日志到结果文件。所有量使用同一声明的压力基准，判分不做平移、缩放、网格包围盒对齐或重排。
