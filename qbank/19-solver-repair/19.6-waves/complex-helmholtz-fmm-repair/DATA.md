# 输入与输出

本题是三维标量 Helmholtz 复核与固定离散算子求值。遵循 [CONTRACT](../../../../docs/CONTRACT.md) 的 JSON、Gmsh和HDF5规则，以下给出完整题内语义。输入声明包含 `task: complex-helmholtz-fmm-repair`、`spatial_dimension: 3`、`data_file: input.h5`；`geometries`、`conditions` 均为空。无时间演化：`time_axes` 恰为 `{"instant":"times"}`，`times` 为 float64 `[0.0]`，所有场仅有一个静态标签。

## 参数与核

`physics.model` 为 `complex-helmholtz-operators-v1`。`physics.parameters` 恰含下表各项；每项恰含 `value` 和 `unit`，无省略或缺省值。有限数值不接受布尔值，整数必须是JSON整数。

| 参数 | value | unit |
| --- | --- | --- |
| operation | 整数0或1 | `1` |
| wavenumber_real | [0.5,3]内实数 | `1/m` |
| wavenumber_imag | [0,1.2]内实数 | `1/m` |

设 k=wavenumber_real+i*wavenumber_imag，采用 exp(-iωt) 时间约定及外向核 G(x,y)=exp(ik r)/(4πr)，r=|x-y|，坐标单位m。虚部为零亦属合法输入。所有向量按全局笛卡尔x/y/z排列，不存在局部坐标。复值均按实部、虚部分量表示；不使用HDF5复数dtype。

## operation=0：点相互作用

`meshes` 为空。`locations` 恰含 `sources` 和 `targets`，二者均为 `kind: points`，分别引用 `source_ids`/`source_coordinates`、`target_ids`/`target_coordinates`。编号均为非负严格递增int64[N]；坐标为float64[N,3]。源数32至512，目标数1至24，各坐标分量绝对值不超过10m。同表内不同点距离至少0.001m，任意源与目标距离至少0.2m。源、目标编号各自在其位置中有效，不按跨表相等编号认作同一对象。

唯一输入场为 `strength`，引用同名float64数组，位置 `sources`，quantity=`complex_source_strength`、unit=`1`、kind=`components`、component_shape=`[2]`、components=`["real","imag"]`、value_kind=`point`，time_axis=`instant`。数组形状 `[1,N_source,2]`；每个实／虚分量绝对值不超过2，可为零或负值。每个源是给定点源，不在空间内插值。

对每个目标返回 u=Σ_j G(x,y_j) q_j 和目标梯度 ∇_x u。逐项梯度为 G(x,y_j)(ik−1/r)(x−y_j)/r 乘q_j的和，单位分别m⁻¹、m⁻²。`fmm_*` 来自真实快速接口，`local_*` 来自真实局部相互作用接口；两条路径均需修复并输出，不能用其中一条覆盖另一条。

| 输出 | quantity | unit | components |
| --- | --- | --- | --- |
| fmm_potential | fmm_helmholtz_potential | `1/m` | real, imag |
| local_potential | local_helmholtz_potential | `1/m` | real, imag |
| fmm_gradient | fmm_helmholtz_target_gradient | `1/m2` | x_real, x_imag, y_real, y_imag, z_real, z_imag |
| local_gradient | local_helmholtz_target_gradient | `1/m2` | x_real, x_imag, y_real, y_imag, z_real, z_imag |

## operation=1：曲面算子

`meshes` 恰为 `{"surface":{"file":"surface.msh"}}`。这是无自交、连通、严格凸的闭合三角曲面；所有边恰被两个反向相邻面共享，外向法线由输入顶点顺序确定。只有一阶Gmsh type2三角面，每个节点均使用，不含额外体积、线或点单元；节点标签为1至1,000,000的正整数，元素标签为正整数。顶点18至100，三角面32至196；坐标分量绝对值不超过10m，边长至少0.05m，各面面积至少0.001m²，包围体积在[0.1,50]m³。相邻共面三角面允许；严格凸指其他非共面顶点位于每个外向面支撑平面的内侧。不得用输入顺序猜测内向／外向或由观测结果翻转法线。

`locations.surface_nodes` 为 `{"kind":"mesh","mesh":"surface","entity":"node","ids":"node_ids"}`；`node_ids` 为全部节点标签严格递增排列。`locations.targets` 与operation=0相同，但目标数1至12；每点在曲面外，与任意三角面距离至少0.3m，各坐标分量绝对值不超过10m，同表目标间距至少0.001m。

唯一输入场为 `density`，quantity=`complex_surface_density`、unit=`1`，其他dtype/kind/shape/components/value_kind/time_axis同strength，location=`surface_nodes`，shape=`[1,N_node,2]`。每个分量绝对值不超过2。密度为这些节点系数定义的连续P1曲面函数φ，在每个平面三角形内按重心坐标线性插值。此系数定义于实际输入网格，不是某连续曲面函数的另外采样解释。

以外向n定义 Sφ(x)=∫ΓG(x,y)φ(y)dS_y，Dφ(x)=∫Γ∂n_yG(x,y)φ(y)dS_y。V为S的边界迹，K为D的主值边界算子，不加±1/2跳跃项；W=-∂n_xD。其P1弱形式为

`A_W[i,j] = ∫Γ∫Γ G(x,y) [curlΓ ψ_i(x)·curlΓ ψ_j(y) - k² (n_x·n_y) ψ_i(x)ψ_j(y)] dS_y dS_x`，其中 curlΓψ=n×∇Γψ。

V和K的弱矩阵分别将G和∂n_yG在实P1试探／检验函数下作双积分。所有边界输出均是同一P1空间的离散强形式系数 `c=M^-1 A φ`，`M[i,j]=∫Γψ_iψ_j dS`；由真实库 `strong_form()` 给出。它们代表P1重构场的节点值，W亦为有限维弱泛函的质量矩阵表示，不能解释为连续超奇异场在尖角节点的经典值。外部势则在目标点直接评价S、D，不求解任何边界积分方程。

曲面算子固定调用 Bempp 的连续P1空间、双精度、Numba设备接口；regular积分阶6、singular积分阶8。评价对象是这些固定离散和积分设置的结果；不要求更改网格、积分规则、质量矩阵或提高阶数以代替源码修复。

| 输出 | quantity | location | unit |
| --- | --- | --- | --- |
| boundary_single_layer | projected_single_layer | surface_nodes | `m` |
| boundary_double_layer | projected_double_layer | surface_nodes | `1` |
| boundary_hypersingular | projected_hypersingular | surface_nodes | `1/m` |
| potential_single_layer | exterior_single_layer | targets | `m` |
| potential_double_layer | exterior_double_layer | targets | `1` |

这五项components均为 `["real","imag"]`。输出行严格按该location声明的IDs排列，不能沿用库内部自由度顺序。

## 公共字段与数组约束

两种操作的快速接口均固定展开阶10、ncrit=16、dense_evaluation=False，曲面近场表示为 `numba_evaluate`。两种操作均要求源区域的轴对齐包围盒对角线不超过4m：operation=0取点源坐标，operation=1取曲面顶点坐标；目标点不计入此直径约束。支持范围只覆盖这些固定设置的标量算子。

所有输出均引用同名数组，dtype=`float64`、kind=`components`、value_kind=`point`、time_axis=`instant`，component_shape为表中分量数；shape=`[1,N_location,N_component]`。未列出的字段、输出或位置均不允许。除当前操作所需IDs、coordinates、times及唯一输入场数组外，input.h5无其他dataset。mesh节点坐标只取Gmsh，不重复存于HDF5。输出只写当前操作的全部输出数组，不能附带另一操作的占位输出。输入节点重编号、面／节点存储顺序变化不得改变身份映射后的数值含义。
