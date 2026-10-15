# rigid-scattering 数据契约

入口problem.json及其data_file引用的扁平HDF5，路径相对清单。physics恰含model、parameters；model固定`acoustic-rigid-scattering-v1`，task可省略，出现须为`rigid-scattering`。禁止contract_version、profile、analysis、materials混用；不接受本题未列字段、模型或条件组合。

## 物理定义

相量约定为真实扰动Re(A exp(+iωt))，ω=2πf>0。声压是相对背景的扰动，不是总绝对压力；单频输入和输出均为复振幅，不是RMS或仅模长。流体为均匀无穷外域，背景ρ、c给定，k=ω/c。障碍是单个封闭无自交、可定向、连通的多面体；Gmsh三角节点顺序规定固体向外法向ns（朝流体），与流体外域的边界向外法向相反。外域(∆+k²)P=0，出射条件r(∂rP+ikP)→0，基函数exp(−ikr)/(4πr)。不以有限截断或某个PML的结果定义真值；边界积分伪共振是数值方法责任。入射场Pinc=A exp[−ik d·(x−xref)]，A=amplitude_real+i amplitude_imag，单位方向d由参数给出，Uinc=d Pinc/(ρc)。求出射散射场Psc，使总法向速度(Uinc+Usc)·ns=0，等价∂nsPsc=ik(ns·d)Pinc。输出Psc与Pinc+Psc；总场不满足仅出射条件，出射条件只施于散射场。

## 全局参数

parameters恰为下表全部项，各项只有value和unit，有限实数且布尔值不能作数值，整数须JSON整数。

| 参数 | 单位 | 含义及值域 |
|---|---|---|
| `frequency` | `Hz` | 单频f>0，ω=2πf |
| `density` | `kg/m3` | 均匀背景密度ρ>0 |
| `sound_speed` | `m/s` | 均匀声速c>0 |
| `direction_x` | `1` | 入射传播单位方向d的x分量 |
| `reference_x` | `m` | 入射相位参考点x_ref的x分量 |
| `direction_y` | `1` | 入射传播单位方向d的y分量 |
| `reference_y` | `m` | 入射相位参考点x_ref的y分量 |
| `direction_z` | `1` | 入射传播单位方向d的z分量 |
| `reference_z` | `m` | 入射相位参考点x_ref的z分量 |
| `amplitude_real` | `Pa` | 入射压力复振幅A实部 |
| `amplitude_imag` | `Pa` | 入射压力复振幅A虚部 |

## 几何、位置与身份

meshes恰含main，MSH4.1 ASCII；可选geometries只保留来源，求解几何以网格为准。spatial_dimension=3，坐标为m。tag是身份不是行号，Physical Group若声明必须与location的IDs精确相符；组名不定义边界。main仅含非退化一阶三角形type2，不导出边／点／体单元。surface为main全部二维三角单元location；domain为全部所用节点。表面单个连通闭壳、每条边恰有两相邻面且定向相反，按节点顺序的总有向体积为正（ns固体向外）；没有未用节点、自交、开口或多重壳。receivers为独立points，含真实外部接收点坐标与自己的非负IDs，允许位置集合中有多个接收点但不得在内部或表面。每点距表面至少1e−8倍障碍包围盒对角线。只允许domain、surface、receivers三个location；输出引用receivers全部IDs。

## 时间、分量与输入重建

time_axes恰为harmonic单帧[0.0]；全部输入和输出只引用harmonic。0是相量存储标记，不是物理初态、相位未知量或额外频率轴；每例只有parameters.frequency这一物理频率。所有输入sampling.time=constant，不接受物理历史或输出多帧。

本题fields必须为空；入射振幅、方向与相位参考点仅由全局参数给定，rigid只含规定option。输出为float64复标量components，shape=[2]、components=["c1","c2"]，依次为实部和虚部，保留[T,N,2]全部轴；不使用复数dtype或幅相表示。输入HDF5只含位置IDs、receivers坐标与harmonic时间数组。方向范数须满足|norm(d)−1|≤1e−12，不由工具归一化。

## 条件全集

### `rigid`

role=`boundary`，variable=`normal_velocity`，operator=`rigid`；location为surface全部三角面。必须出现。该算子恰一条覆盖表定完整位置。data恰含下列全部键：

| data键 | 类型、单位和含义 |
|---|---|
| `state` | 静止刚性体，总场法向速度为0；精确为`{"option":"stationary"}` |



## 输出

outputs逻辑名与array key自由；每个quantity至少一次，可重复请求。全部float64、不含sampling、时间轴为harmonic，dtype／shape／components与单位按表及前述分量规则。

| quantity | 类型、单位及定义 | 支持位置、value_kind |
|---|---|---|
| `scattered_pressure` | components [2]；`Pa`；散射压力Psc | receivers全部点，point |
| `pressure` | components [2]；`Pa`；总声压Pinc+Psc | receivers全部点，point |

receivers输出是其真实坐标处点值，不是区域积分或任意角度函数；没有隐含远场近似。结果HDF5仅含输出array、所需IDs及时间轴，严格复制输入身份与行序；不导出输入场、坐标或新网格。

## 接收条件与限制

外表面至多800三角面、9000节点，至多128接收点。每轴至多101帧，全部输入／输出场各至多3000000数值分量。正式数据须核验几何无自交／重叠、材料适用、小扰动线性范围、初边值相容、所请求点值／平均存在及物理解可确定，并用独立参考证明预算内精度；校验器不证明这些性质。不得以格式合法、求解器低残差或与同一离散一致替代声学正确性。
