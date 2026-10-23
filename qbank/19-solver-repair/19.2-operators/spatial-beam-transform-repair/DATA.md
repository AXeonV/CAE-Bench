# DATA：空间线弹性梁算子

遵循 [CONTRACT](../../../../docs/CONTRACT.md)。`task` 固定 `spatial-beam-transform-repair`，`spatial_dimension=3`，`physics.model=linear-timoshenko-spatial-beam-v1`，`physics.parameters={}`；`geometries`、`meshes` 为空对象，`conditions=[]`。全部几何与材料在逐梁输入数组中声明。

`data_file=input.h5`。`locations={"beams":{"kind":"entities","ids":"beam_ids"}}`；`beam_ids` 是1至16个严格递增的唯一正 `int64` 身份编号，顺序定义各数组对应关系，编号数值无物理意义。`time_axes={"instant":"times"}`，`times` 是 `float64` 数组 `[0.0]`，表示静力求值状态。

所有下表输入均 `float64`，形状 `[1,N,C]`，其中N为梁数，C为分量数。对象名与HDF5 key相同；`location=beams`，`time_axis=instant`，`component_shape=[C]`，`value_kind=point`；C=1用`kind=scalar`，否则`kind=components`。输入 `sampling={"space":"uniform","time":"constant","extrapolation":"forbid"}`。

| 对象/key | quantity | unit | components及含义 |
|---|---|---|---|
| endpoints | endpoints | m | root_x,root_y,root_z,tip_x,tip_y,tip_z；全局端点坐标 |
| section_axis | section_reference_axis | 1 | x,y,z；全局截面参考方向 |
| young_modulus | young_modulus | Pa | value；E |
| poisson_ratio | poisson_ratio | 1 | value；ν |
| area | cross_section_area | m^2 | value；A |
| inertia_y | second_moment_y | m^4 | value；Iyy=∫z²dA |
| inertia_z | second_moment_z | m^4 | value；Izz=∫y²dA |
| torsion_constant | torsion_constant | m^4 | value；J，非极惯性矩默认值 |
| shear_area_y | effective_shear_area_y | m^2 | value；Ay |
| shear_area_z | effective_shear_area_z | m^2 | value；Az |
| density | density | kg/m^3 | value；ρ |
| body_acceleration | body_acceleration | m/s^2 | x,y,z；全局恒定体加速度b |
| tip_load | normalized_generalized_force | N | fx,fy,fz,mx_over_L,my_over_L,mz_over_L；全局端部力及力矩/梁长 |

长度L=|x1-x0|在[0.1,20]m，端点各坐标绝对值≤100m。令t=(x1-x0)/L，参考方向a的模在[0.1,10]，其对t的正交投影模≥0.1|a|。局部y方向n是a-(a·t)t归一化，局部z方向m=t×n，局部x方向t。R的三行是t,n,m，故R将全局向量分量变到局部分量。截面方向由这些输入唯一定义，不按载荷方向重新选轴。

E在[1e9,3e11]Pa，ν在[0,0.45]，A在[1e-4,0.1]m²，Iyy、Izz、J在[1e-8,1e-3]m⁴，Ay、Az在[1e-5A,A]，ρ在[100,2e4]kg/m³。G=E/[2(1+ν)]。局部y位移与绕z弯曲由EIzz及GAy控制，局部z位移与绕y弯曲由EIyy及GAz控制，轴向和扭转刚度分别为EA、GJ。输入b每分量绝对值≤20m/s²，tip_load每分量绝对值≤1e4N。

所有初始位移/转角固定为零。体加速度在空间常量，线载荷w=ρAb。外力数组仅包含其一致节点贡献，不含tip_load；在局部物理自由度中，两个节点的轴向及横向力均为w_local L/2，绕z端矩为[+w_yL²/12,-w_yL²/12]，绕y端矩为[-w_zL²/12,+w_zL²/12]。节点力矩按全局右手小转角虚功定义。

物理自由度顺序d为 `[u0x,u0y,u0z,θ0x,θ0y,θ0z,u1x,u1y,u1z,θ1x,θ1y,θ1z]`，θ为全局右手小转角，力向量f按同顺序包含全局力及力矩。令S=diag(1,1,1,L,L,L,1,1,1,L,L,L)，公开归一化自由度q=S d、力p=S^-T f、刚度Knorm=S^-T K S^-1，所以pᵀq=fᵀd。q单位m，p单位N，Knorm单位N/m。归一化只改变单位，不改变梁力学定义。

输出文件须原样复制 `beam_ids` 和 `times`，另含以下五个 `float64` 场数组，均 `[1,N,C]`，元数据沿用上述公共属性，输出无sampling：

| 对象/key | quantity | unit | C及components |
|---|---|---|---|
| lhs_combined | normalized_stiffness | N/m | 144；row_0_col_0至row_11_col_11，按行优先 |
| lhs_separate | normalized_stiffness | N/m | 144；同上 |
| rhs_combined | normalized_generalized_force | N | 12；dof_0至dof_11 |
| rhs_separate | normalized_generalized_force | N | 12；同上 |
| tip_displacement | normalized_displacement | m | 6；ux,uy,uz,L_rx,L_ry,L_rz |

combined来自`CalculateLocalSystem`，separate分别来自`CalculateLeftHandSide`及`CalculateRightHandSide`。自由端解按combined矩阵Knorm的后6×6块求解：q_tip=Knorm_tip,tip^-1(p_body,tip+tip_load)，根端前6个q为零。本输出是夹持单元的有限元静力响应；有体载荷时不额外要求等于连续梁的均布载荷精确解。

