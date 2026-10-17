# slab-transport-transient 数据契约

problem.json及data_file引用的扁平HDF5遵循通用CONTRACT，路径相对清单目录。physics恰含model、parameters；model=`radiation-slab-transport-transient-v1`。task可省略，若出现只能为`slab-transport-transient`；模型不由目录或ID推断。禁止profile、contract_version、analysis、materials混用。

## 物理定义

无限横向分层平板、一维x、方向余弦μ∈[−1,1]，方位角已积分。φ_g=∫ψ_g dμ、J_g=∫μψ_g dμ，不乘2π／4π。Σt_g=Σa_g+Σ_h S[h,g]，有限群速下v_g^−1 ∂tψ_g+μ∂xψ_g+Σt_gψ_g=(q_g+Σ_h S[g,h]φ_h)/2。吸收为正、各向同性非增殖散射，无裂变或反馈。t=0层内各向同性ψ_g=φ0_g/2；层间初值可间断，t>0内部界面ψ连续，入射边界和体源在整个区间恒定。t=0边界／界面不相容按初边值输运问题的内域初始迹及t>0入射理解；不把初态改成平衡场。求指定时刻的标量通量与流，包括有限传播效应，不用准稳态代替。光子／中子标记仅说明粒子种类，无隐藏核数据或群宽度权重。

## 全局参数

physics.parameters恰含下表全部项，每项仅value和unit；数值有限，布尔不能作数值，整数须JSON整数。

| 参数 | 单位 | 定义及范围 |
|---|---|---|
| `group_count` | `1` | 群数G，JSON整数1..4；各群是输入给定有效响应的离散群，无隐含能群宽度权重 |
| `particle` | `1` | JSON整数0=光子，1=中子；不触发额外核数据或自动响应 |

## 对象与几何

spatial_dimension固定1。meshes和geometries均为空。1表示平板法向全局x轴。locations恰含下表；IDs为int64、非负严格递增，system必须ID=[0]；其余固定ID规则按表。层从x=0按IDs数组行序排列，H为全部width之和，坐标单位m；各层IDs可非连续，不从ID数值推坐标。所有累计界面必须有限且严格递增。probes.coordinates为float64[N,1]；每点x与任一界面的距离须≥1e−10·H且严格在(0,H)。不要求按坐标排序，值始终按IDs对应；无界面迹或边界导数请求。

| location | 定义与数量 |
|---|---|
| `layers` | entities，1..32项；按IDs行序沿+x排列的材料层对象，x=0起始；层内参数常值 |
| `system` | entities，1..1项；完整平板系统对象，ID固定0 |
| `probes` | points，1..128项；真实位置x，严格在层内部，排除全部界面与两端；不作空间重建 |

## 时间与数组

time_axes恰含`requests`、`static`。static恰为float64[1]的[0.0]，静态参数及初态记录引用static。requests为float64[T]，1≤T≤256，所有值在[0,t_end]，严格递增；t_end定义为requests最后值且必须>0，不要求首项为0。输出时刻不是内部步长；初态总是在物理t=0。所有时间单位s，时间数组key自由。未列轴不允许，输出均引用requests。

字段全部float64，shape=[T,N,*component_shape]，T取所引用时间轴长度，N取location IDs长度。scalar为kind=scalar、component_shape=[1]、components=["value"]；其余为kind=components，shape按表代入g=group_count，components为按行优先展开的c1..cL（从c1开始、末轴变化最快），包括矩阵非对角及零项。所有value_kind=point，entities表示其对象自身参数或集总状态，不表示空间平均。条件data只用{"field":"逻辑字段名"}引用；对应fields记录的array才是HDF5 key，名称自由。fields恰为条件实际引用项；quantity等于data键名，键value例外等于该条件variable；字段必须同location及上述时间轴。单个字段可被多个相容引用共享，不能以数组等长代替身份。无内联常量／选项或隐式广播。每个输入字段必须显式sampling：space=uniform（每个独立对象自身的值，不在对象间插值），extrapolation=forbid；static的time=constant。层参数按对象记录构成各层常值，不在层之间线性插值。

## 条件全集

### `layers`

conditions中恰一条：role=`material`，variable=`layer`，operator=`layers`，location=`layers`；完整覆盖该location，使用`static`时间轴。data恰含下列键，无默认值：

| data键 | 类型、单位、含义与范围 |
|---|---|
| `width` | scalar [1]；`m`；层厚h>0 |

### `medium`

conditions中恰一条：role=`material`，variable=`medium`，operator=`medium`，location=`layers`；完整覆盖该location，使用`static`时间轴。data恰含下列键，无默认值：

| data键 | 类型、单位、含义与范围 |
|---|---|
| `absorption` | components ['g']；`1/m`；宏观吸收Σa_g>0 |
| `scatter` | components ['g', 'g']；`1/m`；各向同性群转移S[g,h]≥0，第一轴出射群g、第二轴入射群h；含自散射 |

### `source`

conditions中恰一条：role=`source`，variable=`source`，operator=`source`，location=`layers`；完整覆盖该location，使用`static`时间轴。data恰含下列键，无默认值：

| data键 | 类型、单位、含义与范围 |
|---|---|
| `value` | components ['g']；`1/(m3.s)`；层内常量总群体源q_g≥0；各向同性角源q_g/2 |

### `incoming`

conditions中恰一条：role=`boundary`，variable=`incoming`，operator=`incoming`，location=`system`；完整覆盖该location，使用`static`时间轴。data恰含下列键，无默认值：

| data键 | 类型、单位、含义与范围 |
|---|---|
| `left` | components ['g']；`1/(m2.s)`；x=0、μ>0的角通量ψ=L_g≥0，入射半球内不依赖μ |
| `right` | components ['g']；`1/(m2.s)`；x=H、μ<0的角通量ψ=R_g≥0，入射半球内不依赖μ |

### `speed`

conditions中恰一条：role=`material`，variable=`speed`，operator=`speed`，location=`system`；完整覆盖该location，使用`static`时间轴。data恰含下列键，无默认值：

| data键 | 类型、单位、含义与范围 |
|---|---|
| `value` | components ['g']；`m/s`；群速v_g>0，全空间常量 |

### `initial`

conditions中恰一条：role=`initial`，variable=`initial_flux`，operator=`initial`，location=`layers`；完整覆盖该location，使用`static`时间轴。data恰含下列键，无默认值：

| data键 | 类型、单位、含义与范围 |
|---|---|
| `value` | components ['g']；`1/(m2.s)`；t=0层内各向同性标量通量φ0_g≥0，ψ0=φ0/2；独立于体源和入射 |

## 输出

每个quantity至少出现一次，可重复请求，outputs逻辑名与array key自由；同quantity的单位、位置、shape均按表，float64、value_kind=point、时间轴=requests、无sampling。各输出按下表定义，不另作时间或空间平均。

| quantity | 类型、单位与含义 | location |
|---|---|---|
| `scalar_flux` | components ['g']；`1/(m2.s)`；各群标量通量φ_g，保持输入激励确定的绝对幅值，不另作归一化 | `probes` |
| `current` | components ['g']；`1/(m2.s)`；各群沿+x的净粒子流J_g，可为负 | `probes` |

结果仅含要求的输出array及其输入IDs／时间轴的精确副本，不导出坐标、输入场或额外数组。

## 接收限制

各表规模为公开上限；输入场总分量与输出场总分量分别不超过2000000。所有输入／输出浮点值有限。输入符合本题物理模型的适用范围，全部请求的观测存在且有限，并可在公开资源预算内达到评分精度。
