# ionic-equilibrium 数据契约

入口problem.json及data_file引用的扁平HDF5，路径相对清单。顶层采用CONTRACT结构，physics恰含model、parameters；model=`electrochemistry-ionic-equilibrium-v1`，task可省略，出现须为`ionic-equilibrium`。禁止profile、contract_version、analysis、materials混用；不接受未列参数、条件、字段或位置。

## 物理定义与支持组合

一维平行平板之间0<x<L，等温理想稀溶液、恒定绝对介电率ε，液体电势相对于同一储槽φ=0参考。各组分与该电化学势储槽平衡：c_i(x)=c_i,∞ exp(−z_iFφ/(RT))；−εφ_xx=FΣ_i z_i c_i。两端分别给定φ(0)、φ(L)。给定储槽浓度为电中性，不对有限间隙内各离子总数另加守恒或独立归一化约束。表面电荷σL=−εφ_x(0)，σR=+εφ_x(L)，均按该电极真实面积计。无固定体电荷、Stern层、离子有限尺寸、化学反应或电流；不是线性Debye–Hückel近似。

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

time_axes恰含state，其引用float64[1]=[0.0]，所有输入和输出均用state；0是稳态存储标记，不是物理初态。

场均float64，完整形状[T,N,*component_shape]。scalar为[1]、components=["value"]；components按表中shape行优先展平标签为c1..cL（L为分量总数）。s替换为species_count。s分量依次对应输入组分i=1..s。

所有data只允许{"field":"逻辑字段名"}，禁止内联数值、option或数组。fields恰为实际被引用场；quantity等于data键名，键value例外等于该条件variable；逻辑字段名与array key自由且区分。字段必须在对应条件同location及上表规定时间轴，不能借相同数组长度配对其他身份。每字段均point，sampling显式，space=uniform、extrapolation=forbid；所有场time=constant。uniform表示各对象上给定值，不要求不同对象行相同，不作实体或观测点之间插值；连续物理解由方程求出，禁止把输入采样当内部解网格。

## 条件全集

### `ions`

role=`material`，variable=`ions`，operator=`ions`，location=`system`；所引用字段均为time_axis=`state`（条件记录本身不含time_axis键）。恰一条，完整覆盖该位置。data恰含：

| 键 | 类型、单位及含义 |
|---|---|
| `charge` | components [s]，`1`；电荷数z_i，整数−3..3；至少一个正与一个负，允许中性组分 |
| `reservoir` | components [s]，`mol/m3`；φ=0储槽浓度c_i,∞>0；Σz_i c_i,∞=0 |
### `left`

role=`boundary`，variable=`potential`，operator=`left`，location=`left`；所引用字段均为time_axis=`state`（条件记录本身不含time_axis键）。恰一条，完整覆盖该位置。data恰含：

| 键 | 类型、单位及含义 |
|---|---|
| `value` | scalar [1]，`V`；边界液体电势φ，相对于固定同一φ=0参考；正负均可 |
### `right`

role=`boundary`，variable=`potential`，operator=`right`，location=`right`；所引用字段均为time_axis=`state`（条件记录本身不含time_axis键）。恰一条，完整覆盖该位置。data恰含：

| 键 | 类型、单位及含义 |
|---|---|
| `value` | scalar [1]，`V`；边界液体电势φ，相对于固定同一φ=0参考；正负均可 |

## 输出

每个下列quantity至少出现一次，可重复请求；逻辑名及array key自由。全部float64、point、state轴，无sampling，分量规则同上。必须使用表中完整location及全部对象，不能新增输出位置、重排身份或省略分量。输出是各独立工况的稳态值，不是时间平均、单元平均或整体积分。

| quantity | 类型、单位、含义 | location |
|---|---|---|
| `surface_charge_left` | scalar [1]，`C/m2`；该电极单位真实面积自由电荷，左−εφ_x(0)，右+εφ_x(L)，无Stern层 | `left` |
| `surface_charge_right` | scalar [1]，`C/m2`；该电极单位真实面积自由电荷，左−εφ_x(0)，右+εφ_x(L)，无Stern层 | `right` |
| `potential` | scalar [1]，`V`；液体电势φ(x) | `probes` |
| `concentration` | components [s]，`mol/m3`；按液体体积计的组分浓度，轴i与输入一致 | `probes` |

结果HDF5只含输出array和必需IDs／时间轴，严格复制输入支持数组；不输出输入场、坐标、网格或额外数组。

## 接收限制

储槽满足Σz_i c_i,∞=0；按存储float64作为精确实数计算加权和，必须严格为0。声明检查使用精确二进制有理数，无电中性容差、不投影输入。每端还须max_i |z_i F φ端/(RT)|≤20，限制本题平衡指数范围。

对象数量、参数及场值范围见各表；输入和输出场各≤2000000数值分量。正式数据还须独立核验本题模型及材料适用、给定条件相容、所请求观测存在、参考精度与预算内可达性。涉及浓度场或库存演化时须验证全过程非负与适定性，排除任意病态尺度和无限刚性组合。声明检查不证明物理解、参考或数值准确性。不从目录、来源软件或隐藏配置补题意。
