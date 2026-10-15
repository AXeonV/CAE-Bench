# modal-flexible 数据契约

入口为UTF-8 problem.json及其data_file指定的扁平HDF5，路径相对清单解释。考生仅需本题instruction、DATA和通用CONTRACT。`spatial_dimension=2`；`physics`恰含model、parameters，model固定为`multibody-modal-flexible-v1`；task可省略，出现时须为`modal-flexible`。不允许profile、analysis、materials、contract_version。无未列键、条件或隐藏默认值。

## 物理与方法边界

每个system是一套固定参考系下的线性柔性模态模型：Mη̈+Cη̇+Kη=f(t)。η每个分量具有长度单位；M、K对称正定，C对称半正定，允许非对角耦合。它们和初态是输入物理事实，不能重新提取、重排、截断或归一化模态。不同system互不作用；给定的是有限维柔性模型，不要求重建连续应力场或证明模态截断误差。积分及误差控制由考生负责。

## 全局参数

parameters恰为下表全部项，各项为带单位有限标量的value/unit对象，布尔值不能作数值。

| 参数名 | 单位 | 含义及范围 |
|---|---|---|
| `start_time` | `s` | 初始时刻t0 |
| `end_time` | `s` | 终止时刻tf，tf>t0 |
| `mode_count` | `1` | 模态数k，整数；范围[1,12] |

## 位置与身份

`meshes={}`、`geometries={}`。locations全部为CONTRACT的entities，记录恰为kind=entities及ids引用；没有coordinates或伪造网格。每个实体的状态或参数保留自己的ID，物理位置来自输入场及条件参数。实际ID可不连续，不能用数组行号代替ID。保留位置名`systems`，N=1..32。每个ID是一套独立系统。只允许保留位置，不允许其他location；所有ID为非负、严格递增int64。

## 时间和字段

必须有名为`initial`的单帧轴[t0]和名为`response`的输出轴，response全在[t0,tf]内、至多201帧且非空。其他轴仅可用于loads引用的场；这些加载轴单帧时必须为[t0]，表示整个[t0,tf]常量，多帧时首末恰为t0、tf，逐分量连续分段线性插值，不外推。非loads字段均为initial轴单帧常量，不在时间上演化；字段名带0表示真实初态。输出时刻不是内部积分步；不得跳过未请求的中间载荷历史。所有输入field显式sampling：space="uniform"，time在loads多帧时为"linear"、其余"constant"，extrapolation="forbid"。uniform表示每个独立ID自身的离散参数，不在不同ID间作空间重建、平滑或平均。

所有表内字段均float64；kind=scalar固定shape=[1]、components=["value"]；vector使用全局前D分量及["x","y","z"]的前D项；components类型采用表中shape，标签依行优先展平固定为c1,c2,...,cL（L是shape各维乘积）。k取mode_count。所有数组为[T,N,*shape]，保留时间、ID、分量轴。字段对象名和array key均自由，quantity对输入必须恰等于引用它的data键名，单位／kind／shape严格按表。字段必须和条件同location，不允许常量简写替代field，即使均匀亦然。输入fields恰为被条件引用的字段；同一field可复用，但不能靠同shape跨ID错配。

## 条件全集

### `modal_system`

role=`material`、variable=`system`、operator=`modal_system`；location=`systems`，恰一条记录覆盖该位置全部IDs。必须出现。 data恰含下列全部键：

| data键 | 表示及含义 |
|---|---|
| `mass_matrix` | field引用；components [k,k]；kg；对称正定模态质量M |
| `stiffness` | field引用；components [k,k]；N/m；对称正定模态刚度K |
| `damping` | field引用；components [k,k]；kg/s；对称半正定模态阻尼C |
| `eta0` | field引用；components [k]；m；初始模态位移η0 |
| `eta_dot0` | field引用；components [k]；m/s；初始模态速度 |


### `loads`

role=`source`、variable=`load`、operator=`loads`；location=`systems`，恰一条记录覆盖该位置全部IDs。必须出现。 data恰含下列全部键：

| data键 | 表示及含义 |
|---|---|
| `modal_force` | field引用；components [k]；N；各模态广义力f(t) |


modal_system及loads均恰一条覆盖systems，不允许按子集拆分。未列出的算子一律不允许；字段正值要求见表；矩阵对称／正定含义按物理部分。常量参数不能使用field替代。

## 输出

outputs逻辑名及array key自由；每个quantity必须出现，允许重复请求但每次须覆盖对应完整位置。输出轴恰为response；均float64、value_kind=point，不含sampling。

| quantity | 分量、单位与含义 | 位置 |
|---|---|---|
| `modal_displacement` | components [k]；m；η，按给定模态顺序，不作重新归一化或模态重排 | `systems`全部IDs |
| `modal_velocity` | components [k]；m/s；η对时间导数 | `systems`全部IDs |

结果HDF5仅含输出arrays、所需IDs及时间轴，不重复坐标或输入字段；严格遵守输入行序。不能对速度作平移拟合、重排模态或重新归一化。

## 接收边界

正式数据须核验相容性、唯一连续分支、所请求观测存在、无有限时间发散，并以独立基准证实预算内能达到目标。几何／约束适定、矩阵条件数、精度及预算目前没有正式数值验证；合法格式不能替代这些证据。
每个输入轴至多201帧，输入字段与输出字段各自总分量数至多2000000；不是对HDF5压缩后字节数的约束。
