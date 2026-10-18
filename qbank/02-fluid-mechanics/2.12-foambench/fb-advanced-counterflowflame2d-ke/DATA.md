# 数据定义：甲烷与空气对向扩散火焰：k–ε平均流

## 范围与状态

本题是2.12.120的自包含接口定义。`task` 必须精确为 `fb-advanced-counterflowflame2d-ke`。采用 [CONTRACT](../../../../docs/CONTRACT.md) 的 `physics` 路径，不使用CFD profile。`physics.model` 必须精确为 `foambench-counterflowflame2d-ke`，`spatial_dimension=2`。此模型是文档契约草案，尚未装配领域声明检查、网格、HDF5或数值参考；以下文件与数组均为未来数据包要求，不表示当前目录已有可运行输入。

## 几何、方程与材料

域为 0<x<0.02m、−0.01<y<0.01m。fuel 是 x=0，air 是 x=0.02，outlet 是 y=±0.01 的两段开口；四角按入口边界取值。二维场在z不变，无前后表面条件。

求二维瞬态可压缩反应混合物的质量、动量、五组分质量和总能量守恒方程。组分顺序固定为 CH4、O2、N2、CO2、H2O，Y 是质量分数，ΣY=1，ρ=p/(Rmix T)，Rmix=ΣYs Rs，Rs=Ru/Ms，Ru=8314.462618 J/(kmol.K)。无重力、无辐射、无额外外部热源。层流黏应力 τ=μ[∇u+(∇u)ᵀ−(2/3)(∇·u)I]，无附加体黏度。

唯一反应 CH4+2O2→CO2+2H2O；反应进度率 q=5.2×10¹⁶ exp(−14906/T)cCH4 cO2²，cs=ρYs/Ms（kmol/m3），q 单位 kmol/(m3.s)，前因子单位 m6/(kmol2.s)，温度指数0。ωs=Ms νs q，其中 ν=(-1,-2,0,1,2)，单位 kg/(m3.s)；N2源严格为0。为保证元素和总质量守恒，统一原子量C=12.0107、H=1.00794、O=15.9994、N=14.0067 kg/kmol，各分子量按化学式求和，详见下表；不使用各物种独立舍入而不一致的分子量。反应是单步全局机理，不能解释为详细机理。

每组分采用 NASA 七系数多项式：cp,s/Rs=a1+a2T+a3T²+a4T³+a5T⁴；hs/(Rs T)=a1+a2T/2+a3T²/3+a4T³/4+a5T⁴/5+a6/T；ss/Rs=a1 lnT+a2T+a3T²/2+a4T³/3+a5T⁴/4+a7。T≤1000K用低温系数，T>1000K用高温系数；在标注温度区间外仍按同一端侧多项式外推，此为确定的数学延拓，不承诺真实物性有效。es=hs−RsT，混合物e=ΣYs es；总能量 E=e+|u|²/2 包含生成焓，故保守总能量方程不再添加化学热源，反应热由组分改变自然体现。导热与组分焓通量为 −κ∇T+Σhs Js。

组分 μs=As T^(3/2)/(T+Ts)；Cv,s=cp,s−Rs，κs=μs Cv,s[1.32+1.77Rs/Cv,s]。以摩尔分数 Xs=(Ys/Ms)/Σ(Yj/Mj) 混合：Φij=[1+sqrt(μi/μj)(Mj/Mi)^(1/4)]²/sqrt[8(1+Mi/Mj)]，μ=Σ Xi μi/(Σj Xj Φij)，κ=Σ Xi κi/(Σj Xj Φij)。cp=ΣYs cp,s。统一单位Lewis数扩散 D=κ/(ρcp)，先取 Js*=−ρD∇Ys，再取 Js=Js*−YsΣJj*，从而ΣJs=0；不加Soret、Dufour、压力扩散。能量方程含黏应力功；无独立燃烧效率因子、湍流火焰速度或点火模型。

| 组分 | M (kg/kmol) | As (Pa.s/K^(1/2)) | Ts (K) | 多项式温度范围(K) |
| --- | --- | --- | --- | --- |
| O2 | 31.9988 | 1.753e-6 | 139 | 200–5000 |
| H2O | 18.01528 | 2.978e-7 | 1064 | 200–5000 |
| CH4 | 16.04246 | 1.0194e-6 | 171.06 | 200–6000 |
| CO2 | 44.0095 | 1.503e-6 | 222 | 200–5000 |
| N2 | 28.0134 | 1.401e-6 | 107 | 200–5000 |

| 组分 | 温段 | (a1,a2,a3,a4,a5,a6,a7)，T以K代入 |
| --- | --- | --- |
| O2 | 低 | (3.21294,0.00112749,-5.75615e-7,1.31388e-9,-8.76855e-13,-1005.25,6.03474) |
| O2 | 高 | (3.69758,0.00061352,-1.25884e-7,1.77528e-11,-1.13644e-15,-1233.93,3.18917) |
| H2O | 低 | (3.38684,0.00347498,-6.3547e-6,6.96858e-9,-2.50659e-12,-30208.1,2.59023) |
| H2O | 高 | (2.67215,0.00305629,-8.73026e-7,1.201e-10,-6.39162e-15,-29899.2,6.86282) |
| CH4 | 低 | (5.14988,-0.013671,4.91801e-5,-4.84744e-8,1.66694e-11,-10246.6,-4.64132) |
| CH4 | 高 | (1.63543,0.0100844,-3.36924e-6,5.34973e-10,-3.15528e-14,-10005.6,9.9937) |
| CO2 | 低 | (2.27572,0.00992207,-1.04091e-5,6.86669e-9,-2.11728e-12,-48373.1,10.1885) |
| CO2 | 高 | (4.45362,0.00314017,-1.27841e-6,2.394e-10,-1.66903e-14,-48967,-0.955396) |
| N2 | 低 | (3.29868,0.00140824,-3.96322e-6,5.64152e-9,-2.44486e-12,-1020.9,3.95037) |
| N2 | 高 | (2.92664,0.00148798,-5.68476e-7,1.0097e-10,-6.75335e-15,-922.798,5.98053) |

采用标准可压缩平均流 k–ε 闭合，不加浮力生产、膨胀耗散、低雷诺数或燃烧专用修正。μt=0.09ρk²/ε，τt=2μt dev(S)−(2/3)ρkI，S=(∇u+∇uᵀ)/2，P=max(τt:∇u,0)。守恒输运为 ∂t(ρk)+∇·(ρuk)=∇·[(μ+μt)∇k]+P−ρε；∂t(ρε)+∇·(ρuε)=∇·[(μ+μt/1.3)∇ε]+1.44(ε/k)P−1.92ρε²/k。k=0时取μt=P=0，ε/k相关源项按k→0且ε→0的静止无湍流极限取0；其他时刻要求k≥0、ε>0。

初始k=30 m2/s2、ε=30000 m2/s3。燃料入口强度 I=0.0458、混合长度 L=0.000504m，空气入口 I=0.0471、L=0.019677m，入口 k=1.5(I|u|)²、ε=0.09^(3/4)k^(3/2)/L。出口k、ε法向导数均为0，包括倒流；不把源文件占位value=1当作入口物理值。

平均流动量和能量方程采用τ+τt，其中SA为τt=2μt dev(S)，KE采用上述τt。总能量定义仍不含k；不另加k扩散能量通量。有效导热κeff=κ+μt cp/0.85；扩散Js*=[−ρD−μt/0.7]∇Ys，再按同一修正保证ΣJs=0。化学源直接用平均T、Y计算，不加湍流化学相互作用。


`physics.parameters` 只允许下面列出的带单位有限标量；值固定为本移植变体，隐藏数据不得无声明更换物理参数。公式中的固定热化学/闭合系数按本页定义，不在JSON中存放多项式字符串、列表或可执行表达式。边界值在条件中明确存储，重复标量必须与表中一致。

| 参数 | 值 | 单位 |
| --- | --- | --- |
| end_time | 0.5 | s |
| output_interval | 0.05 | s |
| fuel_velocity_x | 0.1 | m/s |
| air_velocity_x | -0.1 | m/s |
| inlet_temperature | 293 | K |
| reservoir_total_pressure | 100000.0 | Pa |

## 初始、边界及源项

法向n始终指向域外，所有速度与向量按全局(x,y)顺序。边界在0至0.5s保持不变。除本页模型已定义的反应/浮力/闭合源外无其他源项。初始状态是瞬态起始条件，不是可任意改变的数值初猜。

fuel：u=(0.1,0)m/s，T=293K，Y=(1,0,0,0,0)，∂np=0。air：u=(-0.1,0)m/s，T=293K，Y=(0,0.23,0.77,0,0)，∂np=0。

outlet：总压储槽 p0=100000Pa。令un=u·n；外流(un≥0)取p=p0、∂nu=0、∂nT=0、∂nY=0；倒流(un<0)取切向速度为0、∂nun=0，p=p0−ρ|u|²/2，T=293K，Y=(0,0,1,0,0)。这是本题明确采用的动压总压定义，不使用等熵总压关系；密度由边界p/T/Y联立状态方程得到。边界切换在un=0按外流处理，扩散通量由指定值或零梯度决定。

初始内部u=(0,0)m/s、p=100000Pa、T=2000K、Y=(0,0,1,0,0)，密度按状态方程；t=0边界优先于内部初值。高温氮气是明确的初态，不能替换为预混火焰或冷态。

## 文件、位置与采样

未来输入包包含 `problem.json`、Gmsh MSH 4.1 ASCII `mesh.msh`、`input.h5`，可选 `domain.geo`。路径相对problem.json，清单 `meshes.main.file=mesh.msh`；坐标为m，Gmsh第三坐标为0，网格拓扑二维。几何可由 `geometries.domain` 引用并由网格记录链接；实际离散以msh为准。`locations.domain` 是全部二维域单元，`kind=mesh, mesh=main, entity=element, dimension=2, ids=domain_ids`。每个条件边界名称在locations中定义为相应一维边单元集合，记录 `kind=mesh, mesh=main, entity=element, dimension=1, ids=<名称>_ids`，并以 `physical_group={dimension:1,tag:整数}` 显式绑定；domain绑定维度2组。组号在实际清单给出，不能靠组名称推断条件；并集wall或outlet可用单独Physical Group表示，同一边可属于多个组但不得产生矛盾条件。

输出 `locations.samples={"kind":"points","ids":"sample_ids","coordinates":"sample_coordinates"}`；sample_ids为非负严格递增int64[N]，sample_coordinates为float64[N,2]，全为流体内部固定点，不含边界、角点和固体。输出为点值，不是单元平均；激波恰过采样点时取该时刻求解场的熵解外侧极限，若两侧极限不同则取两侧算术平均。没有自动生成中心点或隐含网格顺序。所有mesh位置的ID为正严格递增int64；边界单元ID不是domain单元ID。

`time_axes.initial=initial_times`，initial_times为float64[1]=[0]；`time_axes.output=output_times`，output_times为float64[11]，第j项为j×0.05s。输出时间与内部积分步长无关。没有统计平均或伪时间。时间轴由输入提供并在结果中逐值复制，不重算或重排。

初始场在domain单元上以 `value_kind=average` 存储，各单元的值严格为上文均匀内部初值；入口/边界数值场在相应边单元上同样为average。其空间采样 `sampling={"space":"uniform","time":"constant","extrapolation":"hold"}`，表示给定位置全部单元上的同一常值并在整个物理区间保持，不从相邻边或域外外推。均匀矢量和组分也必须以完整数组存储，禁止内联JSON数值列表或省略实体轴；均匀标量条件可用带单位常数。每个变量的初始字段命名 `initial_<变量>`，time_axis为initial；边界字段命名 `<边界>_<变量>`，time_axis也为initial，作为全时段常量使用。此命名表的变量由下列条件表逐项枚举；为constant表达的标量无需另造field。所有字段dtype=float64，标量component_shape=[1]/components=["value"]，速度[2]/["x","y"]，质量分数[5]/["CH4","O2","N2","CO2","H2O"]，单位与对应输出一致。

## 条件清单

每个表格中逗号列出的变量或位置均展开为独立条件记录，不在JSON键内塞逗号列表。每条记录恰含 `role,variable,operator,location,data`。数值常数写成 `{"value":数值,"unit":"单位"}`，字段引用 `{"field":"字段对象名"}`；data键列未标为可选的均必需，不接收其他算子或参数。value/backflow_value是数据参数名，不是未声明表达式。条件不依排列先后生效；初态和边界在t=0的相交点遵守前述优先规则。

| role | variable | location | operator | data键与物理含义 |
| --- | --- | --- | --- | --- |
| initial | velocity, temperature, pressure, mass_fractions | domain | assign | 各变量一条，value引用对应initial字段 |
| boundary | velocity, temperature, mass_fractions | fuel, air | dirichlet | 各入口各变量一条，value引用对应均匀入口字段 |
| boundary | pressure | fuel, air | normal_derivative | value=0 Pa/m |
| boundary | velocity | outlet | open_velocity | backflow_tangential_speed=0 m/s；按上文切换定义 |
| boundary | pressure | outlet | reservoir_total_pressure | p0=100000 Pa；按上文联立定义 |
| boundary | temperature | outlet | inlet_outlet | backflow_value=293 K；外流零法向梯度 |
| boundary | mass_fractions | outlet | inlet_outlet | backflow_value引用五分量氮气字段；外流零法向梯度 |
| initial | turbulent_kinetic_energy, dissipation_rate | domain | assign | value引用对应initial字段，数值见闭合定义 |
| boundary | turbulent_kinetic_energy, dissipation_rate | fuel, air | dirichlet | value引用入口字段，由闭合定义给定或计算后存数组 |
| boundary | turbulent_kinetic_energy, dissipation_rate | outlet | normal_derivative | value=0，单位为对应变量单位/m |


域内全部常系数和显式公式源已由physics和本页方程定义，不额外添加material/source记录。mean_gauge（若出现）是以source角色承载的非局部规范约束，不是物理体源。momentum_compatible/open_velocity/slip等含无数据分支的算子仍须带表列的数值参数，避免用未知字段或空data暗示物理。

例如某均匀二维边界速度条件采用 `data={"value":{"field":"fuel_velocity"}}`，该field必须位于同一location；边界温度常数采用 `data={"value":{"value":293,"unit":"K"}}`。示例仅说明类型，实际变量、位置与数值以本题上述定义为准。标量0导数表示相应变量的零法向导数；矢量0导数必须引用显式二维零field，不将一个标量隐式广播为两个分量。

## 输出

`outputs` 必须逐项为下面结构，所有字段共用samples/output，T=11、N=len(sample_ids)，无空间/时间重建或隐式轴。单位和quantity字符串由此固定，压力含义以模型段落为准。

```json
{
  "velocity": {
    "array": "velocity",
    "quantity": "velocity",
    "location": "samples",
    "time_axis": "output",
    "dtype": "float64",
    "kind": "vector",
    "component_shape": [
      2
    ],
    "components": [
      "x",
      "y"
    ],
    "unit": "m/s",
    "value_kind": "point"
  },
  "pressure": {
    "array": "pressure",
    "quantity": "pressure",
    "location": "samples",
    "time_axis": "output",
    "dtype": "float64",
    "kind": "scalar",
    "component_shape": [
      1
    ],
    "components": [
      "value"
    ],
    "unit": "Pa",
    "value_kind": "point"
  },
  "temperature": {
    "array": "temperature",
    "quantity": "temperature",
    "location": "samples",
    "time_axis": "output",
    "dtype": "float64",
    "kind": "scalar",
    "component_shape": [
      1
    ],
    "components": [
      "value"
    ],
    "unit": "K",
    "value_kind": "point"
  },
  "mass_fractions": {
    "array": "mass_fractions",
    "quantity": "mass_fractions",
    "location": "samples",
    "time_axis": "output",
    "dtype": "float64",
    "kind": "components",
    "component_shape": [
      5
    ],
    "components": [
      "CH4",
      "O2",
      "N2",
      "CO2",
      "H2O"
    ],
    "unit": "1",
    "value_kind": "point"
  },
  "turbulent_kinetic_energy": {
    "array": "turbulent_kinetic_energy",
    "quantity": "turbulent_kinetic_energy",
    "location": "samples",
    "time_axis": "output",
    "dtype": "float64",
    "kind": "scalar",
    "component_shape": [
      1
    ],
    "components": [
      "value"
    ],
    "unit": "m2/s2",
    "value_kind": "point"
  },
  "dissipation_rate": {
    "array": "dissipation_rate",
    "quantity": "dissipation_rate",
    "location": "samples",
    "time_axis": "output",
    "dtype": "float64",
    "kind": "scalar",
    "component_shape": [
      1
    ],
    "components": [
      "value"
    ],
    "unit": "m2/s3",
    "value_kind": "point"
  }
}
```

结果 `result.h5` 必须恰包含各输出array、sample_ids与output_times；float64场shape为[T,N,*component_shape]，IDs和时间的dtype/shape/值/顺序与输入完全一致。不写坐标、网格、初态、边界场、额外诊断或元数据。input.h5恰包含locations引用的IDs和坐标、time_axes数组、fields数组，不夹带未引用数据。上述全部条件、字段、ID与几何边界须在数据制作时交叉核验；通用结构检查不验证方程、模型闭合、网格分辨率或数值准确度。
