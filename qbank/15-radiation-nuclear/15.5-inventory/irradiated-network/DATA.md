# irradiated-network 数据契约

problem.json及data_file引用的扁平HDF5遵循通用CONTRACT，路径相对清单目录。physics恰含model、parameters；model=`radiation-irradiated-network-v1`。task可省略，若出现只能为`irradiated-network`；模型不由目录或ID推断。禁止profile、contract_version、analysis、materials混用。

## 物理定义

有限库存受给定外部单群标量通量照射，r_j(t)=σ_jΦ(t)。dN_i/dt=Σ_j[B[i,j]λ_j+Y[i,j]r_j(t)]N_j−[λ_i+r_i(t)]N_i。B、Y第一轴目的核素、第二轴来源核素；对角为0、各列和≤1，缺额离开系统，不支持一个反应生成多个被跟踪原子的裂变产额。衰变正边图无环，反应图可循环；允许零截面及稳定核素。所有率及局部衰变能由输入给定，不下载核库，不作自屏蔽、通量或功率反馈，无补料或迁移。输出A=Σλ_j N_j及P=Σε_jλ_jN_j只计衰变；无反应沉积能输入，不把它计入P。Φ按给定历史连续分段线性插值。

## 全局参数

physics.parameters恰含下表全部项，每项仅value和unit；数值有限，布尔不能作数值，整数须JSON整数。

| 参数 | 单位 | 定义及范围 |
|---|---|---|
| `nuclide_count` | `1` | 核素数N，JSON整数1..32 |

## 对象与几何

spatial_dimension固定1。meshes和geometries均为空。1仅为有限维系统的协议标记，不引入空间方程。locations恰含下表；IDs为int64、非负严格递增，system必须ID=[0]；其余固定ID规则按表。分支矩阵B和（若有）Y逐列和≤1，对角恰0，不用容差放宽；λ=0的核素其B列必须全0。B的正边图无环。矩阵分量顺序由nuclides IDs确定，不取决于conditions排列。

| location | 定义与数量 |
|---|---|
| `nuclides` | entities，1..32项；核素对象，恰N个，IDs固定0..N−1，矩阵分量按此顺序；不凭ID查询核数据 |
| `system` | entities，1..1项；完整库存系统，ID固定0 |

## 时间与数组

time_axes恰含`control`、`requests`、`static`。static恰为float64[1]的[0.0]，静态参数及初态记录引用static。requests为float64[T]，1≤T≤256，所有值在[0,t_end]，严格递增；t_end定义为requests最后值且必须>0，不要求首项为0。输出时刻不是内部步长；初态总是在物理t=0。control为float64[K]，2≤K≤256，首项0、末项恰等于t_end；控制字段逐区间线性插值、端点取存储值，禁止外推。control和requests可不同，内部时间步自选。所有时间单位s，时间数组key自由。未列轴不允许，输出均引用requests。

字段全部float64，shape=[T,N,*component_shape]，T取所引用时间轴长度，N取location IDs长度。scalar为kind=scalar、component_shape=[1]、components=["value"]；其余为kind=components，shape按表代入n=nuclide_count，components为按行优先展开的c1..cL（从c1开始、末轴变化最快），包括矩阵非对角及零项。所有value_kind=point，entities表示其对象自身参数或集总状态，不表示空间平均。条件data只用{"field":"逻辑字段名"}引用；对应fields记录的array才是HDF5 key，名称自由。fields恰为条件实际引用项；quantity等于data键名，键value例外等于该条件variable；字段必须同location及上述时间轴。单个字段可被多个相容引用共享，不能以数组等长代替身份。无内联常量／选项或隐式广播。每个输入字段必须显式sampling：space=uniform（每个独立对象自身的值，不在对象间插值），extrapolation=forbid；static的time=constant，control的time=linear。

## 条件全集

### `nuclides`

conditions中恰一条：role=`material`，variable=`nuclide`，operator=`nuclides`，location=`nuclides`；完整覆盖该location，使用`static`时间轴。data恰含下列键，无默认值：

| data键 | 类型、单位、含义与范围 |
|---|---|
| `decay` | scalar [1]；`1/s`；λ_j≥0，允许稳定核素 |
| `energy` | scalar [1]；`J`；每次衰变局部沉积能ε_j≥0，已扣除逃逸能，不是质量亏损 |

### `branches`

conditions中恰一条：role=`material`，variable=`decay_branch`，operator=`branches`，location=`system`；完整覆盖该location，使用`static`时间轴。data恰含下列键，无默认值：

| data键 | 类型、单位、含义与范围 |
|---|---|
| `value` | components ['n', 'n']；`1`；B[i,j]≥0，j衰变后进入i的分支；对角0、列和≤1，缺额流出系统；正边图无环 |

### `initial`

conditions中恰一条：role=`initial`，variable=`inventory`，operator=`initial`，location=`nuclides`；完整覆盖该location，使用`static`时间轴。data恰含下列键，无默认值：

| data键 | 类型、单位、含义与范围 |
|---|---|
| `value` | scalar [1]；`1`；各核素初始原子数N_j(0)≥0，原子计数无量纲 |

### `reaction`

conditions中恰一条：role=`material`，variable=`reaction`，operator=`reaction`，location=`nuclides`；完整覆盖该location，使用`static`时间轴。data恰含下列键，无默认值：

| data键 | 类型、单位、含义与范围 |
|---|---|
| `cross_section` | scalar [1]；`m2`；给定单群有效微观移除截面σ_j≥0；不含衰变 |

### `products`

conditions中恰一条：role=`material`，variable=`reaction_branch`，operator=`products`，location=`system`；完整覆盖该location，使用`static`时间轴。data恰含下列键，无默认值：

| data键 | 类型、单位、含义与范围 |
|---|---|
| `value` | components ['n', 'n']；`1`；Y[i,j]≥0，j反应后生成i；对角0、列和≤1，缺额流出系统，允许反应循环；不支持裂变多产物增殖 |

### `history`

conditions中恰一条：role=`source`，variable=`irradiation`，operator=`history`，location=`system`；完整覆盖该location，使用`control`时间轴。data恰含下列键，无默认值：

| data键 | 类型、单位、含义与范围 |
|---|---|
| `value` | scalar [1]；`1/(m2.s)`；给定外部标量粒子通量Φ(t)≥0，速率r_j=σ_jΦ，不作库存反馈 |

## 输出

每个quantity至少出现一次，可重复请求，outputs逻辑名与array key自由；同quantity的单位、位置、shape均按表，float64、value_kind=point、时间轴=requests、无sampling。各输出按下表定义，不另作时间或空间平均。

| quantity | 类型、单位与含义 | location |
|---|---|---|
| `inventory` | scalar [1]；`1`；各核素原子数N_j(t) | `nuclides` |
| `activity` | scalar [1]；`Bq`；Σ_j λ_j N_j(t)，包含全部库存核素，无额外分支倍数 | `system` |
| `decay_power` | scalar [1]；`W`；Σ_j ε_j λ_j N_j(t)，仅衰变沉积，不包含照射反应能 | `system` |

结果仅含要求的输出array及其输入IDs／时间轴的精确副本，不导出坐标、输入场或额外数组。

## 接收限制

各表规模为公开上限；输入场总分量与输出场总分量分别不超过2000000。所有输入／输出浮点值有限。正式数据须独立验证模型适用、观测存在、参考收敛及同预算可达性，正式数据接收须有预算内达到公开精度的独立数值证据；这不是由结构检查自动证明的事实，不能由参数正值代替数值证据。
