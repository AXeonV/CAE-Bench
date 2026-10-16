# electrode-diffusion 数据契约

入口problem.json及data_file引用的扁平HDF5，路径相对清单。顶层采用CONTRACT结构，physics恰含model、parameters；model=`electrochemistry-electrode-diffusion-v1`，task可省略，出现须为`electrode-diffusion`。禁止profile、contract_version、analysis、materials混用；不接受未列参数、条件、字段或位置。

## 物理定义与支持组合

支持电解质充分过量，使一维0<x<L液体电势固定0；还原态R及氧化态O只扩散，∂t cR=D_R∂xx cR、∂t cO=D_O∂xx cO，无迁移、对流或体反应。x=L固定为初始均匀储槽浓度。x=0电极电位Δ(t)给定，令f=nF/(RT)、ψ=Δ−E0，j=nFk[(cR,s/c*)exp((1−α)fψ)−(cO,s/c*)exp(−αfψ)]，c_s为液体侧表面浓度。通量正向+x，N_R(0)=−j/(nF)、N_O(0)=+j/(nF)，N=−D∂x c；等价D_R cR_x(0)=j/(nF)、D_O cO_x(0)=−j/(nF)。必须耦合求表面浓度，不能以储槽值替代。无双电层、串联电阻或电位反馈。允许初始均匀浓度与初始非零反应通量的导数不相容：通量边界对t>0成立，采用该初态的抛物型连续极限解；t=0浓度取均匀初值，t=0电流按该初始表面浓度及Δ(0)计算，不要求初始浓度梯度同时满足通量。

## 全局参数

parameters恰含下表全部项；各项只有value、unit，数值有限，布尔不能作数值，JSON整数要求不得用浮点数替代。全部无缺省。

| 参数 | 单位 | 含义与值域 |
|---|---|---|
| `temperature` | `K` | 恒定温度T>0 |
| `gas_constant` | `J/(mol.K)` | 输入明确给定气体常数R>0 |
| `faraday` | `C/mol` | 输入明确给定法拉第常数F>0 |
| `length` | `m` | 有限扩散层L>0 |
| `diffusivity_reduced` | `m2/s` | 还原态恒定D_R>0 |
| `diffusivity_oxidized` | `m2/s` | 氧化态恒定D_O>0 |
| `concentration_scale` | `mol/m3` | 活度归一化浓度c*>0 |
| `electrons` | `1` | n为JSON整数1..4 |
| `alpha` | `1` | 阴极指数系数α，0<α<1 |
| `rate` | `mol/(m2.s)` | 标准面摩尔速率k>0 |
| `standard_potential` | `V` | 标准还原电位E0，与电解液0采用同一参考 |

## 位置、几何及身份

spatial_dimension=1，meshes、geometries均为空。entities表示真实有限对象，无虚构坐标；维度1表示真实一维空间坐标。IDs为int64、非负、严格递增，身份仅在location内有效，字段N轴按IDs行序对应，不按ID数值作数组下标。points位置仅定义真实边界／观测坐标，均为float64[N,1]、单位m，不是内部离散网格；ID不携带坐标信息。

| location | kind、数量 | 完整语义 |
|---|---|---|
| `electrode` | points，1..1项 | x=0处电极的液体侧位置 |
| `system` | entities，1..1项 | 唯一外部远端储槽／初态参数对象 |
| `probes` | points，1..256项 | 严格内部0<x<L的真实接收点，可重复坐标 |

## 时间、数组及重建

time_axes恰含initial、drive、observe。initial引用float64[1]=[0.0]；observe引用float64[T]，1≤T≤129，首项≥0且末项H>0；drive引用float64[B]，2≤B≤129、首项0且末项H，中间严格递增。输出只用observe，材料与初态用initial，驱动条件用drive。驱动逐对象在相邻时刻线性插值，覆盖[0,H]，不外推；输出请求不是内部时间步。

场均float64，完整形状[T,N,*component_shape]。scalar为[1]、components=["value"]；components按表中shape行优先展平标签为c1..cL（L为分量总数）。R/O双分量c1=还原态R、c2=氧化态O。

所有data只允许{"field":"逻辑字段名"}，禁止内联数值、option或数组。fields恰为实际被引用场；quantity等于data键名，键value例外等于该条件variable；逻辑字段名与array key自由且区分。字段必须在对应条件同location及上表规定时间轴，不能借相同数组长度配对其他身份。每字段均point，sampling显式，space=uniform、extrapolation=forbid；drive场time=linear，其他场time=constant。uniform表示各对象上给定值，不要求不同对象行相同，不作实体或观测点之间插值；连续物理解由方程求出，禁止把输入采样当内部解网格。

## 条件全集

### `initial`

role=`initial`，variable=`concentration`，operator=`initial`，location=`system`；所引用字段均为time_axis=`initial`（条件记录本身不含time_axis键）。恰一条，完整覆盖该位置。data恰含：

| 键 | 类型、单位及含义 |
|---|---|
| `value` | components [2]，`mol/m3`；全区间初始均匀cR0、cO0>0；x=L始终由同样浓度的储槽维持 |
### `potential`

role=`boundary`，variable=`potential`，operator=`potential`，location=`electrode`；所引用字段均为time_axis=`drive`（条件记录本身不含time_axis键）。恰一条，完整覆盖该位置。data恰含：

| 键 | 类型、单位及含义 |
|---|---|
| `value` | scalar [1]，`V`；电极电位Δ(t)=φm−φl，电解液φl=0 |

## 输出

每个下列quantity至少出现一次，可重复请求；逻辑名及array key自由。全部float64、point、observe轴，无sampling，分量规则同上。必须使用表中完整location及全部对象，不能新增输出位置、重排身份或省略分量。输出是瞬时状态，不是时间平均、单元平均或整体积分。

| quantity | 类型、单位、含义 | location |
|---|---|---|
| `concentration` | components [2]，`mol/m3`；内部点的cR、cO | `probes` |
| `surface_concentration` | components [2]，`mol/m3`；x=0液体侧唯一迹cR,s、cO,s | `electrode` |
| `faradaic_current` | scalar [1]，`A/m2`；单位真实电极面积的阳极法拉第电流j | `electrode` |

结果HDF5只含输出array和必需IDs／时间轴，严格复制输入支持数组；不输出输入场、坐标、网格或额外数组。t=0内部及表面浓度均取均匀初态，电流按初始浓度与Δ(0)的公式求值；边界导数不要求在t=0相容。

## 接收限制



对象数量、参数及场值范围见各表；输入和输出场各≤2000000数值分量。正式数据还须独立核验本题模型及材料适用、给定条件相容、所请求观测存在、参考精度与预算内可达性。涉及浓度场或库存演化时须验证全过程非负与适定性，排除任意病态尺度和无限刚性组合。声明检查不证明物理解、参考或数值准确性。不从目录、来源软件或隐藏配置补题意。
