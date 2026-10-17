# neutron-diffusion-source 数据契约

problem.json及data_file引用的扁平HDF5遵循通用CONTRACT，路径相对清单目录。physics恰含model、parameters；model=`radiation-neutron-diffusion-source-v1`。task可省略，若出现只能为`neutron-diffusion-source`；模型不由目录或ID推断。禁止profile、contract_version、analysis、materials混用。

## 物理定义

无限横向分层平板的一维多群中子扩散，有效D_g独立给定。无裂变，−∂x(D_g∂xφ_g)+(Σa_g+Σ_h S[h,g])φ_g−Σ_h S[g,h]φ_h=q_g，J_g=−D_g∂xφ_g。矩阵第一轴目的群、第二轴来源群，允许自散射，其损失与产生恰抵消。每个界面φ_g和J_g连续；在真实几何边界x=0,H施加φ_g=0，无外推长度、额外入射或反射。这个零Dirichlet扩散模型不冒充角输运真空边界。材料响应和源给定，不作热反馈或核数据拟合。

## 全局参数

physics.parameters恰含下表全部项，每项仅value和unit；数值有限，布尔不能作数值，整数须JSON整数。

| 参数 | 单位 | 定义及范围 |
|---|---|---|
| `group_count` | `1` | 群数G，JSON整数1..4；各群是输入给定有效响应的离散群，无隐含能群宽度权重 |

## 对象与几何

spatial_dimension固定1。meshes和geometries均为空。1表示平板法向全局x轴。locations恰含下表；IDs为int64、非负严格递增，system必须ID=[0]；其余固定ID规则按表。层从x=0按IDs数组行序排列，H为全部width之和，坐标单位m；各层IDs可非连续，不从ID数值推坐标。所有累计界面必须有限且严格递增。probes.coordinates为float64[N,1]；每点x与任一界面的距离须≥1e−10·H且严格在(0,H)。不要求按坐标排序，值始终按IDs对应；无界面迹或边界导数请求。

| location | 定义与数量 |
|---|---|
| `layers` | entities，1..32项；按IDs行序沿+x排列的材料层对象，x=0起始；层内参数常值 |
| `system` | entities，1..1项；完整平板系统对象，ID固定0 |
| `probes` | points，1..128项；真实位置x，严格在层内部，排除全部界面与两端；不作空间重建 |

## 时间与数组

time_axes恰含`static`。static恰为float64[1]的[0.0]，静态参数记录引用static。所有时间单位s，时间数组key自由。未列轴不允许，输出均引用static。

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
| `diffusion` | components ['g']；`m`；各群扩散系数D_g>0，独立给定，不从总截面反推 |

### `source`

conditions中恰一条：role=`source`，variable=`source`，operator=`source`，location=`layers`；完整覆盖该location，使用`static`时间轴。data恰含下列键，无默认值：

| data键 | 类型、单位、含义与范围 |
|---|---|
| `value` | components ['g']；`1/(m3.s)`；层内常量总群体源q_g≥0 |

## 输出

每个quantity至少出现一次，可重复请求，outputs逻辑名与array key自由；同quantity的单位、位置、shape均按表，float64、value_kind=point、时间轴=static、无sampling。各输出按下表定义，不另作时间或空间平均。

| quantity | 类型、单位与含义 | location |
|---|---|---|
| `scalar_flux` | components ['g']；`1/(m2.s)`；各群标量通量φ_g，保持输入激励确定的绝对幅值，不另作归一化 | `probes` |
| `current` | components ['g']；`1/(m2.s)`；各群沿+x的净粒子流J_g，可为负 | `probes` |

结果仅含要求的输出array及其输入IDs／时间轴的精确副本，不导出坐标、输入场或额外数组。

## 接收限制

各表规模为公开上限；输入场总分量与输出场总分量分别不超过2000000。所有输入／输出浮点值有限。输入符合本题物理模型的适用范围，全部请求的观测存在且有限，并可在公开资源预算内达到评分精度。
