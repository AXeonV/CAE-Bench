# rlc-harmonic 数据契约

入口problem.json和data_file引用的扁平HDF5，路径相对清单。physics恰为model、parameters；model=`electromagnetic-rlc-harmonic-v1`，task可省略，出现须为`rlc-harmonic`。禁止profile、contract_version、analysis或materials混用；不能以题号补物理。

## 物理定义

无空间几何的有向集总网络。每个支路tail→head定义正电流I和电压v=Vtail−Vhead，地节点电压恒0。每节点流出电流代数和0，无未声明的节点注入；源也作为支路。R、L、C为严格正常数；电阻v=RI。e^(+iωt)相量，电容I=iωCv，电感v=iωLI；电压源v=value，电流源I=value。无瞬态初态或额外直流偏置。

## 全局参数

parameters恰含下表项，每项只有value和unit；有限实数，布尔不能作数值，整数须JSON整数。空表表示parameters={}。

| 参数 | 单位 | 含义与范围 |
|---|---|---|
| `frequency` | `Hz` | f>0，ω=2πf |
| `ground_node` | `1` | 地节点的真实ID，非负JSON整数，须属于nodes |

## 几何和身份

nodes为全部电路节点entities，2..33个；branches为全部支路entities，1..64个。两组ID各自非负唯一，可数值重合但不是同一对象；ground_node必须属于nodes。所有location只能为这两组之一的非空entities子集；条件支路集合按实际ID形成branches的无遗漏、无重叠划分。tail/head字段须为int64节点真实ID、不同且属于nodes；参数及端点静态。所有节点至少在一个支路上，所有节点通过电阻子图连通（保障参考和耗散），电压源子图无无向环（平行两源也算环）。其他RLC及源可有并联。合法数据须进一步保证约束相容、DAE正则且响应唯一，校验器的图检查不证明这些性质。无空间坐标、mesh、geometry、points或aggregate。geometries和meshes必须为空。spatial_dimension=1只作协议元数据标记，不表示一维空间传输线。

## 时间、数组与重建

time_axes仅含键harmonic，其引用的float64[1]数组恰为[0.0]，所有字段和输出引用该轴。0仅为相量存储标记。

条件data引用fields逻辑名，其array才是HDF5 key，两者名称自由。fields恰为全部实际引用项；quantity等于data键名，value例外等于条件variable。字段须与条件同location。数组[T,N,*component_shape]不省略轴；scalar=[1]、components=["value"]；复标量components [2]依次实虚，组件标签按shape行优先展平c1..cL，不使用复数dtype、幅相或RMS。所有数值float64，唯tail/head为int64。scalar数据可用同单位有限数值value/unit常量或field；tail/head必须field，不能用常量或浮点ID。components必须field，不允许内联数组。输入value_kind entities为point，sampling.space=uniform。sampling必须显式，extrapolation=forbid，时间单帧constant。只作上述空间／实体重建，无额外时间演化。无本题未列数据、选项、模型或隐藏默认值。

## 条件全集

### `resistor`

role=`material`，variable=`branch`，operator=`resistor`；location为branches非空支路子集，可多条，同算子也可分组。必须出现。data恰含以下全部键：

| 键 | 类型、单位、含义 |
|---|---|
| `tail` | scalar [1]，1；正向起点节点ID |
| `head` | scalar [1]，1；正向终点节点ID |
| `resistance` | scalar [1]，Ohm；正元件参数；严格正 |

### `capacitor`

role=`material`，variable=`branch`，operator=`capacitor`；location为branches非空支路子集，可多条，同算子也可分组。可不出现。data恰含以下全部键：

| 键 | 类型、单位、含义 |
|---|---|
| `tail` | scalar [1]，1；正向起点节点ID |
| `head` | scalar [1]，1；正向终点节点ID |
| `capacitance` | scalar [1]，F；正元件参数；严格正 |

### `inductor`

role=`material`，variable=`branch`，operator=`inductor`；location为branches非空支路子集，可多条，同算子也可分组。可不出现。data恰含以下全部键：

| 键 | 类型、单位、含义 |
|---|---|
| `tail` | scalar [1]，1；正向起点节点ID |
| `head` | scalar [1]，1；正向终点节点ID |
| `inductance` | scalar [1]，H；正元件参数；严格正 |

### `voltage_source`

role=`source`，variable=`branch`，operator=`voltage_source`；location为branches非空支路子集，可多条，同算子也可分组。可不出现。data恰含以下全部键：

| 键 | 类型、单位、含义 |
|---|---|
| `tail` | scalar [1]，1；正向起点节点ID |
| `head` | scalar [1]，1；正向终点节点ID |
| `value` | components [2]，V；规定支路源相量 |

### `current_source`

role=`source`，variable=`branch`，operator=`current_source`；location为branches非空支路子集，可多条，同算子也可分组。可不出现。data恰含以下全部键：

| 键 | 类型、单位、含义 |
|---|---|
| `tail` | scalar [1]，1；正向起点节点ID |
| `head` | scalar [1]，1；正向终点节点ID |
| `value` | components [2]，A；规定支路源相量 |

## 输出

逻辑名与array key自由，每个quantity至少出现一次，可重复请求；全部float64，无sampling，时间轴为harmonic，shape及components遵守前述规则。

| quantity | 类型、单位与含义 | 位置与value_kind |
|---|---|---|
| `node_voltage` | components [2]，V；指定方向的复量 | nodes全部节点，point |
| `branch_voltage` | components [2]，V；指定方向的复量 | branches全部支路，point |
| `branch_current` | components [2]，A；指定方向的复量 | branches全部支路，point |

电路量为离散实体值，无空间插值或几何平均。结果仅含输出array及所需IDs／时间轴，严格复制输入身份与行序，不导出输入场、坐标或新网格。

## 接收限制

2..33节点、1..64支路。唯一时间轴含1帧，输入场和输出场各至多4000000数值分量。正式数据须独立核验元件适用、源及边界条件相容、正则／唯一响应、观测存在和预算内精度；校验器不证明这些性质。结构合法不代表电磁结果正确。
