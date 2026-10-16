# coil-circuit 数据契约

入口problem.json和data_file引用的扁平HDF5，路径相对清单。physics恰为model、parameters；model=`electromagnetic-coil-circuit-v1`，task可省略，出现须为`coil-circuit`。禁止profile、contract_version、analysis或materials混用；不能以题号补物理。

## 物理定义

二维xy、z平移不变，e^(+iωt)相量，线性ν>0、σ≥0。B=(∂yAz,−∂xAz)，−div(ν∇Az)+iωσAz=wI，Jind,z=−iωσAz，纵向标势梯度固定0。给定有符号绕组密度w；绕组为独立理想绞线激励，不把wI再算成块体σ中的电流。真实轴长ℓ给λ=ℓ∫ΩwAz dS，电路满足(R+iωL+1/(iωC))I+iωλ=Vs。L只含外部串联电感，不重复场磁链。正向绕组、I、λ、Vs按上述能量共轭符号，场与电路双向反馈。Dirichlet给绝对Az，其余ν∂nAz=0，内部Az及ν∂nAz连续；至少一条Dirichlet。电路只有一个线圈及给定串联RLC，不要求提取绕组几何、端部场或电路拓扑。二维所有面积积分按单位z长度解释；没有隐含厚度，coil-circuit中明确的ℓ只用于总磁链和电路。

## 全局参数

parameters恰含下表项，每项只有value和unit；有限实数，布尔不能作数值，整数须JSON整数。空表表示parameters={}。

| 参数 | 单位 | 含义与范围 |
|---|---|---|
| `frequency` | `Hz` | f>0，ω=2πf |
| `length` | `m` | 真实轴向长度ℓ>0 |
| `resistance` | `Ohm` | 串联电阻R>0 |
| `inductance` | `H` | 外部串联电感L>0，不含所求场磁链 |
| `capacitance` | `F` | 串联电容C>0 |

## 几何和身份

meshes恰含main；MSH4.1 ASCII，坐标m，spatial_dimension=2。main只含非退化一阶三角形type2及全部外边界线type1，全部节点z=0。无未用节点、悬挂节点、重叠体、自交或非流形公共面；域通过完整公共边／面连通；每个外面导出一次，不导出更低维单元。domain恰为main全部节点，cells恰为全部体单元；其他location仅main节点、体单元或外边界元素的非空子集。tag为身份不是行号，Physical Group若声明必须与IDs精确相符，组名不定义物理。禁止points或aggregate。另有coil唯一entities对象，恰一个非负ID，无坐标；只用于电路源及输出，其他entities禁止。节点边界取所有顶点均属于该节点集的全部完整外面，节点集须恰等于这些面的顶点并。Dirichlet至少一条，各节点边界的节点集互不相交；所有边界作用面不得重叠。已声明边界与其余默认自然边界共享端点时按弱解解释，数据须保证所需观测存在。

## 时间、数组与重建

time_axes仅含键harmonic，其引用的float64[1]数组恰为[0.0]，所有字段和输出引用该轴。0仅为相量存储标记。

条件data引用fields逻辑名，其array才是HDF5 key，两者名称自由。fields恰为全部实际引用项；quantity等于data键名，value例外等于条件variable。字段须与条件同location。数组[T,N,*component_shape]不省略轴；scalar=[1]、components=["value"]；复标量components [2]依次实虚，复向量components [2,2]按x/y各自实虚，组件标签按shape行优先展平c1..cL，不使用复数dtype、幅相或RMS。所有数值float64。scalar数据可用同单位有限数值value/unit常量或field；components必须field，不允许内联数组。输入value_kind节点为point、单元为average；节点sampling.space=piecewise_linear，为一阶网格上的唯一P1重建，元素为piecewise_constant，元素值即该元素常值。coil实体为point、space=uniform。sampling必须显式，extrapolation=forbid，时间单帧constant。只作上述空间／实体重建，无额外时间演化。无本题未列数据、选项、模型或隐藏默认值。

## 条件全集

### `material`

role=`material`，variable=`electromagnetic`，operator=`material`；location为cells完整体域，恰一条。必须出现。data恰含以下全部键：

| 键 | 类型、单位、含义 |
|---|---|
| `reluctivity` | scalar [1]，m/H；磁阻率ν=1/μ>0；严格正 |
| `conductivity` | scalar [1]，S/m；电导率σ≥0；非负 |

### `dirichlet`

role=`boundary`，variable=`vector_potential`，operator=`dirichlet`；location为上述闭包规则的外边界节点集，可多条。必须出现。data恰含以下全部键：

| 键 | 类型、单位、含义 |
|---|---|
| `value` | components [2]，Wb/m；给定Az |

### `winding`

role=`source`，variable=`winding_density`，operator=`winding`；location为cells完整体域，恰一条。必须出现。data恰含以下全部键：

| 键 | 类型、单位、含义 |
|---|---|
| `value` | scalar [1]，1/m2；有符号绕组密度w，可正负且不恒零 |

### `voltage_drive`

role=`source`，variable=`voltage`，operator=`voltage_drive`；location为coil唯一实体，恰一条。必须出现。data恰含以下全部键：

| 键 | 类型、单位、含义 |
|---|---|
| `value` | components [2]，V；外加串联电压Vs |

## 输出

逻辑名与array key自由，每个quantity至少出现一次，可重复请求；全部float64，无sampling，时间轴为harmonic，shape及components遵守前述规则。

| quantity | 类型、单位与含义 | 位置与value_kind |
|---|---|---|
| `coil_current` | components [2]，A；未知线圈正向电流I | coil唯一实体，point |
| `flux_linkage` | components [2]，Wb；线圈磁链λ | coil唯一实体，point |
| `vector_potential` | components [2]，Wb/m；Az | cells或非空体单元子集，average |
| `magnetic_flux_density` | components [2, 2]，T；B | cells或非空体单元子集，average |
| `induced_current` | components [2]，A/m2；Jind,z=−iωσAz | cells或非空体单元子集，average |

体单元按实际三角面积积分再除体积／面积，不得把点值当作积分平均；在所用场表示下与积分严格等价的重心值、节点均值或求积公式允许使用。结果仅含输出array及所需IDs／时间轴，严格复制输入身份与行序，不导出输入场、坐标或新网格。

## 接收限制

至多5000三角形、6000节点。唯一时间轴含1帧，输入场和输出场各至多4000000数值分量。正式数据须独立核验几何与材料适用、源及边界条件相容、正则／唯一响应、观测存在和预算内精度；校验器不证明这些性质。结构合法不代表电磁结果正确。
