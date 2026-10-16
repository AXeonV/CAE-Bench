# adiabatic-combustion 数据契约

入口problem.json及data_file引用的扁平HDF5，路径相对清单；顶层采用CONTRACT通用结构。physics恰含model、parameters，model=`species-adiabatic-combustion-v1`；task可省略，出现须为`adiabatic-combustion`。禁止profile、contract_version、analysis、materials混用。不接受未列字段、位置、条件或参数组合。

## 物理与支持范围

各独立完全混合、封闭、刚性定容理想气体反应器绝热，无流动功、热损失或外源。v_r=a_r exp(−E_r/(RT))∏_i(c_i/c*)^α_ri，0^0=1；dc_i/dt=Σ_r(β_ri−α_ri)v_r。u_i(T)=u_i,ref+cv_i(T−Tref)，单位体积总内能U=Σ_i c_i u_i(T)始终等于初态U0；因此(Σ_i c_i cv_i)dT/dt=−Σ_i u_i(T) dc_i/dt。压力p=RTΣ_i c_i。形成内能已包含在u_i,ref，不另加反应热。全部反应不可逆且质量守恒，允许惰性组分及多步反应；不根据名称引入数据库、辐射、解离平衡或反向速率。仅支持cv常量适用且全过程250≤T≤5000K的有限机理，初始总浓度严格正。燃烧考查组成与温度的热反馈，可含自加速点火，不要求输出阈值点火延迟或传播火焰。

## 全局参数

parameters恰含下表全部项；每项只有value、unit，数值有限、布尔不是数值、integer必须JSON整数；全部参数无缺省。

| 参数 | 单位 | 含义及值域 |
|---|---|---|
| `species_count` | `1` | 组分数s，JSON整数2..8；非平凡质量守恒反应至少需两个组分 |
| `reaction_count` | `1` | 反应数r，JSON整数1..16 |
| `concentration_scale` | `mol/m3` | 共同活度归一化浓度c*>0，不是初态 |
| `gas_constant` | `J/(mol.K)` | 理想气体常数R>0，由输入给定 |
| `reference_temperature` | `K` | 内能参考温度Tref>0 |

## 几何、位置和身份

spatial_dimension=1；meshes、geometries均为空。entities表示实际混合容器、反应或参数对象，无虚构坐标；空间维度1仅为此有限维模型的存储标记，不引入空间方程。IDs按CONTRACT非负、严格递增，实体行与字段N轴对应，ID不能作数组下标。

| location | kind及数量 | 完整语义 |
|---|---|---|
| `system` | entities，1..1项 | 唯一材料／动力学参数对象，不是空间探针 |
| `vessels` | entities，1..32项 | 独立完全混合有限容积反应器／容器，IDs可不连续，各组分轴按c1..cs |
| `reactions` | entities，1..16项 | r条有向不可逆反应，按IDs行序；可逆反应必须显式给两条 |

## 时间、数组与重建

time_axes恰为initial、observe。initial引用float64[1]=[0.0]；observe引用float64[T]，1≤T≤129，首项≥0、末项H>0；输出仅用observe，所有输入场仅用initial。输出请求不约束求解器内部时间步，也不表示帧间跳跃。物理初态固定t=0，不是迭代初猜。

场均float64，形状[T,N,*component_shape]。scalar固定shape=[1]、components=["value"]；components类型按表中shape行优先展平为["c1",...,"cL"]，L为分量总数。s替换为species_count；所有组分按i=1..s，同一算例各表始终同序，标签不表示化学名称。逻辑字段名与HDF5 array key自由且区分；quantity等于data键名，键value例外等于该条件variable。引用只能同location、同规定时间轴，fields恰为被条件实际引用的字段，无未用字段。

所有data均必须采用{"field":"逻辑字段名"}，不接受内联数值、option或数组；表中每种operator恰一条，data键全集如下，无可选键／缺省参数或其他条件。每字段均point；sampling显式，extrapolation=forbid。材料与所有entities场space=uniform、time=constant，表示各对象固定属性／初态，不作对象间插值；uniform不要求不同实体行的值相同，各行独立给定。

## 条件全集

### `initial`

role=`initial`，variable=`concentration`，operator=`initial`，location=`vessels`；时间轴`initial`，完整覆盖该位置。data恰含：

| 键 | 类型、单位、语义与限制 |
|---|---|
| `value` | components [s]，`mol/m3`；初始浓度c_i≥0 |
### `kinetics`

role=`material`，variable=`kinetics`，operator=`kinetics`，location=`reactions`；时间轴`initial`，完整覆盖该位置。data恰含：

| 键 | 类型、单位、语义与限制 |
|---|---|
| `reactants` | components [s]，`1`；反应物计量α_ri，整数0..4，每行总和1..4 |
| `products` | components [s]，`1`；生成物计量β_ri，整数0..4，每行总和1..8，β行不等于α行 |
| `prefactor` | scalar [1]，`mol/(m3.s)`；反应体积速率前因子a_r≥0，已用c*归一化，非传统随反应级数变单位的k |
| `activation` | scalar [1]，`J/mol`；活化能E_r≥0 |
### `species`

role=`material`，variable=`species`，operator=`species`，location=`system`；时间轴`initial`，完整覆盖该位置。data恰含：

| 键 | 类型、单位、语义与限制 |
|---|---|
| `molar_mass` | components [s]，`kg/mol`；组分摩尔质量M_i>0；每行反应Σ(β−α)M=0 |
| `heat_capacity` | components [s]，`J/(mol.K)`；定容摩尔热容cv_i>0，整个温度区间常量 |
| `reference_energy` | components [s]，`J/mol`；Tref处的摩尔内能u_i,ref，含形成内能；可正负 |
### `thermal_initial`

role=`initial`，variable=`temperature`，operator=`thermal_initial`，location=`vessels`；时间轴`initial`，完整覆盖该位置。data恰含：

| 键 | 类型、单位、语义与限制 |
|---|---|
| `value` | scalar [1]，`K`；初始温度T0>0 |

## 输出

每个下列quantity至少一次，可重复请求；逻辑名及array key自由，不得修改quantity、单位、location或分量。输出均float64、point、引用observe，不含sampling。形状及components按上文规则；各输出是相应时刻与对象的瞬时状态，不是时间平均或积分。

| quantity | 类型、单位和含义 | 完整位置 |
|---|---|---|
| `concentration` | components [s]，`mol/m3`；各容器内体积摩尔浓度c_i(t) | `vessels` |
| `temperature` | scalar [1]，`K`；绝热能量守恒确定的温度T(t) | `vessels` |
| `pressure` | scalar [1]，`Pa`；绝对压力p=RTΣ_i c_i | `vessels` |

结果HDF5只含输出array及必需IDs／时间轴，严格复制输入身份和顺序；不导出输入场、坐标或额外数组。恰好t=0的浓度和温度取初态，压力按本题公式由初态计算。

## 接收限制与组合

reactions对象数恰为reaction_count；反应矩阵每个实体行是一条反应，每个分量是组分i，非转置矩阵。每行α和β均非零且不相等；α行和1..4、β行和1..8。质量声明检查每反应要求abs(Σ_i(β−α)M_i)≤1e−12·Σ_i(β+α)M_i，生产数据保证真实质量守恒；不投影／修正原计量或质量。归一化活度是无量纲c_i/c*，前因子单位固定mol/(m3.s)，不能直接当成传统k使用。每个反应器初始Σc_i>0、250≤T0≤5000K；全过程温度界限及气体模型适用性由数据建设独立验证，声明检查不以仅初温合法证明全过程适用。

对象数量及参数范围见上表，输入与输出场各至多2000000数值分量。除显式声明检查外，正式数据还须独立核验材料模型适用、连续问题适定、所请求观测存在、非负物理解及预算内参考精度；排除任意病态尺度和无限刚性组合。声明校验不证明物理／数值准确性。无正式样例时不从目录名、来源软件或文件顺序推导任何额外条件。
