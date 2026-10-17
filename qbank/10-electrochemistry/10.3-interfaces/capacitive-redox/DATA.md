# capacitive-redox 数据契约

入口problem.json及data_file引用的扁平HDF5，路径相对清单。顶层采用CONTRACT结构，physics恰含model、parameters；model=`electrochemistry-capacitive-redox-v1`，task可省略，出现须为`capacitive-redox`。禁止profile、contract_version、analysis、materials混用；不接受未列参数、条件、字段或位置。

## 物理定义与支持组合

各半电池彼此独立，恒温、封闭定容完全混合R/O液体；支持电解质与理想远端对电极将液体电势固定为0，其库存不属本题。工作界面R⇌O+n e⁻，阳极氧化为正；Δ=φm−φl、ψ=Δ−E0、f=nF/(RT)。jF=nFk[(cR/c*)exp((1−α)fψ)−(cO/c*)exp(−αfψ)]。Cdl dΔ/dt=J(t)−jF；dcR/dt=−A jF/(nFV)，dcO/dt=+A jF/(nFV)。Cdl为单位真实面积微分电容，J及jF也按真实工作面积计；电容不消耗R/O，jC=J−jF，cR+cO守恒。无空间扩散、热变化、串联电阻、额外均相反应或未声明电极。初始Δ不要求Nernst平衡，外加电流不要求初始为0。

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
| `cells` | entities，1..32项 | 独立完全混合的工作半电池；电解液电势恒定为0，无空间梯度 |

## 时间、数组及重建

time_axes恰含initial、drive、observe。initial引用float64[1]=[0.0]；observe引用float64[T]，1≤T≤129，首项≥0且末项H>0；drive引用float64[B]，2≤B≤129、首项0且末项H，中间严格递增。输出只用observe，材料与初态用initial，驱动条件用drive。驱动逐对象在相邻时刻线性插值，覆盖[0,H]，不外推；输出请求不是内部时间步。

场均float64，完整形状[T,N,*component_shape]。scalar为[1]、components=["value"]；components按表中shape行优先展平标签为c1..cL（L为分量总数）。R/O双分量c1=还原态R、c2=氧化态O。

所有data只允许{"field":"逻辑字段名"}，禁止内联数值、option或数组。fields恰为实际被引用场；quantity等于data键名，键value例外等于该条件variable；逻辑字段名与array key自由且区分。字段必须在对应条件同location及上表规定时间轴，不能借相同数组长度配对其他身份。每字段均point，sampling显式，space=uniform、extrapolation=forbid；drive场time=linear，其他场time=constant。uniform表示各对象上给定值，不要求不同对象行相同，不作实体或观测点之间插值；连续物理解由方程求出，禁止把输入采样当内部解网格。

## 条件全集

### `material`

role=`material`，variable=`interface`，operator=`material`，location=`cells`；所引用字段均为time_axis=`initial`（条件记录本身不含time_axis键）。恰一条，完整覆盖该位置。data恰含：

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

role=`initial`，variable=`concentration`，operator=`initial`，location=`cells`；所引用字段均为time_axis=`initial`（条件记录本身不含time_axis键）。恰一条，完整覆盖该位置。data恰含：

| 键 | 类型、单位及含义 |
|---|---|
| `value` | components [2]，`mol/m3`；依次R、O浓度，均≥0且每行总和>0 |
### `potential_initial`

role=`initial`，variable=`potential`，operator=`potential_initial`，location=`cells`；所引用字段均为time_axis=`initial`（条件记录本身不含time_axis键）。恰一条，完整覆盖该位置。data恰含：

| 键 | 类型、单位及含义 |
|---|---|
| `value` | scalar [1]，`V`；初始Δ=φm−φl=φm，可为任意有限值 |
### `current`

role=`source`，variable=`applied_current`，operator=`current`，location=`cells`；所引用字段均为time_axis=`drive`（条件记录本身不含time_axis键）。恰一条，完整覆盖该位置。data恰含：

| 键 | 类型、单位及含义 |
|---|---|
| `value` | scalar [1]，`A/m2`；单位真实面积外电路阳极电流J(t)，可正负或0 |

## 输出

每个下列quantity至少出现一次，可重复请求；逻辑名及array key自由。全部float64、point、observe轴，无sampling，分量规则同上。必须使用表中完整location及全部对象，不能新增输出位置、重排身份或省略分量。输出是瞬时状态，不是时间平均、单元平均或整体积分。

| quantity | 类型、单位、含义 | location |
|---|---|---|
| `potential` | scalar [1]，`V`；Δ=φm−φl，电解液电势为0，不是扣掉Nernst电位后的过电位 | `cells` |
| `concentration` | components [2]，`mol/m3`；依次cR、cO，按液体体积计 | `cells` |
| `faradaic_current` | scalar [1]，`A/m2`；jF，阳极正 | `cells` |
| `capacitive_current` | scalar [1]，`A/m2`；jC=J−jF，包含充放电符号 | `cells` |

结果HDF5只含输出array和必需IDs／时间轴，严格复制输入支持数组；不输出输入场、坐标、网格或额外数组。t=0浓度和电位取输入初态，jF按同一动力学求值，jC=J(0)−jF(0)。

## 接收限制

初始每个cells对象cR+cO>0；初始浓度允许某一态为0。所有参数和初态逐cell独立给定，未要求各行相同。

对象数量、参数及场值范围见各表；输入和输出场各≤2000000数值分量。正式数据还须独立核验本题模型及材料适用、给定条件相容、所请求观测存在、参考精度与预算内可达性。涉及浓度场或库存演化时须验证全过程非负与适定性，排除任意病态尺度和无限刚性组合。声明检查不证明物理解、参考或数值准确性。不从目录、来源软件或隐藏配置补题意。
