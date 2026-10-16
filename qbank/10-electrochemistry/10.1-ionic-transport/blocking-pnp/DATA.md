# blocking-pnp 数据契约

入口problem.json及data_file引用的扁平HDF5，路径相对清单。顶层采用CONTRACT结构，physics恰含model、parameters；model=`electrochemistry-blocking-pnp-v1`，task可省略，出现须为`blocking-pnp`。禁止profile、contract_version、analysis、materials混用；不接受未列参数、条件、字段或位置。

## 物理定义与支持组合

一维0<x<L的封闭等温理想稀溶液，介电率ε恒定。通量正向为+x：N_i=−D_i(∂x c_i+z_iF c_i ∂xφ/(RT))，∂t c_i=−∂x N_i；−εφ_xx=FΣ_i z_i c_i。两端φ由历史给定，所有离子两端N_i=0（阻挡，无通透、吸附或法拉第反应）。初态各c_i全区间均匀且电中性，两端初始电势均为0，因此初始φ=0与零通量相容。后续各离子有限库存分别守恒；不可用储槽Boltzmann浓度替代此瞬态问题。σL=−εφ_x(0)，σR=+εφ_x(L)，为电极真实面积电荷。无流动、固定体电荷、Stern层、体反应或额外电中性方程，电势必须与空间电荷自洽。

## 全局参数

parameters恰含下表全部项；各项只有value、unit，数值有限，布尔不能作数值，JSON整数要求不得用浮点数替代。全部无缺省。

| 参数 | 单位 | 含义与值域 |
|---|---|---|
| `temperature` | `K` | 恒定温度T>0 |
| `gas_constant` | `J/(mol.K)` | 输入明确给定气体常数R>0 |
| `faraday` | `C/mol` | 输入明确给定法拉第常数F>0 |
| `species_count` | `1` | 离子及可选中性组分数s，JSON整数2..8 |
| `length` | `m` | 液体区间长度L>0 |
| `permittivity` | `F/m` | 绝对介电率ε>0，不是相对介电常数 |

## 位置、几何及身份

spatial_dimension=1，meshes、geometries均为空。entities表示真实有限对象，无虚构坐标；维度1表示真实一维空间坐标。IDs为int64、非负、严格递增，身份仅在location内有效，字段N轴按IDs行序对应，不按ID数值作数组下标。points位置仅定义真实边界／观测坐标，均为float64[N,1]、单位m，不是内部离散网格；ID不携带坐标信息。

| location | kind、数量 | 完整语义 |
|---|---|---|
| `system` | entities，1..1项 | 唯一均匀溶液材料对象 |
| `left` | points，1..1项 | x=0的左电极液体侧边界 |
| `right` | points，1..1项 | x=L的右电极液体侧边界 |
| `probes` | points，1..256项 | 真实观测点0≤x≤L，可重复坐标；边界浓度取液体迹 |

## 时间、数组及重建

time_axes恰含initial、drive、observe。initial引用float64[1]=[0.0]；observe引用float64[T]，1≤T≤129，首项≥0且末项H>0；drive引用float64[B]，2≤B≤129、首项0且末项H，中间严格递增。输出只用observe，材料与初态用initial，驱动条件用drive。驱动逐对象在相邻时刻线性插值，覆盖[0,H]，不外推；输出请求不是内部时间步。

场均float64，完整形状[T,N,*component_shape]。scalar为[1]、components=["value"]；components按表中shape行优先展平标签为c1..cL（L为分量总数）。s替换为species_count。s分量依次对应输入组分i=1..s。

所有data只允许{"field":"逻辑字段名"}，禁止内联数值、option或数组。fields恰为实际被引用场；quantity等于data键名，键value例外等于该条件variable；逻辑字段名与array key自由且区分。字段必须在对应条件同location及上表规定时间轴，不能借相同数组长度配对其他身份。每字段均point，sampling显式，space=uniform、extrapolation=forbid；drive场time=linear，其他场time=constant。uniform表示各对象上给定值，不要求不同对象行相同，不作实体或观测点之间插值；连续物理解由方程求出，禁止把输入采样当内部解网格。

## 条件全集

### `ions`

role=`material`，variable=`ions`，operator=`ions`，location=`system`；所引用字段均为time_axis=`initial`（条件记录本身不含time_axis键）。恰一条，完整覆盖该位置。data恰含：

| 键 | 类型、单位及含义 |
|---|---|
| `charge` | components [s]，`1`；电荷数z_i，整数−3..3；至少一个正与一个负，允许中性组分 |
| `diffusivity` | components [s]，`m2/s`；各组分恒定D_i>0 |
### `initial`

role=`initial`，variable=`concentration`，operator=`initial`，location=`system`；所引用字段均为time_axis=`initial`（条件记录本身不含time_axis键）。恰一条，完整覆盖该位置。data恰含：

| 键 | 类型、单位及含义 |
|---|---|
| `value` | components [s]，`mol/m3`；全区间均匀c_i0>0，Σz_i c_i0=0 |
### `left`

role=`boundary`，variable=`potential`，operator=`left`，location=`left`；所引用字段均为time_axis=`drive`（条件记录本身不含time_axis键）。恰一条，完整覆盖该位置。data恰含：

| 键 | 类型、单位及含义 |
|---|---|
| `value` | scalar [1]，`V`；边界液体电势φ，相对于固定同一φ=0参考；正负均可 |
### `right`

role=`boundary`，variable=`potential`，operator=`right`，location=`right`；所引用字段均为time_axis=`drive`（条件记录本身不含time_axis键）。恰一条，完整覆盖该位置。data恰含：

| 键 | 类型、单位及含义 |
|---|---|
| `value` | scalar [1]，`V`；边界液体电势φ，相对于固定同一φ=0参考；正负均可 |

## 输出

每个下列quantity至少出现一次，可重复请求；逻辑名及array key自由。全部float64、point、observe轴，无sampling，分量规则同上。必须使用表中完整location及全部对象，不能新增输出位置、重排身份或省略分量。输出是瞬时状态，不是时间平均、单元平均或整体积分。

| quantity | 类型、单位、含义 | location |
|---|---|---|
| `surface_charge_left` | scalar [1]，`C/m2`；该电极单位真实面积自由电荷，左−εφ_x(0)，右+εφ_x(L)，无Stern层 | `left` |
| `surface_charge_right` | scalar [1]，`C/m2`；该电极单位真实面积自由电荷，左−εφ_x(0)，右+εφ_x(L)，无Stern层 | `right` |
| `potential` | scalar [1]，`V`；液体电势φ(x,t) | `probes` |
| `concentration` | components [s]，`mol/m3`；按液体体积计的组分浓度，轴i与输入一致 | `probes` |

结果HDF5只含输出array和必需IDs／时间轴，严格复制输入支持数组；不输出输入场、坐标、网格或额外数组。t=0浓度取全区间初始值，电势及两个表面电荷均为0。

## 接收限制

初始电中性要求将存储float64视为精确实数后Σz_i c_i0严格为0；声明检查使用精确二进制有理数，无电中性容差、不投影输入；两端drive首帧电势必须精确为0。各drive帧每端max_i |z_i F φ端/(RT)|≤20；线性历史的中间值亦有界。

对象数量、参数及场值范围见各表；输入和输出场各≤2000000数值分量。正式数据还须独立核验本题模型及材料适用、给定条件相容、所请求观测存在、参考精度与预算内可达性。涉及浓度场或库存演化时须验证全过程非负与适定性，排除任意病态尺度和无限刚性组合。声明检查不证明物理解、参考或数值准确性。不从目录、来源软件或隐藏配置补题意。
