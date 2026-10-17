# mixed-potential 数据契约

入口problem.json及data_file引用的扁平HDF5，路径相对清单。顶层采用CONTRACT结构，physics恰含model、parameters；model=`electrochemistry-mixed-potential-v1`，task可省略，出现须为`mixed-potential`。禁止profile、contract_version、analysis、materials混用；不接受未列参数、条件、字段或位置。

## 物理定义与支持组合

一个等电位金属导体表面具有多个独立通道r，每通道为R_r⇌O_r+n_r e⁻，正j表示氧化，浓度活度由外储槽维持。所有电位均相对同一固定参考。令f_r=n_rF/(RT)，ψ_r=Φ−φl_r−E0_r，j_r=n_r F k_r[aR_r exp((1−α_r)f_rψ_r)−aO_r exp(−α_r f_rψ_r)]。求唯一公共金属电位Φ，使Σ_r A_r j_r=I。I=0仅要求总电流为0，允许各通道存在非零且抵消的电流。所有A、k及活度严格正且0<α<1，保证总电流随Φ严格单调且两端无界。无双电层、欧姆压降、传质限制或未声明副反应；不把每通道分别置于Nernst平衡。

## 全局参数

parameters恰含下表全部项；各项只有value、unit，数值有限，布尔不能作数值，JSON整数要求不得用浮点数替代。全部无缺省。

| 参数 | 单位 | 含义与值域 |
|---|---|---|
| `temperature` | `K` | 恒定温度T>0 |
| `gas_constant` | `J/(mol.K)` | 输入明确给定气体常数R>0 |
| `faraday` | `C/mol` | 输入明确给定法拉第常数F>0 |
| `applied_current` | `A` | 公共金属给定总阳极电流I，可正负或0；0为整体开路 |

## 位置、几何及身份

spatial_dimension=1，meshes、geometries均为空。entities表示真实有限对象，无虚构坐标；维度1仅为有限对象的存储标记，不增加空间方程。IDs为int64、非负、严格递增，身份仅在location内有效，字段N轴按IDs行序对应，不按ID数值作数组下标。

| location | kind、数量 | 完整语义 |
|---|---|---|
| `metal` | entities，1..1项 | 唯一等电位导体，电势Φ相对于已固定公共参考 |
| `channels` | entities，1..32项 | 导体表面的独立氧化还原反应通道；不共享库存，输入活度由外部储槽维持 |

## 时间、数组及重建

time_axes恰含state，其引用float64[1]=[0.0]，所有输入和输出均用state；0是稳态存储标记，不是物理初态。

场均float64，完整形状[T,N,*component_shape]。scalar为[1]、components=["value"]；components按表中shape行优先展平标签为c1..cL（L为分量总数）。

所有data只允许{"field":"逻辑字段名"}，禁止内联数值、option或数组。fields恰为实际被引用场；quantity等于data键名，键value例外等于该条件variable；逻辑字段名与array key自由且区分。字段必须在对应条件同location及上表规定时间轴，不能借相同数组长度配对其他身份。每字段均point，sampling显式，space=uniform、extrapolation=forbid；所有场time=constant。uniform表示各对象上给定值，不要求不同对象行相同，不作实体或观测点之间插值；连续物理解由方程求出，禁止把输入采样当内部解网格。

## 条件全集

### `channels`

role=`material`，variable=`channel`，operator=`channels`，location=`channels`；所引用字段均为time_axis=`state`（条件记录本身不含time_axis键）。恰一条，完整覆盖该位置。data恰含：

| 键 | 类型、单位及含义 |
|---|---|
| `area` | scalar [1]，`m2`；该通道真实反应面积A>0 |
| `electrons` | scalar [1]，`1`；反应R→O+n e⁻的n，精确整数1..4 |
| `alpha` | scalar [1]，`1`；阴极指数系数α，0<α<1 |
| `rate` | scalar [1]，`mol/(m2.s)`；标准面摩尔速率k>0 |
| `standard_potential` | scalar [1]，`V`；标准还原电位E0，相对于同一公共参考 |
| `solution_potential` | scalar [1]，`V`；本通道电解液电势φl，同一公共参考 |
| `reduced_activity` | scalar [1]，`1`；还原态无量纲活度aR>0 |
| `oxidized_activity` | scalar [1]，`1`；氧化态无量纲活度aO>0 |

## 输出

每个下列quantity至少出现一次，可重复请求；逻辑名及array key自由。全部float64、point、state轴，无sampling，分量规则同上。必须使用表中完整location及全部对象，不能新增输出位置、重排身份或省略分量。输出是各独立工况的稳态值，不是时间平均、单元平均或整体积分。

| quantity | 类型、单位、含义 | location |
|---|---|---|
| `metal_potential` | scalar [1]，`V`；公共金属电势Φ | `metal` |
| `faradaic_current` | scalar [1]，`A/m2`；各通道阳极为正的法拉第电流密度j | `channels` |

结果HDF5只含输出array和必需IDs／时间轴，严格复制输入支持数组；不输出输入场、坐标、网格或额外数组。

## 接收限制



对象数量、参数及场值范围见各表；输入和输出场各≤2000000数值分量。正式数据还须独立核验本题模型及材料适用、给定条件相容、所请求观测存在、参考精度与预算内可达性。有限参数的极端条件仍须有稳定求值与预算内基准证据。声明检查不证明物理解、参考或数值准确性。不从目录、来源软件或隐藏配置补题意。
