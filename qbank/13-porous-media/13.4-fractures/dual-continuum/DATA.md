# 双连续体瞬态渗流的数据约定

本题使用[通用数据协议](../../../../docs/CONTRACT.md)，以下定义本题的全部专用语义。task 为 `dual-continuum`（可以省略，由单题工具包确定）；spatial_dimension 必须为整数 2。只使用 `physics` 形式，不同时提供 profile、analysis、materials 或 contract_version。

## 文件、网格与位置

data_file 指向单个扁平 HDF5 文件；文件名与 HDF5 key 不携带物理含义。meshes 恰含 main，指向 Gmsh MSH 4.1 ASCII 的平面三角网格，z=0。geometries 可为空或按协议引用文件，不要求运行几何脚本。

三角形 type 2 描述参考域，线段 type 1 导出全部外边界，每条外边界恰好一次；不导出点单元。三角形沿边连通，共享节点 tag 的内部边表示相邻连续材料，不是边界。没有未使用节点、重复几何三角形、非流形或悬挂节点。

locations.domain 为全部三角形节点：kind=mesh、mesh=main、entity=node。locations.cells 为全部三角形：entity=element、dimension=2。二者均完整覆盖，ids 引用严格递增 int64 tag。其他条件位置为同网格节点子集或线段子集；边界线段位置 dimension=1，节点位置不写 dimension。Physical Group 如果声明必须与 IDs 精确一致，不按组名判断条件。

节点边界位置表示所有顶点都在该节点集中的完整外边界线段；节点集必须正好等于这些线段的端点并，不允许孤立节点。element 线段位置的条件在线段上分片常数，节点边界按端点值线性重建。外法向由唯一相邻三角形指向域外，与线段 tag、节点存储顺序无关。

本题只导出三角形与外边界线段，不允许内部线段或其他单元类型。

不使用 points、entities、aggregate 或其他网格位置。

## 物理声明与参数

physics.model 必须为 `porous-dual-continuum-v1`，parameters 恰含下表全部键。每项为 `{"value":有限数值,"unit":"表中代码"}`，不得写成数组或场引用。

| parameters 键 | unit | 含义与范围 |
|---|---|---|
| `start_time` | `s` | 物理初始时刻 t0 |
| `end_time` | `s` | 结束时刻 tf>t0 |
| `density` | `kg/m3` | 恒定参考密度 ρ，必须严格正值 |
| `viscosity` | `Pa.s` | 动力黏度 μ，必须严格正值 |
| `gravity_x` | `m/s2` | 重力加速度 x 分量 gx |
| `gravity_y` | `m/s2` | 重力加速度 y 分量 gy |

## 物理响应

一个固定二维区域中有基质 m、裂隙 f 两个重叠连续体，使用同一参考几何而有独立压力。K_m、K_f 与 C_m、C_f 均按单位总体积折算，不能各再乘体积份额或把总体积算两次。q_i=−K_i(∇p_i−ρg)/μ，储量变化为 C_i dp_i；e=α(pm−pf) 正值基质流入裂隙。基质净源为 Qm−e，裂隙净源为 Qf+e，二者交换严格相反。边界条件与初态按每个连续体独立读取，不以单一等效压代替两个状态。

## 时间、字段与连续含义

time_axes 必含 initial=[t0]、response（1..101 个严格递增请求时刻，位于 [t0,tf]）。材料、初态及标明 static 的记录只引用 initial。变化载荷可另引用加载轴，该轴至少两帧且端点恰为 t0、tf；单帧载荷必须引用 initial 并在全过程恒定。全部轴均须被字段或输出使用。response 不表示内部时间步；只输出声明时刻，不额外输出 t0 或迭代历史。
数据保证初态与 t0 的给定状态边界相容。若请求 t0，已给定状态按其初态空间重建输出，代数量由该初态及材料计算；依赖梯度的通量用初态在各三角形内的梯度计算，不先投影或修改初态。界面法向通量连续要求适用于 t>t0，不要求任意初态梯度已经满足该条件。

fields 的逻辑名与 array key 可任意取协议允许的唯一名称，条件引用逻辑名，HDF5 使用 array key。所有数值场 dtype=float64。scalar 为 [T,N,1]、component_shape=[1]、components=["value"]；vector 为 [T,N,2]、[2]、["x","y"]；tensor 为 [T,N,2,2]、[2,2]、["xx","xy","yx","yy"]。不使用 Voigt、局部坐标或省略轴。

节点场 value_kind=point、sampling.space=piecewise_linear，按参考三角形重心坐标作 P1 重建；边界节点按线段线性重建。element 位置的材料、体源及线段场 value_kind=average、space=piecewise_constant，给定均值同时定义整个实体上的常值。材料在时间上恒定；单帧 sampling.time=constant，多帧为 linear（分量逐段线性），extrapolation=forbid。非线性响应在重建后计算，不对响应直接插值。

每个字段 quantity 必须等于下表对应的 data 键；键为 value 时 quantity 等于条件 variable。字段 location 必须与条件 location 相同，unit、kind、分量由下表固定。只允许被条件引用的 fields；引用同一字段可复用，但不隐式广播或匹配不同位置。标量数据可取同单位的 {"value":数值,"unit":"代码"} 常量或 {"field":"字段逻辑名"}；矢量、张量只能引用 HDF5 场。常量表示在该条件位置和全过程均匀。

## 全部条件

每条记录恰含 role、variable、location、operator、data。operator 必须逐字采用下列小节标题；每节给出全部 data 键，必需记录不得省略。材料／源／初态在其全支撑上各恰有一条记录，不能用顺序叠加或省略源来表示零源。边界记录可有多条，以同一未知变量为组不允许覆盖同一完整外边界线段；同一未知变量的节点边界记录之间也不共享节点，不同连续体可共享几何节点。同一节点位置可由一条记录包含多个边界分段。

### matrix_pressure

role=`boundary`，variable=`matrix_pressure`，location=完整外边界节点子集；必需。支持上述时间表示。data 恰含：

| data 键 | 表示与含义 |
|---|---|
| `value` | scalar，component_shape=[1]，unit=`Pa`；基质连续体给定压力 |

### matrix_normal_flux

role=`boundary`，variable=`matrix_volume`，location=外边界线段子集；可选。支持上述时间表示。data 恰含：

| data 键 | 表示与含义 |
|---|---|
| `value` | scalar，component_shape=[1]，unit=`m/s`；基质连续体向外折算体积通量 |

### initial_matrix

role=`initial`，variable=`matrix_pressure`，location=domain（全部域节点）；必需。仅使用静态初始轴。data 恰含：

| data 键 | 表示与含义 |
|---|---|
| `value` | scalar，component_shape=[1]，unit=`Pa`；基质连续体初压 |

### fracture_pressure

role=`boundary`，variable=`fracture_pressure`，location=完整外边界节点子集；必需。支持上述时间表示。data 恰含：

| data 键 | 表示与含义 |
|---|---|
| `value` | scalar，component_shape=[1]，unit=`Pa`；裂隙连续体给定压力 |

### fracture_normal_flux

role=`boundary`，variable=`fracture_volume`，location=外边界线段子集；可选。支持上述时间表示。data 恰含：

| data 键 | 表示与含义 |
|---|---|
| `value` | scalar，component_shape=[1]，unit=`m/s`；裂隙连续体向外折算体积通量 |

### initial_fracture

role=`initial`，variable=`fracture_pressure`，location=domain（全部域节点）；必需。仅使用静态初始轴。data 恰含：

| data 键 | 表示与含义 |
|---|---|
| `value` | scalar，component_shape=[1]，unit=`Pa`；裂隙连续体初压 |

### material

role=`material`，variable=`dual_medium`，location=cells（全部三角形）；必需。仅使用静态初始轴。data 恰含：

| data 键 | 表示与含义 |
|---|---|
| `exchange` | scalar，component_shape=[1]，unit=`1/(Pa.s)`；单位总体积交换 α>0，正流向为基质至裂隙连续体 |
| `matrix_permeability` | tensor，component_shape=[2, 2]，unit=`m2`；基质连续体体积折算渗透率 K，已含体积份额；完整矩阵必须全局对称正定，存储的对称分量完全一致；特征值范围为 [1e-16,1e-6] m2，谱条件数≤1e6 |
| `matrix_storage` | scalar，component_shape=[1]，unit=`1/Pa`；基质连续体单位总体积压力储集 C>0，已含体积份额 |
| `fracture_permeability` | tensor，component_shape=[2, 2]，unit=`m2`；裂隙连续体体积折算渗透率 K，已含体积份额；完整矩阵必须全局对称正定，存储的对称分量完全一致；特征值范围为 [1e-16,1e-6] m2，谱条件数≤1e6 |
| `fracture_storage` | scalar，component_shape=[1]，unit=`1/Pa`；裂隙连续体单位总体积压力储集 C>0，已含体积份额 |

### volume_source

role=`source`，variable=`dual_volume`，location=cells（全部三角形）；必需。支持上述时间表示。data 恰含：

| data 键 | 表示与含义 |
|---|---|
| `matrix` | scalar，component_shape=[1]，unit=`1/s`；基质单位总体积注入 |
| `fracture` | scalar，component_shape=[1]，unit=`1/s`；裂隙连续体单位总体积注入 |

每个连续体都至少有一条自身的 pressure 外边界；其余未覆盖边对该连续体 normal_flux=0。同一几何边可分别给基质和裂隙连续体条件，它们属于不同未知量，不算重叠；同一连续体的压力与通量不能在完整边上叠加。两套初压都必需。

## 输出

outputs 必须恰好请求下表各 quantity，每种恰好一次，逻辑名与 array key 不固定。全部输出 dtype=float64、time_axis=response，kind、component_shape、components 按上面的统一分量表。cells 上 value_kind=average 表示三角形面积平均。非线性量先由连续状态计算再积分，不能用平均状态代入非线性关系。压力保留已声明的基准，其余量保留物理符号。

| quantity | location | kind／shape | unit | 含义 |
|---|---|---|---|---|
| `matrix_pressure` | `cells` | scalar／[1] | `Pa` | 基质连续体压力平均 |
| `matrix_velocity` | `cells` | vector／[2] | `m/s` | 基质连续体体积折算 Darcy 通量平均 |
| `fracture_pressure` | `cells` | scalar／[1] | `Pa` | 裂隙连续体压力平均 |
| `fracture_velocity` | `cells` | vector／[2] | `m/s` | 裂隙连续体体积折算 Darcy 通量平均 |
| `exchange_rate` | `cells` | scalar／[1] | `1/s` | α(pm−pf) 的单元平均，正值基质流向裂隙 |

result.h5 仅包含上述 outputs.array 及这些输出引用的位置 IDs 和时间轴。共享 key 只写一次，不复制坐标、输入材料或网格。可用 `caeoj.sdk.load_problem`、`read_field`、`write_result` 辅助读写，也可直接使用 JSON、Gmsh、HDF5 库；结构工具不求解或修正物理结果。
