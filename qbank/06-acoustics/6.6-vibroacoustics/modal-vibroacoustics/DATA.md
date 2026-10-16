# modal-vibroacoustics 数据契约

入口problem.json及其data_file引用的扁平HDF5，路径相对清单。physics恰含model、parameters；model固定`acoustic-modal-vibroacoustics-v1`，task可省略，出现须为`modal-vibroacoustics`。禁止contract_version、profile、analysis、materials混用；不接受本题未列字段、模型或条件组合。

## 物理定义

相量约定为真实扰动Re(A exp(+iωt))，ω=2πf>0。声压是相对背景的扰动，不是总绝对压力；单频输入和输出均为复振幅，不是RMS或仅模长。有界静止非均匀无黏介质，体积模量K=ρc²。iωP/K+div U=q，iωρU+∇P=0。材料参数逐四面体常数；共享节点的内部面压力连续、法向速度连续。未声明外面U·n=0，n是流体域向外法向；没有额外压力基准或切向无滑移条件。唯一给定模态结构有m个长度坐标η、实质量M／阻尼C／刚度K_s，M与K_s正定、C半正定。modal_wall上Un=iωΣj φjηj，φ为实值面片常数，正向沿流体外法向。(−ω²M+iωC+K_s)η=Fext+∫wall φ P dS；模态声压力以正声压推动向外为正，与边界速度同一方向。所有modal_wall记录共同耦合同一个structure实体，积分是其并集的实际面积积分。m个形状在该并集上独立，不重排／重新归一化模态、不重复叠加附加质量。给定降阶模型不含模态提取、应力恢复或更新几何；数据排除未消除的耦合物理共振。

## 全局参数

parameters恰为下表全部项，各项只有value和unit，有限实数且布尔值不能作数值，整数须JSON整数。

| 参数 | 单位 | 含义及值域 |
|---|---|---|
| `frequency` | `Hz` | 单频f>0，ω=2πf |
| `mode_count` | `1` | 模态数m，整数1..8 |

## 几何、位置与身份

meshes恰含main，MSH4.1 ASCII；可选geometries只保留来源，求解几何以网格为准。spatial_dimension=3，坐标为m。tag是身份不是行号，Physical Group若声明必须与location的IDs精确相符；组名不定义边界。main只含非退化一阶四面体type4及全部外边界一阶三角形type2，不导出更低维单元。无未用节点、悬挂节点、重叠体或非流形公共面；每个外面导出一次，域通过完整公共面连通。保留domain为全部所用节点、cells为全部体单元；其他mesh位置只允许main节点子集、体单元子集或外面单元子集。场的实体身份固定在参考几何上，内部升阶／改网格自由。外法向n从唯一相邻体指向域外，不由面节点存储顺序推断。压力边界用节点集，精确作用于全部顶点均在该集的所有完整外面；节点集须恰为这些作用面顶点之并，不允许孤立点／棱约束。多条压力记录不得共享节点。其他边界按实际面IDs给定，任何完整外面至多一种边界，不能依列表顺序覆盖；不同类别仅可在棱相交。额外允许且必须有structure location，kind=entities、单个非负ID；它表示唯一模态结构，不是空间点或假区域聚合。

## 时间、分量与输入重建

time_axes恰为harmonic单帧[0.0]；全部输入和输出只引用harmonic。0是相量存储标记，不是物理初态、相位未知量或额外频率轴；每例只有parameters.frequency这一物理频率。所有输入sampling.time=constant，不接受物理历史或输出多帧。

fields恰为被条件引用的字段；条件field引用逻辑对象名，该对象的array才是HDF5 key，两者名称自由。输入quantity固定等于data键名；唯一例外是value，其quantity等于该条条件variable（下表明确）。field须与条件同location，不能按相同长度借别处数据。所有field为float64，数组[T,N,*component_shape]，不省略轴。scalar固定shape=[1]、components=["value"]；vector固定[3]及x/y/z。components按表shape行优先展平命名c1..cL（L为shape各维乘积）。复标量[2]依次实、虚，复向量[3,2]为x实虚、y实虚、z实虚；不使用复数dtype或幅相数组。m取mode_count；模态矩阵[m,m]按输入模态顺序行优先，模态复量[m,2]每模态实虚相邻，shape[m]是m个实值形状系数。输入field显式sampling，extrapolation=forbid；节点space=piecewise_linear，表示沿一阶参考网格的唯一P1重建（边界节点在对应面上重建）；单元space=piecewise_constant，为每个实体常值；entities的space=uniform，为离散模态参数，不作空间重建。value_kind节点／entities为point、元素为average，不接受输入integral。sampling.time固定constant；只作上述空间重建，不定义额外时间演化。scalar data可以用同单位有限数值的value/unit常量（全位置、全程常量），或显式field；components／vector仅field，不允许内联数组。表中static只允许常量或静态轴field。位置引用和option只能按表精确形式。所有数据无布尔数值、隐藏默认值或未列选项。

## 条件全集

### `material`

role=`material`，variable=`acoustic`，operator=`material`；location为cells完整体域。必须出现。该算子恰一条覆盖表定完整位置。data恰含下列全部键：

| data键 | 类型、单位和含义 |
|---|---|
| `density` | scalar [1]；`kg/m3`；背景密度ρ>0；static |
| `sound_speed` | scalar [1]；`m/s`；声速c>0；static |

### `volume_source`

role=`source`，variable=`dilatation`，operator=`volume_source`；location为cells完整体域。必须出现。该算子恰一条覆盖表定完整位置。data恰含下列全部键：

| data键 | 类型、单位和含义 |
|---|---|
| `value` | components [2]；`1/s`；体积膨胀率源q |

### `pressure`

role=`boundary`，variable=`pressure`，operator=`pressure`；location为上述闭包规则的外边界节点location。可不出现。可多条，作用面不能重复。data恰含下列全部键：

| data键 | 类型、单位和含义 |
|---|---|
| `value` | components [2]；`Pa`；给定声压Pb |

### `normal_velocity`

role=`boundary`，variable=`normal_velocity`，operator=`normal_velocity`；location为外边界三角单元location。可不出现。可多条，作用面不能重复。data恰含下列全部键：

| data键 | 类型、单位和含义 |
|---|---|
| `value` | components [2]；`m/s`；向域外的法向粒子速度 |

### `impedance`

role=`boundary`，variable=`normal_velocity`，operator=`impedance`；location为外边界三角单元location。可不出现。可多条，作用面不能重复。data恰含下列全部键：

| data键 | 类型、单位和含义 |
|---|---|
| `impedance` | components [2]；`Pa.s/m`；复阻抗Z，ReZ≥0且|Z|>0 |
| `drive` | components [2]；`Pa`；压力驱动Pd |

### `structure`

role=`material`，variable=`structure`，operator=`structure`；location为structure唯一实体。必须出现。该算子恰一条覆盖表定完整位置。data恰含下列全部键：

| data键 | 类型、单位和含义 |
|---|---|
| `mass` | components ['m', 'm']；`kg`；对称正定模态质量M |
| `damping` | components ['m', 'm']；`kg/s`；对称半正定模态阻尼C |
| `stiffness` | components ['m', 'm']；`N/m`；对称正定模态刚度K |
| `force` | components ['m', 2]；`N`；外部模态力Fext；每模态实虚相邻 |

### `modal_wall`

role=`boundary`，variable=`normal_velocity`，operator=`modal_wall`；location为外边界三角单元location。必须出现。可多条，作用面不能重复。data恰含下列全部键：

| data键 | 类型、单位和含义 |
|---|---|
| `shape` | components ['m']；`1`；实值法向位移形状φ，各面分片常数；正值沿流体外法向 |

pressure算子规定P=Pb，normal_velocity规定U·n等于value；impedance规定P=Z U·n+drive。单频Z满足ReZ≥0且|Z|>0。驱动正负和法向均按向流体外。未声明外面法向速度0，不叠加切向速度或额外压力条件。

## 输出

outputs逻辑名与array key自由；每个quantity至少一次，可重复请求。全部float64、不含sampling、时间轴为harmonic，dtype／shape／components与单位按表及前述分量规则。

| quantity | 类型、单位及定义 | 支持位置、value_kind |
|---|---|---|
| `modal_displacement` | components ['m', 2]；`m`；模态位移η的复振幅，按输入模态顺序 | structure唯一实体，point |
| `pressure` | components [2]；`Pa`；复声压P | cells或其非空体单元子集，average |
| `velocity` | components [3, 2]；`m/s`；复粒子速度U | cells或其非空体单元子集，average |

体单元平均按实际体积积分再除体积，不是中心值或节点算术均值。结果HDF5仅含输出array、所需IDs及时间轴，严格复制输入身份与行序；不导出输入场、坐标或新网格。

## 接收条件与限制

至多3000四面体、9000节点。每轴至多101帧，全部输入／输出场各至多3000000数值分量。正式数据须核验几何无自交／重叠、材料适用、小扰动线性范围、初边值相容、所请求点值／平均存在及物理解可确定，并用独立参考证明预算内精度；校验器不证明这些性质。不得以格式合法、求解器低残差或与同一离散一致替代声学正确性。
