# partition-transfer 数据契约

入口problem.json及data_file引用的扁平HDF5，路径相对清单；顶层采用CONTRACT通用结构。physics恰含model、parameters，model=`species-partition-transfer-v1`；task可省略，出现须为`partition-transfer`。禁止profile、contract_version、analysis、materials混用。不接受未列字段、位置、条件或参数组合。

## 物理与支持范围

多个封闭、等温、固定体积的完全混合相容器，通过任意有限传质网络交换同一组分，无反应或体积流动。连接e由a指向b，N_ei=G_ei(c_ai−c_bi/K_ei)，单位mol/s；V_a dc_ai/dt为入向连接N之和减去出向连接N之和。K是平衡时c_b/c_a，不是分配质量分数。N可负，反向净流不截零；隔离容器与平行连接均允许，各连接独立计入，同一容器不能自连。初态给定后网络库存Σ_a V_a c_ai守恒，不强制所有连接瞬间达平衡。

## 全局参数

parameters恰含下表全部项；每项只有value、unit，数值有限、布尔不是数值、integer必须JSON整数；全部参数无缺省。

| 参数 | 单位 | 含义及值域 |
|---|---|---|
| `species_count` | `1` | 组分数s，JSON整数1..8 |

## 几何、位置和身份

spatial_dimension=1；meshes、geometries均为空。entities表示实际混合容器、反应或参数对象，无虚构坐标；空间维度1仅为此有限维模型的存储标记，不引入空间方程。IDs按CONTRACT非负、严格递增，实体行与字段N轴对应，ID不能作数组下标。

| location | kind及数量 | 完整语义 |
|---|---|---|
| `vessels` | entities，1..32项 | 独立完全混合有限容积反应器／容器，IDs可不连续，各组分轴按c1..cs |
| `links` | entities，1..64项 | 有向传质连接；方向只定义流率符号，不禁止逆向净交换 |

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
### `volumes`

role=`material`，variable=`volume`，operator=`volumes`，location=`vessels`；时间轴`initial`，完整覆盖该位置。data恰含：

| 键 | 类型、单位、语义与限制 |
|---|---|
| `value` | scalar [1]，`m3`；各容器固定体积V_a>0 |
### `links`

role=`material`，variable=`transfer_link`，operator=`links`，location=`links`；时间轴`initial`，完整覆盖该位置。data恰含：

| 键 | 类型、单位、语义与限制 |
|---|---|
| `origin` | scalar [1]，`1`；起点容器的实际ID，不是数组行号 |
| `destination` | scalar [1]，`1`；终点容器实际ID，须不同于起点 |
| `partition` | components [s]，`1`；平衡分配比K_i=c_destination/c_origin>0 |
| `conductance` | components [s]，`m3/s`；组分传质导通率G_i≥0 |

## 输出

每个下列quantity至少一次，可重复请求；逻辑名及array key自由，不得修改quantity、单位、location或分量。输出均float64、point、引用observe，不含sampling。形状及components按上文规则；各输出是相应时刻与对象的瞬时状态，不是时间平均或积分。

| quantity | 类型、单位和含义 | 完整位置 |
|---|---|---|
| `concentration` | components [s]，`mol/m3`；各容器内体积摩尔浓度c_i(t) | `vessels` |
| `molar_flow` | components [s]，`mol/s`；各连接从origin流向destination的有符号净摩尔率 | `links` |

结果HDF5只含输出array及必需IDs／时间轴，严格复制输入身份和顺序；不导出输入场、坐标或额外数组。恰好t=0的浓度取初态，摩尔流率按本题公式由初态计算。

## 接收限制与组合

links端点字段为float64但值须精确整数且≤2^53−1，引用实际vessels ID；vessels ID同样≤2^53−1。端点不能自连；允许非连续ID、平行连接和隔离容器。初态、V和所有边参数均按本表身份关联，不按ID大小推测相类型。

对象数量及参数范围见上表，输入与输出场各至多2000000数值分量。除显式声明检查外，正式数据还须独立核验材料模型适用、连续问题适定、所请求观测存在、非负物理解及预算内参考精度；排除任意病态尺度和无限刚性组合。声明校验不证明物理／数值准确性。无正式样例时不从目录名、来源软件或文件顺序推导任何额外条件。
