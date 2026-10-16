# 非饱和稳态渗流的数据约定

本题使用[通用数据协议](../../../../docs/CONTRACT.md)，以下定义本题的全部专用语义。task 为 `richards-steady`（可以省略，由单题工具包确定）；spatial_dimension 必须为整数 2。只使用 `physics` 形式，不同时提供 profile、analysis、materials 或 contract_version。

## 文件、网格与位置

data_file 指向单个扁平 HDF5 文件；文件名与 HDF5 key 不携带物理含义。meshes 恰含 main，指向 Gmsh MSH 4.1 ASCII 的平面三角网格，z=0。geometries 可为空或按协议引用文件，不要求运行几何脚本。

三角形 type 2 描述参考域，线段 type 1 导出全部外边界，每条外边界恰好一次；不导出点单元。三角形沿边连通，共享节点 tag 的内部边表示相邻连续材料，不是边界。没有未使用节点、重复几何三角形、非流形或悬挂节点。

locations.domain 为全部三角形节点：kind=mesh、mesh=main、entity=node。locations.cells 为全部三角形：entity=element、dimension=2。二者均完整覆盖，ids 引用严格递增 int64 tag。其他条件位置为同网格节点子集或线段子集；边界线段位置 dimension=1，节点位置不写 dimension。Physical Group 如果声明必须与 IDs 精确一致，不按组名判断条件。

节点边界位置表示所有顶点都在该节点集中的完整外边界线段；节点集必须正好等于这些线段的端点并，不允许孤立节点。面／边条件在相应线段上分片常数。外法向由唯一相邻三角形指向域外，与线段 tag、节点存储顺序无关。

本题只导出三角形与外边界线段，不允许内部线段或其他单元类型。

不使用 points、entities、aggregate 或其他网格位置。

## 物理声明与参数

physics.model 必须为 `porous-richards-steady-v1`，parameters 恰含下表全部键。每项为 `{"value":有限数值,"unit":"表中代码"}`，不得写成数组或场引用。

| parameters 键 | unit | 含义与范围 |
|---|---|---|


本题 parameters 为 `{}`，没有全局标量参数。

## 物理响应

气相恒压且不运动，水不发生蒸发或相变，忽略动量惯性。y 轴向上，压力水头 h 是水压减气压后除以恒定水重度，不是总水头；总水头为 h+y。q=−Ks kr(h)∇(h+y)。设 m=1−1/n；h<0 时 Se=[1+(α|h|)^n]^(−m)，h≥0 时 Se=1；θ=θr+(φ−θr)Se，kr=Se^(1/2)[1−(1−Se^(1/m))^m]^2。Ks 是饱和水力传导率而非 m2 的本征渗透率。稳态按水体积守恒平衡 Q；不引入滞回、大气交换或未声明的蒸散。

## 时间、字段与连续含义

time_axes 恰含 steady，其 HDF5 数组为 float64[1] 的 [0.0]。所有输入与输出引用 steady，不提供初态或多帧。

fields 的逻辑名与 array key 可任意取协议允许的唯一名称，条件引用逻辑名，HDF5 使用 array key。所有数值场 dtype=float64。scalar 为 [T,N,1]、component_shape=[1]、components=["value"]；vector 为 [T,N,2]、[2]、["x","y"]；tensor 为 [T,N,2,2]、[2,2]、["xx","xy","yx","yy"]。不使用 Voigt、局部坐标或省略轴。

节点场 value_kind=point、sampling.space=piecewise_linear，按参考三角形重心坐标作 P1 重建；边界节点按线段线性重建。材料、源及线段场 value_kind=average、space=piecewise_constant，给定均值同时定义整个实体上的常值。材料在时间上恒定；单帧 sampling.time=constant，多帧为 linear（分量逐段线性），extrapolation=forbid。初态按同样空间规则定义，不能当迭代初猜；传输中的非线性响应在重建后计算，不对响应直接插值。

每个字段 quantity 必须等于下表对应的 data 键；键为 value 时 quantity 等于条件 variable。字段 location 必须与条件 location 相同，unit、kind、分量由下表固定。只允许被条件引用的 fields；引用同一字段可复用，但不隐式广播或匹配不同位置。标量数据可取同单位的 {"value":数值,"unit":"代码"} 常量或 {"field":"字段逻辑名"}；矢量、张量只能引用 HDF5 场。常量表示在该条件位置和全过程均匀。

## 全部条件

每条记录恰含 role、variable、location、operator、data。下表列出全部算子和 data 键；必需记录不得省略。材料／源／初态在其全支撑上各恰有一条记录，不能用顺序叠加或省略源来表示零源。边界记录可有多条，以同一未知变量为组不允许覆盖同一完整外边界线段；节点条件之间也不共享节点，同一节点位置可由一条记录包含多个边界分段。

### material

role=`material`，variable=`unsaturated_medium`，location=cells（全部三角形）；必需。支持上述时间表示。data 恰含：

| data 键 | 表示与含义 |
|---|---|
| `hydraulic_conductivity` | tensor，component_shape=[2, 2]，unit=`m/s`；饱和水力传导张量 Ks；特征值位于 [1e-12,1e-2] m/s，条件数≤1e6 |
| `porosity` | scalar，component_shape=[1]，unit=`1`；孔隙体积分数 φ，0.05≤φ≤0.8 |
| `residual_water` | scalar，component_shape=[1]，unit=`1`；残余体积含水率 θr，0≤θr<φ |
| `retention_alpha` | scalar，component_shape=[1]，unit=`1/m`；持水参数 α，0.01≤α≤10 |
| `retention_n` | scalar，component_shape=[1]，unit=`1`；持水参数 n，1.2≤n≤4 |

### volume_source

role=`source`，variable=`water_volume`，location=cells（全部三角形）；必需。支持上述时间表示。data 恰含：

| data 键 | 表示与含义 |
|---|---|
| `value` | scalar，component_shape=[1]，unit=`1/s`；单位总体积净水体积注入 Q |

### head

role=`boundary`，variable=`pressure_head`，location=完整外边界节点子集；必需。支持上述时间表示。data 恰含：

| data 键 | 表示与含义 |
|---|---|
| `value` | scalar，component_shape=[1]，unit=`m`；相对恒定气压的压力水头 hD，−100≤hD≤100 |

### normal_flux

role=`boundary`，variable=`water_flux`，location=外边界线段子集；可选。支持上述时间表示。data 恰含：

| data 键 | 表示与含义 |
|---|---|
| `value` | scalar，component_shape=[1]，unit=`m/s`；向外 Darcy 水通量 |

head 至少覆盖一条外边界以固定压力水头；未覆盖处向外水通量为零。head 与 normal_flux 不覆盖同一完整边。材料界面水压力水头与法向水通量连续；持水关系可跳变，θ 不要求跨界面连续。所有初边值及物理解均位于 h∈[−100,100] m。

## 输出

outputs 必须恰好请求下表各 quantity，每种恰好一次，逻辑名与 array key 不固定。全部输出 dtype=float64、time_axis=steady，kind、component_shape、components 按上面的统一分量表。cells 上 value_kind=average 表示三角形面积平均；fractures 上 average 为线长平均，mean 上 average 为整个流体域面积平均。非线性量先由连续状态计算再积分，不能用平均状态代入非线性关系。所有量保留其物理压力基准和符号。

| quantity | location | kind／shape | unit | 含义 |
|---|---|---|---|---|
| `pressure_head` | `cells` | scalar／[1] | `m` | 压力水头 h 的单元平均 |
| `water_content` | `cells` | scalar／[1] | `1` | 体积含水率 θ(h) 的单元平均，不含弹性储集量 |
| `darcy_velocity` | `cells` | vector／[2] | `m/s` | Darcy 水通量 q 的单元平均 |

result.h5 仅包含上述 outputs.array 及这些输出引用的位置 IDs 和时间轴。共享 key 只写一次，不复制坐标、输入材料或网格。可用 `caeoj.sdk.load_problem`、`read_field`、`write_result` 辅助读写，也可直接使用 JSON、Gmsh、HDF5 库；结构工具不求解或修正物理结果。
