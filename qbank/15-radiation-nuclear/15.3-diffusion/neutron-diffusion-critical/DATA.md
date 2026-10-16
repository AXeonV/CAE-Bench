# neutron-diffusion-critical 数据契约

problem.json及data_file引用的扁平HDF5遵循通用CONTRACT，路径相对清单目录。physics恰含model、parameters；model=`radiation-neutron-diffusion-critical-v1`。task可省略，若出现只能为`neutron-diffusion-critical`；模型不由目录或ID推断。禁止profile、contract_version、analysis、materials混用。

## 物理定义

无限横向分层平板的一维多群裂变扩散：−∂x(D_g∂xφ_g)+(Σa_g+Σ_h S[h,g])φ_g−Σ_h S[g,h]φ_h=χ_g Σ_h(νΣf_h φ_h)/k。Σa包含裂变吸收，不再重复裂变损失；νΣf为生产截面。无外源，每层χ按存储值使用。各界面φ及−D∂xφ连续，两端真实x=0,H处φ=0，无外推边界。求正基模及其主正本征值k_eff；不选高阶变号模态，不取任意接近1的本征值。以Σ_g∫_0^H φ_g dx=1/(m.s)归一化，φ单位仍为1/(m2.s)，并取全域内部正号；这只是唯一幅度约定，不代表物理堆功率。生产截面、吸收、扩散及χ各群严格为正，以确保耦合的基模目标，不要求求瞬态或临界控制调节。

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
| `production` | components ['g']；`1/m`；各群νΣf_g>0，已含平均产额；吸收已含裂变损失，不再加一次Σf |
| `spectrum` | components ['g']；`1`；裂变谱χ_g>0，每层群和与1之差≤1e−12；按存储值计算，不再归一化 |

## 输出

每个quantity至少出现一次，可重复请求，outputs逻辑名与array key自由；同quantity的单位、位置、shape均按表，float64、value_kind=point、时间轴=static、无sampling。各输出按下表定义，不另作时间或空间平均。

| quantity | 类型、单位与含义 | location |
|---|---|---|
| `scalar_flux` | components ['g']；`1/(m2.s)`；各群标量通量φ_g，按题定积分归一化 | `probes` |
| `multiplication_factor` | scalar [1]；`1`；主正本征值k_eff | `system` |

结果仅含要求的输出array及其输入IDs／时间轴的精确副本，不导出坐标、输入场或额外数组。

## 接收限制

各表规模为公开上限；输入场总分量与输出场总分量分别不超过2000000。所有输入／输出浮点值有限。正式数据须独立验证模型适用、观测存在、参考收敛及同预算可达性，正式数据接收须有预算内达到公开精度的独立数值证据；这不是由结构检查自动证明的事实，不能由参数正值代替数值证据。
