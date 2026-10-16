# surface-radiation 数据契约

入口problem.json及其data_file引用的扁平HDF5，路径相对清单。physics恰含model、parameters；model固定`acoustic-surface-radiation-v1`，task可省略，出现须为`surface-radiation`。禁止contract_version、profile、analysis、materials混用；不接受本题未列字段、模型或条件组合。

## 物理定义

相量约定为真实扰动Re(A exp(+iωt))，ω=2πf>0。声压是相对背景的扰动，不是总绝对压力；单频输入和输出均为复振幅，不是RMS或仅模长。流体为均匀无穷外域，背景ρ、c给定，k=ω/c。障碍是单个封闭无自交、可定向、连通的多面体；Gmsh三角节点顺序规定固体向外法向ns（朝流体），与流体外域的边界向外法向相反。外域(∆+k²)P=0，出射条件r(∂rP+ikP)→0，基函数exp(−ikr)/(4πr)。不以有限截断或某个PML的结果定义真值；边界积分伪共振是数值方法责任。全部固体表面U·ns=W，等价∂nsP=−iωρW；W按实际三角面常值给定。输出真实外部接收点的辐射声压，不含入射场。

## 全局参数

parameters恰为下表全部项，各项只有value和unit，有限实数且布尔值不能作数值，整数须JSON整数。

| 参数 | 单位 | 含义及值域 |
|---|---|---|
| `frequency` | `Hz` | 单频f>0，ω=2πf |
| `density` | `kg/m3` | 均匀背景密度ρ>0 |
| `sound_speed` | `m/s` | 均匀声速c>0 |

## 几何、位置与身份

meshes恰含main，MSH4.1 ASCII；可选geometries只保留来源，求解几何以网格为准。spatial_dimension=3，坐标为m。tag是身份不是行号，Physical Group若声明必须与location的IDs精确相符；组名不定义边界。main仅含非退化一阶三角形type2，不导出边／点／体单元。surface为main全部二维三角单元location；domain为全部所用节点。表面单个连通闭壳、每条边恰有两相邻面且定向相反，按节点顺序的总有向体积为正（ns固体向外）；没有未用节点、自交、开口或多重壳。receivers为独立points，含真实外部接收点坐标与自己的非负IDs，允许位置集合中有多个接收点但不得在内部或表面。每点距表面至少1e−8倍障碍包围盒对角线。只允许domain、surface、receivers三个location；输出引用receivers全部IDs。

## 时间、分量与输入重建

time_axes恰为harmonic单帧[0.0]；全部输入和输出只引用harmonic。0是相量存储标记，不是物理初态、相位未知量或额外频率轴；每例只有parameters.frequency这一物理频率。所有输入sampling.time=constant，不接受物理历史或输出多帧。

fields恰为被条件引用的字段；条件field引用逻辑对象名，该对象的array才是HDF5 key，两者名称自由。输入quantity固定等于data键名；唯一例外是value，其quantity等于该条条件variable（下表明确）。field须与条件同location，不能按相同长度借别处数据。所有field为float64，数组[T,N,*component_shape]，不省略轴。components按表shape行优先展平命名c1..cL（L为shape各维乘积）。复标量[2]依次实、虚，复向量[3,2]为x实虚、y实虚、z实虚；不使用复数dtype或幅相数组。输入field显式sampling，extrapolation=forbid；单元space=piecewise_constant，为每个实体常值。输入value_kind元素为average，不接受输入integral。sampling.time固定constant；只作上述空间重建，不定义额外时间演化。本题复量输入仅允许显式field，不允许内联数组或常量替代。位置引用和option只能按表精确形式。所有数据无布尔数值、隐藏默认值或未列选项。

## 条件全集

### `surface_velocity`

role=`boundary`，variable=`normal_velocity`，operator=`surface_velocity`；location为surface全部三角面。必须出现。该算子恰一条覆盖表定完整位置。data恰含下列全部键：

| data键 | 类型、单位和含义 |
|---|---|
| `value` | components [2]；`m/s`；固体向外法向的表面振速W |



## 输出

outputs逻辑名与array key自由；每个quantity至少一次，可重复请求。全部float64、不含sampling、时间轴为harmonic，dtype／shape／components与单位按表及前述分量规则。

| quantity | 类型、单位及定义 | 支持位置、value_kind |
|---|---|---|
| `pressure` | components [2]；`Pa`；辐射声压P | receivers全部点，point |

receivers输出是其真实坐标处点值，不是区域积分或任意角度函数；没有隐含远场近似。结果HDF5仅含输出array、所需IDs及时间轴，严格复制输入身份与行序；不导出输入场、坐标或新网格。

## 接收条件与限制

外表面至多800三角面、9000节点，至多128接收点。每轴至多101帧，全部输入／输出场各至多3000000数值分量。正式数据须核验几何无自交／重叠、材料适用、小扰动线性范围、初边值相容、所请求点值／平均存在及物理解可确定，并用独立参考证明预算内精度；校验器不证明这些性质。不得以格式合法、求解器低残差或与同一离散一致替代声学正确性。
