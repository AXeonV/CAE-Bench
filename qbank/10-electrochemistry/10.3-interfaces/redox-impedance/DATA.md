# redox-impedance 数据契约

入口problem.json及data_file引用的扁平HDF5，路径相对清单。顶层采用CONTRACT结构，physics恰含model、parameters；model=`electrochemistry-redox-impedance-v1`，task可省略，出现须为`redox-impedance`。禁止profile、contract_version、analysis、materials混用；不接受未列参数、条件、字段或位置。

## 物理定义与支持组合

恒温封闭定容完全混合R/O工作半电池，液体电势固定为0；支持电解质及远端对电极不计入库存。平衡cR,cO均正，Δeq=E0+(RT/(nF))ln(cO/cR)。令f=nF/(RT)、ψeq=Δeq−E0、j0=nFk(cR/c*)^α(cO/c*)^(1−α)、G=f j0，gR=(nFk/c*)exp((1−α)fψeq)，gO=−(nFk/c*)exp(−αfψeq)。对exp(+iωt)微扰，线性系统为δjF=GδΔ+gRδcR+gOδcO，iωδcR=−AδjF/(nFV)，iωδcO=+AδjF/(nFV)，δJ=δjF+iωCdlδΔ。输出Z=δΔ/δJ，单位Ohm.m²，不乘／除面积；任意非零微扰归一化给相同Z，不求有限振幅非线性响应。A和V决定有限库存反馈，不能直接套用无限储槽Rct并联电容；无扩散Warburg项、串联电阻或额外自由拟合项。所有ω>0，不请求DC零频或零库存极限。

## 全局参数

parameters恰含下表全部项；各项只有value、unit，数值有限，布尔不能作数值，JSON整数要求不得用浮点数替代。全部无缺省。

| 参数 | 单位 | 含义与值域 |
|---|---|---|
| `temperature` | `K` | 恒定温度T>0 |
| `gas_constant` | `J/(mol.K)` | 输入明确给定气体常数R>0 |
| `faraday` | `C/mol` | 输入明确给定法拉第常数F>0 |
| `concentration_scale` | `mol/m3` | 活度归一化浓度c*>0 |

## 位置、几何及身份

spatial_dimension=1，meshes、geometries均为空。entities表示真实有限对象，无虚构坐标；维度1仅为有限对象的存储标记，不增加空间方程。IDs为int64、非负、严格递增，身份仅在location内有效，字段N轴按IDs行序对应，不按ID数值作数组下标。

| location | kind、数量 | 完整语义 |
|---|---|---|
| `interface` | entities，1..1项 | 独立完全混合的工作半电池；电解液电势恒定为0，无空间梯度 |
| `frequencies` | entities，1..128项 | 独立频率对象，不作频率间插值，ID不代表频率 |

## 时间、数组及重建

time_axes恰含state，其引用float64[1]=[0.0]，所有输入和输出均用state；0是频域存储标记，不是物理初态或频率值。

场均float64，完整形状[T,N,*component_shape]。scalar为[1]、components=["value"]；components按表中shape行优先展平标签为c1..cL（L为分量总数）。平衡浓度双分量c1=R、c2=O；阻抗双分量c1=实部、c2=虚部。

所有data只允许{"field":"逻辑字段名"}，禁止内联数值、option或数组。fields恰为实际被引用场；quantity等于data键名，键value例外等于该条件variable；逻辑字段名与array key自由且区分。字段必须在对应条件同location及上表规定时间轴，不能借相同数组长度配对其他身份。每字段均point，sampling显式，space=uniform、extrapolation=forbid；所有场time=constant。uniform表示各对象上给定值，不要求不同对象行相同，不作实体或观测点之间插值；连续物理解由方程求出，禁止把输入采样当内部解网格。

## 条件全集

### `material`

role=`material`，variable=`interface`，operator=`material`，location=`interface`；所引用字段均为time_axis=`state`（条件记录本身不含time_axis键）。恰一条，完整覆盖该位置。data恰含：

| 键 | 类型、单位及含义 |
|---|---|
| `area` | scalar [1]，`m2`；实际工作电极面积A>0 |
| `volume` | scalar [1]，`m3`；固定液相体积V>0 |
| `capacitance` | scalar [1]，`F/m2`；按真实面积计的恒正微分电容Cdl |
| `electrons` | scalar [1]，`1`；R→O+n e⁻，n为精确整数1..4 |
| `alpha` | scalar [1]，`1`；阴极指数系数α，0<α<1 |
| `rate` | scalar [1]，`mol/(m2.s)`；标准面摩尔速率k>0 |
| `standard_potential` | scalar [1]，`V`；标准还原电位E0；与电解液电势0采用同一参考 |
### `initial`

role=`initial`，variable=`concentration`，operator=`initial`，location=`interface`；所引用字段均为time_axis=`state`（条件记录本身不含time_axis键）。恰一条，完整覆盖该位置。data恰含：

| 键 | 类型、单位及含义 |
|---|---|
| `value` | components [2]，`mol/m3`；平衡cR、cO，均严格>0 |
### `frequency`

role=`source`，variable=`angular_frequency`，operator=`frequency`，location=`frequencies`；所引用字段均为time_axis=`state`（条件记录本身不含time_axis键）。恰一条，完整覆盖该位置。data恰含：

| 键 | 类型、单位及含义 |
|---|---|
| `value` | scalar [1]，`rad/s`；角频率ω>0，非Hz |

## 输出

每个下列quantity至少出现一次，可重复请求；逻辑名及array key自由。全部float64、point、state轴，无sampling，分量规则同上。必须使用表中完整location及全部对象，不能新增输出位置、重排身份或省略分量。输出是指定角频率的线性响应，不是时间平均、单元平均或整体积分。

| quantity | 类型、单位、含义 | location |
|---|---|---|
| `area_impedance` | components [2]，`Ohm.m2`；Z=δΔ/δJ，最内轴实部、虚部，exp(+iωt) | `frequencies` |

结果HDF5只含输出array和必需IDs／时间轴，严格复制输入支持数组；不输出输入场、坐标、网格或额外数组。

## 接收限制

初始记录在此表示用于线性化的平衡组成，不是待积分的物理时间；Δeq由正的cR、cO和E0按本题公式确定，没有额外输入金属电势或初始扰动。

对象数量、参数及场值范围见各表；输入和输出场各≤2000000数值分量。正式数据还须独立核验本题模型及材料适用、给定条件相容、所请求观测存在、参考精度与预算内可达性。有限参数的极端条件仍须有稳定求值与预算内基准证据。声明检查不证明物理解、参考或数值准确性。不从目录、来源软件或隐藏配置补题意。
