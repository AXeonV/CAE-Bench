# competitive-adsorption 数据契约

入口problem.json及data_file引用的扁平HDF5，路径相对清单；顶层采用CONTRACT通用结构。physics恰含model、parameters，model=`species-competitive-adsorption-v1`；task可省略，出现须为`competitive-adsorption`。禁止profile、contract_version、analysis、materials混用。不接受未列字段、位置、条件或参数组合。

## 物理与支持范围

各容器封闭、等温、固定液体体积且完全混合，互不连接；固体均匀悬浮，公共单层位点竞争吸附，无溶剂吸附与吸附热。dq_i/dt=ka_i c_i(qmax−Σ_j q_j)−kd_i q_i，dc_i/dt=−ρb dq_i/dt。q为每kg固体的摩尔数，c为每m³液体的摩尔数；每个组分c_i+ρb q_i守恒。不得把有限速率动力学换成瞬时平衡等温线。

## 全局参数

parameters恰含下表全部项；每项只有value、unit，数值有限、布尔不是数值、integer必须JSON整数；全部参数无缺省。

| 参数 | 单位 | 含义及值域 |
|---|---|---|
| `species_count` | `1` | 组分数s，JSON整数1..8 |
| `capacity` | `mol/kg` | 公共位点容量qmax>0，每个吸附分子占一个位点 |
| `solid_loading` | `kg/m3` | 单位液体体积的固体质量ρb>0 |

## 几何、位置和身份

spatial_dimension=1；meshes、geometries均为空。entities表示实际混合容器、反应或参数对象，无虚构坐标；空间维度1仅为此有限维模型的存储标记，不引入空间方程。IDs按CONTRACT非负、严格递增，实体行与字段N轴对应，ID不能作数组下标。

| location | kind及数量 | 完整语义 |
|---|---|---|
| `system` | entities，1..1项 | 唯一材料／动力学参数对象，不是空间探针 |
| `vessels` | entities，1..32项 | 独立完全混合有限容积反应器／容器，IDs可不连续，各组分轴按c1..cs |

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
### `sites`

role=`material`，variable=`sites`，operator=`sites`，location=`system`；时间轴`initial`，完整覆盖该位置。data恰含：

| 键 | 类型、单位、语义与限制 |
|---|---|
| `adsorption` | components [s]，`m3/(mol.s)`；吸附速率ka_i≥0 |
| `desorption` | components [s]，`1/s`；解吸速率kd_i≥0 |
### `initial_loading`

role=`initial`，variable=`loading`，operator=`initial_loading`，location=`vessels`；时间轴`initial`，完整覆盖该位置。data恰含：

| 键 | 类型、单位、语义与限制 |
|---|---|
| `value` | components [s]，`mol/kg`；初始固相负载q_i≥0，逐位置Σq_i≤qmax |

## 输出

每个下列quantity至少一次，可重复请求；逻辑名及array key自由，不得修改quantity、单位、location或分量。输出均float64、point、引用observe，不含sampling。形状及components按上文规则；各输出是相应时刻与对象的瞬时状态，不是时间平均或积分。

| quantity | 类型、单位和含义 | 完整位置 |
|---|---|---|
| `concentration` | components [s]，`mol/m3`；各容器内体积摩尔浓度c_i(t) | `vessels` |
| `loading` | components [s]，`mol/kg`；单位固体质量的吸附量q_i(t)，不乘固液比 | `vessels` |

结果HDF5只含输出array及必需IDs／时间轴，严格复制输入身份和顺序；不导出输入场、坐标或额外数组。恰好t=0的浓度／负载取对应初态。

## 接收限制与组合

初始每个位置Σq_i≤qmax，且q_i≥0；ka、kd均允许为0，不额外假设已达平衡。

对象数量及参数范围见上表，输入与输出场各至多2000000数值分量。除显式声明检查外，正式数据还须独立核验材料模型适用、连续问题适定、所请求观测存在、非负物理解及预算内参考精度；排除任意病态尺度和无限刚性组合。声明校验不证明物理／数值准确性。无正式样例时不从目录名、来源软件或文件顺序推导任何额外条件。
