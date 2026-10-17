# 固定孔隙层流瞬态流动的数据约定

本题使用[通用数据协议](../../../../docs/CONTRACT.md)，以下定义本题的全部专用语义。task 为 `pore-laminar-transient`（可以省略，由单题工具包确定）；spatial_dimension 必须为整数 2。只使用 `physics` 形式，不同时提供 profile、analysis、materials 或 contract_version。

## 文件、网格与位置

data_file 指向单个扁平 HDF5 文件；文件名与 HDF5 key 不携带物理含义。meshes 恰含 main，指向 Gmsh MSH 4.1 ASCII 的平面三角网格，z=0。geometries 可为空或按协议引用文件，不要求运行几何脚本。

三角形 type 2 描述参考域，线段 type 1 导出全部外边界，每条外边界恰好一次；不导出点单元。三角形沿边连通，共享节点 tag 的内部边表示相邻连续材料，不是边界。没有未使用节点、重复几何三角形、非流形或悬挂节点。

locations.domain 为全部三角形节点：kind=mesh、mesh=main、entity=node。locations.cells 为全部三角形：entity=element、dimension=2。二者均完整覆盖，ids 引用严格递增 int64 tag。其他条件位置为同网格节点子集或线段子集；边界线段位置 dimension=1，节点位置不写 dimension。Physical Group 如果声明必须与 IDs 精确一致，不按组名判断条件。

节点边界位置表示所有顶点都在该节点集中的完整外边界线段；节点集必须正好等于这些线段的端点并，不允许孤立节点。element 线段位置的条件在线段上分片常数，节点边界按端点值线性重建。外法向由唯一相邻三角形指向域外，与线段 tag、节点存储顺序无关。

本题只导出三角形与外边界线段，不允许内部线段或其他单元类型。

网格只覆盖流体孔隙，可以有固体孔壁围成的孔洞。locations.mean 是唯一 aggregate：source=cells、operation=mean，ids 为含一个非负 int64 ID 的数组。它用于流体域面积平均，不能替换为空间探针；其余位置不使用 aggregate、points 或 entities。

## 物理声明与参数

physics.model 必须为 `porous-pore-laminar-transient-v1`，parameters 恰含下表全部键。每项为 `{"value":有限数值,"unit":"表中代码"}`，不得写成数组或场引用。

| parameters 键 | unit | 含义与范围 |
|---|---|---|
| `start_time` | `s` | 物理初始时刻 t0 |
| `end_time` | `s` | 结束时刻 tf>t0 |
| `density` | `kg/m3` | 恒定参考密度 ρ，必须严格正值 |
| `viscosity` | `Pa.s` | 动力黏度 μ，必须严格正值 |
| `pressure_mean` | `Pa` | 仅当全部外边界为速度条件时指定的体域平均压力；存在牵引边界时必须为 0 且不再约束平均压 |

## 物理响应

网格显式给出固定连通流体孔隙，wall 为固定无滑移孔壁。单相、不可压缩、牛顿、等温层流，保留局部加速度和速度对流惯性；无湍流闭合。总应力 σ=−pI+μ(∇u+∇uᵀ)，体力 f 已含重力；初态给真实流体速度，不是迭代初猜。没有牵引边界时每时刻用全域平均 p=pressure_mean 定压零点；存在牵引时不加均值。mean_pore_velocity 仅对流体面积平均，不乘未知孔隙率。数据保证在给定时间内有唯一足够正则的层流响应。

## 时间、字段与连续含义

time_axes 必含 initial=[t0]、response（1..101 个严格递增请求时刻，位于 [t0,tf]）。材料、初态及标明 static 的记录只引用 initial。变化载荷可另引用加载轴，该轴至少两帧且端点恰为 t0、tf；单帧载荷必须引用 initial 并在全过程恒定。全部轴均须被字段或输出使用。response 不表示内部时间步；只输出声明时刻，不额外输出 t0 或迭代历史。
数据保证初态与 t0 的给定状态边界相容。若请求 t0，已给定状态按其初态空间重建输出，代数量由该初态及材料计算；依赖梯度的通量用初态在各三角形内的梯度计算，不先投影或修改初态。界面法向通量连续要求适用于 t>t0，不要求任意初态梯度已经满足该条件。
孔隙流初态只给速度，t0 压力取唯一物理响应的有限右极限并遵守已声明的压力基准；数据保证该极限存在。

fields 的逻辑名与 array key 可任意取协议允许的唯一名称，条件引用逻辑名，HDF5 使用 array key。所有数值场 dtype=float64。scalar 为 [T,N,1]、component_shape=[1]、components=["value"]；vector 为 [T,N,2]、[2]、["x","y"]；tensor 为 [T,N,2,2]、[2,2]、["xx","xy","yx","yy"]。不使用 Voigt、局部坐标或省略轴。

节点场 value_kind=point、sampling.space=piecewise_linear，按参考三角形重心坐标作 P1 重建；边界节点按线段线性重建。element 位置的材料、体源及线段场 value_kind=average、space=piecewise_constant，给定均值同时定义整个实体上的常值。材料在时间上恒定；单帧 sampling.time=constant，多帧为 linear（分量逐段线性），extrapolation=forbid。非线性响应在重建后计算，不对响应直接插值。

每个字段 quantity 必须等于下表对应的 data 键；键为 value 时 quantity 等于条件 variable。字段 location 必须与条件 location 相同，unit、kind、分量由下表固定。只允许被条件引用的 fields；引用同一字段可复用，但不隐式广播或匹配不同位置。标量数据可取同单位的 {"value":数值,"unit":"代码"} 常量或 {"field":"字段逻辑名"}；矢量、张量只能引用 HDF5 场。常量表示在该条件位置和全过程均匀。

## 全部条件

每条记录恰含 role、variable、location、operator、data。operator 必须逐字采用下列小节标题；每节给出全部 data 键，必需记录不得省略。材料／源／初态在其全支撑上各恰有一条记录，不能用顺序叠加或省略源来表示零源。边界记录可有多条，以同一未知变量为组不允许覆盖同一完整外边界线段；同一未知变量的节点边界记录之间也不共享节点，不同连续体可共享几何节点。同一节点位置可由一条记录包含多个边界分段。

### body_force

role=`source`，variable=`momentum`，location=cells（全部三角形）；必需。支持上述时间表示。data 恰含：

| data 键 | 表示与含义 |
|---|---|
| `value` | vector，component_shape=[2]，unit=`N/m3`；每单位流体体积体力 f，已包含重力 |

### wall

role=`boundary`，variable=`velocity`，location=外边界线段子集；必需。支持上述时间表示。data 恰含：

| data 键 | 表示与含义 |
|---|---|
| `motion` | `{"option":"stationary"}`；固定无滑移孔壁 |

### velocity

role=`boundary`，variable=`velocity`，location=完整外边界节点子集；可选。支持上述时间表示。data 恰含：

| data 键 | 表示与含义 |
|---|---|
| `value` | vector，component_shape=[2]，unit=`m/s`；给定流体速度 uD |

### traction

role=`boundary`，variable=`traction`，location=外边界线段子集；可选。支持上述时间表示。data 恰含：

| data 键 | 表示与含义 |
|---|---|
| `value` | vector，component_shape=[2]，unit=`Pa`；全局总牵引 σn，σ=−pI+μ(∇u+∇uᵀ) |

### initial_velocity

role=`initial`，variable=`velocity`，location=domain（全部域节点）；必需。仅使用静态初始轴。data 恰含：

| data 键 | 表示与含义 |
|---|---|
| `value` | vector，component_shape=[2]，unit=`m/s`；初始流体速度 u0 |

wall 至少覆盖一条孔壁边，motion 只能是 {"option":"stationary"}，表示 u=0，不是数值标量。wall、velocity、traction 必须互斥并完整覆盖全部外边界；wall 与 velocity 均视为速度约束，velocity 数据在与 wall 相接节点处必须为零。仅速度边界时数据保证净体积流入为零。瞬态初速度无散且与 t0 边界相容。牵引指定黏性与压力的总作用，不能误作仅法向压力。牵引边界上的速度符号不预设，数据保证有唯一适用范围内的物理解。

## 输出

outputs 必须恰好请求下表各 quantity，每种恰好一次，逻辑名与 array key 不固定。全部输出 dtype=float64、time_axis=response，kind、component_shape、components 按上面的统一分量表。cells 上 value_kind=average 表示三角形面积平均。mean 上 average 表示整个流体域面积平均。非线性量先由连续状态计算再积分，不能用平均状态代入非线性关系。压力保留已声明的基准，其余量保留物理符号。

| quantity | location | kind／shape | unit | 含义 |
|---|---|---|---|---|
| `pressure` | `cells` | scalar／[1] | `Pa` | 流体机械压力 p 的单元平均 |
| `pore_velocity` | `cells` | vector／[2] | `m/s` | 孔隙内部真实流体速度 u 的单元平均 |
| `mean_pore_velocity` | `mean` | vector／[2] | `m/s` | 流体区域面积平均 ∫Ωu dA/|Ω|，不是总体积表观速度 |

result.h5 仅包含上述 outputs.array 及这些输出引用的位置 IDs 和时间轴。共享 key 只写一次，不复制坐标、输入材料或网格。可用 `caeoj.sdk.load_problem`、`read_field`、`write_result` 辅助读写，也可直接使用 JSON、Gmsh、HDF5 库；结构工具不求解或修正物理结果。
