# resonator-wall 数据契约

入口problem.json及其data_file引用的扁平HDF5，路径相对清单。physics恰含model、parameters；model固定`acoustic-resonator-wall-v1`，task可省略，出现须为`resonator-wall`。禁止contract_version、profile、analysis、materials混用；不接受本题未列字段、模型或条件组合。

## 物理定义

有界静止非均匀线性介质，K=ρc²。∂tp/K+div u=q，ρ∂tu+∇p=0。材料参数逐四面体常数；共享节点的内部面压力连续、法向速度连续。给定物理p、u初态；不作额外声／涡投影，初速度中无源静态分量也保留。未声明外面u·n=0，n是流体域向外法向；不额外固定切向速度或每帧减去平均压力。resonator表面有局部反应壁：u·n=∂tξ，ms∂ttξ+rs∂tξ+ksξ=p−pb。ξ向流体域外为正，ms为单位面积质量、rs为局部阻尼、ks为单位面积位移刚度，pb为背压扰动；压力正值推动壁向外。初始ξ、∂tξ显式给出并与声学初态相容。每个表面点独立局部振子，没有沿面弹性耦合；即使参数和初态按面常值给定，后续ξ也由局部压力迹决定，不强制每面刚性均动。保持壁储能与声场双向反馈，不以无记忆常阻抗替代。

## 全局参数

parameters恰为下表全部项，各项只有value和unit，有限实数且布尔值不能作数值，整数须JSON整数。

| 参数 | 单位 | 含义及值域 |
|---|---|---|
| `start_time` | `s` | 物理初始时刻t0 |
| `end_time` | `s` | 末时刻tf，严格大于t0 |

## 几何、位置与身份

meshes恰含main，MSH4.1 ASCII；可选geometries只保留来源，求解几何以网格为准。spatial_dimension=3，坐标为m。tag是身份不是行号，Physical Group若声明必须与location的IDs精确相符；组名不定义边界。main只含非退化一阶四面体type4及全部外边界一阶三角形type2，不导出更低维单元。无未用节点、悬挂节点、重叠体或非流形公共面；每个外面导出一次，域通过完整公共面连通。保留domain为全部所用节点、cells为全部体单元；其他mesh位置只允许main节点子集、体单元子集或外面单元子集。场的实体身份固定在参考几何上，内部升阶／改网格自由。外法向n从唯一相邻体指向域外，不由面节点存储顺序推断。压力边界用节点集，精确作用于全部顶点均在该集的所有完整外面；节点集须恰为这些作用面顶点之并，不允许孤立点／棱约束。多条压力记录不得共享节点。其他边界按实际面IDs给定，任何完整外面至多一种边界，不能依列表顺序覆盖；不同类别仅可在棱相交。不允许points、entities或aggregate位置。

## 时间、分量与输入重建

time_axes必须含initial单帧[t0]及response非空请求时刻，response全部在[t0,tf]内；每个轴至多101帧。材料、初态及各参数注明static的field只引用initial。其他加载单帧须在t0，表示整个[t0,tf]常量；多帧须首末恰为t0、tf，逐分量连续分段线性插值，sampling.time=linear；不外推。不允许initial、response之外未被加载引用的轴；输出时刻不是内部求解步，不能跳过未请求的历史。所有初边值在t0相容，初态不代表数值初猜。

fields恰为被条件引用的字段；条件field引用逻辑对象名，该对象的array才是HDF5 key，两者名称自由。输入quantity固定等于data键名；唯一例外是value，其quantity等于该条条件variable（下表明确）。field须与条件同location，不能按相同长度借别处数据。所有field为float64，数组[T,N,*component_shape]，不省略轴。scalar固定shape=[1]、components=["value"]；vector固定[3]及x/y/z。输入field显式sampling，extrapolation=forbid；节点space=piecewise_linear，表示沿一阶参考网格的唯一P1重建（边界节点在对应面上重建）；单元space=piecewise_constant，为每个实体常值。value_kind节点为point、元素为average，不接受输入integral。单帧或static的sampling.time=constant，加载多帧按时间段线性；先空间再时间重建。scalar data可以用同单位有限数值的value/unit常量（全位置、全程常量），或显式field；components／vector仅field，不允许内联数组。表中static只允许常量或静态轴field。位置引用和option只能按表精确形式。所有数据无布尔数值、隐藏默认值或未列选项。

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
| `value` | scalar [1]；`1/s`；体积膨胀率源q |

### `initial_pressure`

role=`initial`，variable=`pressure`，operator=`initial_pressure`；location为domain全部节点。必须出现。该算子恰一条覆盖表定完整位置。data恰含下列全部键：

| data键 | 类型、单位和含义 |
|---|---|
| `value` | scalar [1]；`Pa`；初始声压p0；static |

### `initial_velocity`

role=`initial`，variable=`velocity`，operator=`initial_velocity`；location为domain全部节点。必须出现。该算子恰一条覆盖表定完整位置。data恰含下列全部键：

| data键 | 类型、单位和含义 |
|---|---|
| `value` | vector [3]；`m/s`；初始粒子速度u0；static |

### `pressure`

role=`boundary`，variable=`pressure`，operator=`pressure`；location为上述闭包规则的外边界节点location。可不出现。可多条，作用面不能重复。data恰含下列全部键：

| data键 | 类型、单位和含义 |
|---|---|
| `value` | scalar [1]；`Pa`；给定声压pb |

### `normal_velocity`

role=`boundary`，variable=`normal_velocity`，operator=`normal_velocity`；location为外边界三角单元location。可不出现。可多条，作用面不能重复。data恰含下列全部键：

| data键 | 类型、单位和含义 |
|---|---|
| `value` | scalar [1]；`m/s`；向域外的法向粒子速度 |

### `impedance`

role=`boundary`，variable=`normal_velocity`，operator=`impedance`；location为外边界三角单元location。可不出现。可多条，作用面不能重复。data恰含下列全部键：

| data键 | 类型、单位和含义 |
|---|---|
| `impedance` | scalar [1]；`Pa.s/m`；实阻抗R>0；static |
| `drive` | scalar [1]；`Pa`；压力驱动pd |

### `resonator`

role=`boundary`，variable=`normal_velocity`，operator=`resonator`；location为外边界三角单元location。必须出现。可多条，作用面不能重复。data恰含下列全部键：

| data键 | 类型、单位和含义 |
|---|---|
| `mass` | scalar [1]；`kg/m2`；壁面面密度ms>0；static |
| `damping` | scalar [1]；`Pa.s/m`；壁面阻尼rs≥0；static |
| `stiffness` | scalar [1]；`Pa/m`；壁面刚度ks>0；static |
| `displacement0` | scalar [1]；`m`；初始向外位移ξ0；static |
| `velocity0` | scalar [1]；`m/s`；初始向外速度w0；static |
| `back_pressure` | scalar [1]；`Pa`；壁背压力扰动pb(t) |

pressure算子规定p=pb，normal_velocity规定u·n等于value；impedance规定p=R u·n+drive。瞬态R为严格正的实常参数，可逐面变化；驱动正负和法向均按向流体外。未声明外面法向速度0，不叠加切向速度或额外压力条件。

## 输出

outputs逻辑名与array key自由；每个quantity至少一次，可重复请求。全部float64、不含sampling、时间轴为response，dtype／shape／components与单位按表及前述分量规则。

| quantity | 类型、单位及定义 | 支持位置、value_kind |
|---|---|---|
| `wall_displacement` | scalar [1]；`m`；向外壁位移ξ | 每条resonator完整面location，average；每条均需请求 |
| `wall_velocity` | scalar [1]；`m/s`；向外壁速度∂tξ | 每条resonator完整面location，average；每条均需请求 |
| `pressure` | scalar [1]；`Pa`；声压p | cells或其非空体单元子集，average |
| `velocity` | vector [3]；`m/s`；粒子速度u | cells或其非空体单元子集，average |

体单元平均按实际体积积分再除体积；壁面平均按实际三角面积积分再除面积，不是中心值或节点算术均值。结果HDF5仅含输出array、所需IDs及时间轴，严格复制输入身份与行序；不导出输入场、坐标或新网格。

## 接收条件与限制

至多3000四面体、9000节点。每轴至多101帧，全部输入／输出场各至多3000000数值分量。正式数据须核验几何无自交／重叠、材料适用、小扰动线性范围、初边值相容、所请求点值／平均存在及物理解可确定，并用独立参考证明预算内精度；校验器不证明这些性质。不得以格式合法、求解器低残差或与同一离散一致替代声学正确性。
