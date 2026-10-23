# 有限窗口复DTFT数据

遵循[CONTRACT](../../../../docs/CONTRACT.md)。每例只有`problem.json`和`input.h5`。`task=dft-decimation-repair`，`spatial_dimension=1`，`physics.model=finite-window-dft-v1`；`geometries={}`、`meshes={}`、`conditions=[]`。下面完整定义这种固定真实Meep离散模型及观测，未声明的介质、边界和驱动组合不在本题范围。

## 归一化、模型与真实推进

固定长度尺度L0=1 m、真空光速c0=299792458 m/s、时间尺度T0=L0/c0及场尺度E0=1 V/m，Z0为真空阻抗。所有带unit=`1`的本题数值均已无量纲化：长度z/L0、时间t/T0、频率f T0、Ex=E_x/E0、Hy=Z0 H_y/E0。电位移按epsilon0 E0归一化；线性背景epsilon_r=mu_r=1、归一化光速1。本题唯一空间坐标表示传播方向z；协议坐标仍以m写出，因为L0=1m，其数值恰等于归一化z。不能将无量纲频率/时步直接当成Hz/s。

在给定闭区间[nonlinear_lo,nonlinear_hi]内，电本构的无量纲系数为chi2、chi3，外部均0；其物理含义为D_x/(epsilon0 E0)=Ex+chi2 Ex²+chi3 Ex³，系数已分别吸收E0和E0²尺度。磁本构线性。由固定源码原有离散场更新推进，不另改物理推进算法或用连续解替代。两端使用真实`pml(pml_width)`，反射目标1e-15、mean_stretch=1，外部保留库原有终端条件；不添加周期/Bloch边界。初始E/H为0。

在z_s=−length/2+pml_width施加实Ex点源，幅度source_amplitude。真实调用`GaussianSource`对应的`gaussian_src_time(fc,1/tau,cutoff)`，fc=source_frequency、tau=envelope_width；采用库默认integrated电源与实场模式。其复dipole包络为`i/(2πfc)*exp(-(t-cutoff*tau)^2/(2*tau^2))*exp(-i*2πfc*(t-cutoff*tau))`，在`|t-cutoff*tau|>cutoff*tau`外为0，实场取实部；源电流是该dipole的库内离散差分，不用简单高斯余弦电流替换。source_amplitude乘这一真实一维点源幅度；电流尺度为epsilon0 E0/T0，点源的离散空间权重采用原库API。

采用原始`vol1d(length,resolution)`并居中，Courant=0.5，dz=1/resolution、dt=0.5/resolution；num_chunks只指定真实串行分块，不开启MPI。总单元数N_z=length*resolution为偶数整数。时间步为n=1,2,...，按原库推进后t_n=n*dt；从0开始运行，直到首次达到`source.last_time()+after_sources`。本题tau/cutoff/after_sources均整数，窗口终点T_end=2*tau*cutoff+after_sources，步数N=2*resolution*T_end；实际driver还返回真实终止时间，不将time_axes的静态标签0当作场只运行到0。

## 全局参数

`physics.parameters`恰含下表，均为`{"value":数值,"unit":"1"}`。注明整数者必须JSON整数，不使用浮点整数或布尔。

|参数|合法范围与含义|
|---|---|
|length|20..100；归一化全域长度|
|resolution|整数10..30；每L0格点数，N_z为偶整数且≤3000|
|pml_width|1..5，pml_width*resolution为整数，2*pml_width+2<length|
|source_frequency|0.2..0.5；归一化fc|
|envelope_width|整数20..80；高斯包络tau|
|source_amplitude|绝对值在[0.25,1]，可正可负|
|cutoff|整数5或6|
|after_sources|整数20..160；源结束后的运行窗口|
|chi2|−0.03..0.03|
|chi3|0..0.03|
|nonlinear_lo, nonlinear_hi|−length/2≤lo<hi≤length/2；本构系数为0时区间仍必须合法|
|num_chunks|整数1..3|
|decimation|整数0..8；0=自动，k>0=显式采样stride|
|monitor_index|整数，pml_width*resolution+2≤index≤N_z−pml_width*resolution−2|

空间区间可以只占部分域；非线性判断覆盖全部实际chunks，不能只看源或监测点所在处。区间端点以原库对闭区间系数函数的采样规则处理；不平滑或重标定chi系数。

## 请求轴、居中取样与数组

`locations={"probes":{"kind":"points","ids":"probe_ids","coordinates":"probe_coordinates"}}`。probe_ids为非负严格递增int64[Q]，3≤Q≤128。每行是一条带频率属性的观测请求，所有请求在同一实际空间位置，不能把频率当成坐标或按ID大小推断频率。对应频率存输入场frequency，而不是时间轴。

居中采样位置为精确有理数`z_c=(2*monitor_index+1-N_z)/(2*resolution)`；probe_coordinates为float64[Q,1]，每行恰为该有理数按最接近float64舍入后的值。这一规范写法避免分别相减造成格点两侧的舍入歧义。可信driver以`use_centered_grid=true`调用真实`add_dft_fields([Ex,Hy], volume(z_c), frequencies, ...)`，使用原库`yee2cent_offsets`及avg1/avg2对各分量Yee错位值作必要相邻平均/线性空间插值，每组件仅一个真实居中累加点；不假定E/H原生未插值位置重合。输出直接取真实dft_chunk累加器，适配器不重算频谱。此处不要求旧`get_dft_array`的零维数组后处理行为。

`time_axes={"instant":"times"}`，times为float64[0.0]，单位s，仅作这组有限窗口结果的静态标签。唯一输入场frequency：同名HDF5 key，quantity=`normalized_frequency`、unit=`1`、location=`probes`、time_axis=`instant`、dtype=`float64`、kind=`scalar`、component_shape=`[1]`、components=`["value"]`、value_kind=`point`，shape[1,Q,1]；数值在[0.05,2]并沿probe_ids轴严格递增。不声明sampling；它是逐请求的频率属性，不在空间或时间上插值/外推。

输入HDF5恰含probe_ids、probe_coordinates、times、frequency四项。无源时间数组、网格、额外材料场或隐藏驱动；完整驱动语义由以上参数定义。

## 自动及显式采样

显式decimation=k>0时，有无非线性都按给定k采样，保留该选择产生的离散混叠。自动decimation=0时，只要本题chi2或chi3在真实材料中非零，采用k=1；纯线性时保留原库策略：

`B = sqrt(-2*ln(1e-7))/(π*tau)`，`k=max(1,floor(1/(dt*(max_j(abs(frequency_j))+abs(fc)+B/2))))`。

B是该GaussianSource真正的get_fwidth()，不等于构造时的1/tau。源和监测频率均为正，故无零带宽例外。Ex与Hy属于同一个实际频率集合，必须报告一致的真实stride；driver读取`dft_chunk.get_decimation_factor()`，不由适配器按公式回填预期。

对于任一请求频率f，有限窗口结果为：

`Fhat(f) = k*dt/sqrt(2π) * sum_{1≤n≤N, n mod k=0} F_n * exp(+i*2π*f*t_F,n)`。

F_n为上述实际居中取样。Ex取t_F,n=t_n，Hy取t_F,n=t_n−dt/2，保持Yee时间错位；实部/虚部符号按正指数约定。窗口含最后一步，若k不能整除N，不添加虚构末样本或端点权重；起始n=0不累加。这是无量纲有限窗口DTFT，不归一化到峰值，不除以源幅度、总时长或频带宽，不只取模长，也不声称W/Hz、连续积分或稳态相量。

## 输出

所有输出location=probes、time_axis=instant、dtype=float64、value_kind=point，复制probe_ids与times；对象名和HDF5 key相同，unit均为1。它们是每条频率请求的观测/元数据，不表示时间0的瞬时场。

|对象/key|quantity|kind / component_shape / components|shape与意义|
|---|---|---|---|
|observed_dft|normalized_finite_dft|components / [4] / Ex_real,Ex_imag,Hy_real,Hy_imag|[1,Q,4]；上述复DTFT的实部、虚部|
|sampling_stride|sampling_stride|scalar / [1] / value|[1,Q,1]；真实正整数k，以float64存放；每请求相同|
|time_step|normalized_time_step|scalar / [1] / value|[1,Q,1]；实际dt，每请求相同|
|window_end|normalized_window_end|scalar / [1] / value|[1,Q,1]；真实N*dt，每请求相同|

评分同时检查四复分量及全部元数据。全部组件和请求属于同一冻结实现，不允许对不同请求换另一种场推进或输出程序。
