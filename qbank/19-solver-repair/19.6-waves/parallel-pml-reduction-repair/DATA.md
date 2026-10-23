# 数据契约

本题固定 `task="parallel-pml-reduction-repair"`、`spatial_dimension=2`。通用文件、引用、HDF5和编号规则见 [CONTRACT](../../../../docs/CONTRACT.md)。以下定义本题的完整模型和支持范围。输入目录自包含 `problem.json`、`input.h5` 和 `mesh.msh`。

## 坐标、试件和离散

物理使用右手坐标(x,y,z)，波场与y无关，计算截面为(x,z)。协议二维坐标的第一、第二槽分别编码物理x、z；Gmsh XYZ三列为物理(x,z,0)，并非物理三维坐标。所有长度单位m。

网格含一个或两个不接触的矩形试件，每个试件在物理z=0至800，x方向宽600至2400。两个试件间水平空隙至少4h；没有接触、传输或流固耦合。每块由完整均匀正方形格构成，无孔洞、重叠单元或重复坐标节点，正方形边长h在20至25之间，全部试件使用同一h。只含Gmsh type3四节点单元，节点顺序为左下、右下、右上、左上，逆时针；总单元数768至6000。网格可采用任意合法正tag；严格递增的`cell_ids`给出完整单元集合，**单元tag递增即传给上游mesher的元素顺序**。单元节点由网格连接关系定义，HDF5中不另存网格节点或连接关系。

真实SPECFEM2D在每单元使用每方向5个GLL点的四阶谱元、double内部计算、显式二阶Newmark时间推进。非轴对称、无黏弹衰减、无重力、无周期条件，初始场为零，源固定不移动。分区使用上游 `partitioning_method=1`：N个单元按`cell_ids`顺序，前P−1个rank各得floor(N/P)个，末rank取得其余单元。共享网格节点仍由原生MPI装配，独立试件没有共享节点；不能改变指定的P或用串行替代。P为1、3或4。

`geometries={}`、`conditions=[]`；`meshes={"domain":{"file":"mesh.msh"}}`。本题源、边界和初态采用下述固定模型与显式场表示，不通过未声明的条件补定义。

## 物理分支和源

由`physics.model`选择分支：`parallel-scalar-sh-v1`为sh，`parallel-scalar-acoustic-potential-v1`为acoustic-potential。不另设数值类别参数。`physics.parameters`中的参数均为 `{"value":数值,"unit":"下表单位"}`，不允许其他参数或缺省。

| 参数 | 单位 | 含义与范围 |
|---|---|---|
| processes | 1 | JSON整数，指定MPI进程数1、3或4 |
| density | kg/m^3 | 均匀密度rho，1000至3000 |
| p_speed | m/s | SH分支的纵波速度cp或声学声速c，1000至4000 |
| s_speed | m/s | SH横波速度cs，1000至2000；声学严格为0 |
| frequency | Hz | 全部源共同的f，10至20 |
| time_step | s | 实际内部和记录步长dt，0.000125至0.00025 |

SH还要求cp>sqrt(4/3)cs，使各向同性体积模量为正。所有分支满足 `p_speed*dt/(0.1726731646460114*h)<=0.3`。上述速度和网格为本题固定离散输入，不由考生重新选择。

定义Ricker函数 `R(t)=(1−2*pi^2*f^2*t^2)*exp(−pi^2*f^2*t^2)`，其中心为物理t=0。每个源的幅度由`source_amplitude`给出，可以为负；全部源在同一时间中心同时作用、没有额外时移。二维delta是面积delta，积分为1，源不是沿边界施加的载荷，也不是按单元面积再次缩放的体积密度。固定源位置由`source_coordinates`给出，原生谱元用所在单元的张量积GLL Lagrange基函数分配点载荷；网格交界处的定位和装配按同一连续谱元场处理。

**sh：**唯一未知量u是物理y方向的反平面位移标量，单位m；不是协议二维向量。介质满足 `rho*u_tt−rho*cs^2*(u_xx+u_zz)=−sum(F_j*R(t)*delta_2(x−xj,z−zj))`。F为源幅度，单位N/m，代表单位出平面长度的y向线力；该方程固定负号，负F使响应反号。全部四壁为零法向导数，即零SH牵引。初始u及u_t均为零。SH分支禁止PML，`pml_region`全为0。

**acoustic-potential：**未知量chi为位移势，单位kg/m，满足 `chi_tt−c^2*(chi_xx+chi_zz)=sum(A_j*R(t)*delta_2(x−xj,z−zj))`。A为源幅度，单位N；此分支源正号与SH的负号不同。物理位移为`grad(chi)/rho`，单位m；压力为`−chi_tt`，单位Pa。这里不是速度势。有限起点的chi、chi_t均为零，所有C-PML记忆变量初态也为零。关闭上游`USE_TRICK_FOR_BETTER_PRESSURE`，直接记录原始chi，既不记录压力，也不进行时间积分、微分或归一化。

两分支的源在**有限起点** `t_start=−1.2/f` 开始，t<t_start不施加载荷。初始位移/势和一阶时间导数为零；R(t_start)虽很小但不是严格零，从该时刻按真实时间推进计算。不得把从负无穷激励建立的非零尾部场当初态。多个源可线性叠加，只作用于各自所在试件；本题不把一块的场传播到空隙或另一试件。

## 声学边界和C-PML

声学分支`pml_region`可以全部为0，此时四壁均为chi的齐次Neumann边界（刚性壁面法向位移为零）；不是压力释放边界。若非零，则每个试件顶部和底部各恰有三行元素标记为2，其余元素标记0。标记2为仅z方向C-PML；不存在x方向、旋转或角部PML。层厚L=3h，物理内部与PML界面为z=L及z=800−L，场通过同一谱元/MPI装配连续传播。左右边界仍为齐次Neumann；PML外终端z=0、800也采用chi的自然齐次Neumann边界，无额外Dirichlet强制值。

本题保留固定真实库的有限C-PML响应，包括其残余反射，不要求输出理想无反射解析场。PML参数自动调整关闭；令eta为从内界面向外的距离除以L，0<=eta<=1。固定剖面为Kz=1、`dz=−3*c*log(0.001)/L*eta^2`、`alpha_z=pi*f*(1−eta)`；x方向Kx=1、dx=alpha_x=0。卷积记忆变量和原生时间离散固定采用所附求解器实现。`public/Par_file.template`只是这些公开要求的运行配置载体，不另定义物理条件。

## 位置、时间和输入数组

HDF5为根组下扁平dataset。编号均为int64、坐标与时间为float64；每个编号表严格递增且无重复，独立点身份可为非负整数，网格tag须为正整数。Ns为1至2，Nr为2至8，Ne为网格全部单元数。源与接收器严格位于某一个试件内部，距离其每面墙均大于4h；每个接收点距每个源至少4h，无源/接收点重合。未激励试件允许零场。

| key | dtype / shape | 定义 |
|---|---|---|
| cell_ids | int64 [Ne] | 完整单元tag，行顺序同时定义原生分区顺序 |
| source_ids | int64 [Ns] | 源身份，行与源坐标和幅度对应 |
| source_coordinates | float64 [Ns,2] | 物理(x,z)位置，单位m |
| probe_ids | int64 [Nr] | 接收器身份，行与接收点坐标/输出N轴对应 |
| probe_coordinates | float64 [Nr,2] | 物理(x,z)位置，单位m |
| static_time | float64 [1] | 精确为[0]的静态标签，不是源开始时间 |
| times | float64 [Nt] | `t_start + k*dt`，k=0..Nt−1，单位s |
| source_amplitude | float64 [1,Ns,1] | 固定点载荷幅度；绝对值1e7至1e8，单位由分支指定 |
| pml_region | int64 [1,Ne,1] | 每单元恒定的类别标志0或2；平均值与该恒定标志相同 |

Nt为1000至6400，计算窗口长度Nt*dt为0.6至0.8s；最后采样为t_start+(Nt−1)dt，包含初始零场样本。没有输出时间插值或降采样，Nt个样本逐步对应Newmark的整步位移/势。源的内部时间取值与相同步长/物理时间映射固定。接收点采用其所在谱元的张量积GLL Lagrange空间插值；不做空间平均，不将接收点吸附到最近网格节点。

`locations`恰为：

```json
{
  "cells":{"kind":"mesh","mesh":"domain","entity":"element","dimension":2,"ids":"cell_ids"},
  "sources":{"kind":"points","ids":"source_ids","coordinates":"source_coordinates"},
  "probes":{"kind":"points","ids":"probe_ids","coordinates":"probe_coordinates"}
}
```

`time_axes={"static":"static_time","physical":"times"}`。`fields`恰含`source_amplitude`和`pml_region`；前者的quantity在SH/声学分别为`line_force_amplitude`/`acoustic_potential_source_amplitude`、unit为`N/m`/`N`，后者quantity为`spectral_element_pml_region`、unit为`1`。二者array与对象同名，location为`sources`/`cells`，time_axis均为`static`，dtype为`float64`/`int64`，kind为`scalar`，component_shape为[1]，components为["value"]，value_kind分别为`point`/`average`。标志的平均表示只是每单元恒定的编码，不代表对边界类别进行插值。

## 输出

输出HDF5必须包含`wave_response`，float64 [Nt,Nr,1]，轴依次为times、probe_ids行、单一标量分量。还须精确复制`times`和`probe_ids`作为输出支持数组；不重复点坐标，不复制源或单元标志，不附加未声明结果。

`outputs`恰有对象`response`，array=`wave_response`、location=`probes`、time_axis=`physical`、dtype=`float64`、kind=`scalar`、component_shape=[1]、components=["value"]、value_kind=`point`。quantity和unit在SH为`sh_displacement`、`m`，在声学为`acoustic_displacement_potential`、`kg/m`。

规定观测为所附真实库的原始ASCII seismogram输出：库先将采样幅值转换为IEEE单精度，再以7位有效数字输出；转换器读为float64写入HDF5。内部推进仍为double。该观测量化也是固定方法要求，不需要恢复未公开的额外精度。HDF5中的支持时间轴保留声明的float64值；ASCII时间只用于核对对应样本，不替换声明时间。数值评分容差见instruction。
