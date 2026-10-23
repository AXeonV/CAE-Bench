# 柱坐标真空场/PML 数据

遵循 [CONTRACT](../../../../docs/CONTRACT.md)。每例恰有 `problem.json`、`input.h5`、`surfaces.msh`。`task=cylindrical-field-pml-repair`、`spatial_dimension=2`、`physics.model=cylindrical-vacuum-pml-v1`，`geometries={}`、`conditions=[]`。本题仅涵盖下列固定真实 Meep 离散问题；不要求其他源、介质、模式或并行配置。

## 物理模型与尺度

长度L0=1 m，时间T0=L0/c0，c0=299792458 m/s；电场E0=1 V/m，磁场H0=E0/Z0，Z0为真空阻抗。带`unit=1`的数值均已归一化：长度除L0、时间除T0、频率乘T0、E除E0、H除H0。背景epsilon_r=mu_r=1、归一化光速1，初始场为0，无非线性和色散。真空Maxwell系统为∂t B=−curl E、∂t D=curl H−J、D=E、B=H；在柱坐标旋转基中将∂phi替为i*m，由固定库实现Yee离散及PML更新。二维坐标表按 `(r,z)` 顺序编码到协议 `(x,y)` 槽位，MSH第三坐标为0；物理场仍具有六个三维柱坐标分量，不将它们解释为二维向量。

复场角依赖为 `exp(i*m*phi)`，phi是从笛卡尔+x向+y增加的角度，r≥0、z沿轴，`(e_r,e_phi,e_z)`为右手基。真实调用 `volcyl(R+r_pml, 2*(Z+z_pml), resolution)` 并仅沿z居中；域为r∈[0,R+r_pml]、z∈[-Z-z_pml,Z+z_pml]。在r外端用`pml(r_pml,R)`，z两端用`pml(z_pml,Z)`，相加构成边界区域，目标反射1e-15、mean_stretch=1；外端保留原库终端条件。r=0采用原库柱轴正则场更新，不施加额外导体或周期边界。

源为r=z=0、角模式m的复Er点源，幅度source_amplitude（含符号），真实API `gaussian_src_time(1,.02,10)`、`add_point_source(Er,source,veccyl(0,0),amplitude)`。未切换为实场模式。源dipole为 `i/(2*pi)*exp(-(t-500)^2/(2*50^2))*exp(-i*2*pi*(t-500))`，在|t−500|>500外为0；电流由库内dipole离散差分得到，不换成简单高斯余弦电流。源空间权重保留该轴心点源API原义，幅度不按解析点偶极另行重标定。

内部网格为真实库均匀Yee网格，dr=dz=1/resolution，Courant=.5、dt=.5/resolution，单进程。所给MSH**只是三块观测面的母线**，不是电磁内部网格。每步推进后E的时间为t_n=n*dt，H的时间为t_n−dt/2；n从1起，到源结束1000之后再推进80，终点1080，N=2160*resolution步。time_axes中0只是有限窗口结果的静态标签。

## 参数与文件

`physics.parameters`恰含下列项，均`{"value":数值,"unit":"1"}`。除source_amplitude外必须使用JSON整数，禁止浮点整数、布尔及额外参数。

|参数|允许值|
|---|---|
|radius|2或3；R，观测圆柱半径|
|half_height|1或2；Z，观测圆柱半高|
|radial_pml|1或2；r_pml|
|axial_pml|1或2；z_pml|
|resolution|30或40；每L0格点数|
|mode|−1或+1；m|
|source_amplitude|有限数，0.25≤绝对值≤1|

`meshes={"observation":{"file":"surfaces.msh"}}`。MSH4.1 ASCII含四节点：1=(0,Z,0)、2=(R,Z,0)、3=(R,−Z,0)、4=(0,−Z,0)，恰三条type1线：tag11连接1→2、tag17连接2→3、tag23连接3→4。允许每节点的type15点元素；不得额外添加线、面、体、节点。它们依次旋转成+z端盖、侧面、−z端盖，外法向分别+e_z、+e_r、−e_z。下端盖的积分符号必须反转。

`locations`恰为：

```json
{"faces":{"kind":"mesh","mesh":"observation","entity":"element","dimension":1,"ids":"face_ids"},"field_probe":{"kind":"points","ids":"probe_ids","coordinates":"probe_coordinates"}}
```

`time_axes={"instant":"times"}`，`fields={}`。input.h5恰含四数组：

|key|dtype/shape|含义|
|---|---|---|
|face_ids|int64[3]|严格依次[11,17,23]，对应上述三整块旋转面|
|probe_ids|int64[1]|[7]|
|probe_coordinates|float64[1,2]|下文定义的真实居中采样点(r,z)|
|times|float64[1]|[0.]静态标签|

复场位置取原库 `gv[iveccyl(2*resolution+1,1)]`，输入计算顺序严格为`r=(2*resolution+1)*(0.5/resolution)`、`z=0.5/resolution`，采用float64，不以不同运算顺序重算并引入多格点采样。它位于内部非PML区。真实`add_dft_fields(...,use_centered_grid=true,decimation_factor=1)`将各分量从其交错Yee位置按库`yee2cent_offsets/avg1/avg2`居中平均到该点；这不是E/H原始存储点重合或免插值。每个分量均对应一个实际居中格点。

## 有限窗口观测

对任一实际居中分量F，频率固定f=1，复系数为

`Fhat = dt/sqrt(2*pi) * sum(n=1..N) F_n * exp(+i*2*pi*t_F,n)`，

其中t_E,n=n*dt，t_H,n=(n−.5)*dt。全部真实时间步均参加，stride固定1。复场不取绝对值、不取实部代替、不加额外周期平均。

对三块旋转面，谱通量为 `integral Re(Ehat cross conj(Hhat)) dot n dA`，使用原库`add_dft_flux(...,centered_grid=true,decimation_factor=1)`的实际分量平均与空间插值/梯形权重。端盖dA=2*pi*r*dr、侧面dA=2*pi*R*dz；`spectral_flux`记录各面**整块三维积分**，尽管协议位置对应二维母线的line element。没有额外1/2因子。即顶/底用`Erhat*conj(Hphihat)−Ephihat*conj(Hrhat)`，侧面用`Ephihat*conj(Hzhat)−Ezhat*conj(Hphihat)`的实部，底面再取负号。不得把点场单独相乘替代整面积分或只报告三面比例。

谱通量的归一化尺度为`E0^2*L0^2*T0^2/Z0`，复场尺度分别E0*T0与H0*T0。这些是有限时间傅里叶系数及其表面积分，不是瓦特、时间平均稳态功率或功率谱密度。参考对应**固定离散库的实际积分**，不是连续真空点偶极的极限公式。

## 输出

`outputs`恰含下表，全部dtype=float64、unit=`1`、time_axis=`instant`、无sampling；kind为scalar或components，component_shape分别[1]或[12]。

|对象名/array|quantity|location/value_kind|shape|components|
|---|---|---|---|---|
|spectral_flux|normalized_spectral_surface_flux|faces/integral|[1,3,1]|["value"]|
|observed_dft|normalized_centered_finite_dft|field_probe/point|[1,1,12]|Er_real,Er_imag,Ephi_real,Ephi_imag,Ez_real,Ez_imag,Hr_real,Hr_imag,Hphi_real,Hphi_imag,Hz_real,Hz_imag|
|time_step|normalized_time_step|field_probe/point|[1,1,1]|["value"]|
|window_end|normalized_window_end|field_probe/point|[1,1,1]|["value"]|

后两项报告实际dt及实际终止时间，不改变times=[0.]。结果HDF5按CONTRACT复制输出位置IDs及时间：face_ids、probe_ids、times，不能复制probe_coordinates、输入网格或其他数组。所有值须有限；不得隐式广播、交换实体、交换实虚分量或丢弃柱向分量。公开样例reference和grading文件可用于逐项检查。
