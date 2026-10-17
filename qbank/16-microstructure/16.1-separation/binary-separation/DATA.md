# binary-separation 数据契约

入口problem.json和data_file引用的扁平HDF5遵循CONTRACT，所有路径相对清单目录。physics恰含model、parameters，model=`microstructure-binary-separation-v1`；task可省略，出现只能为`binary-separation`。不接受profile、contract_version、analysis或materials混用。

## 物理与边界

c为相对于参考成分缩放的无量纲成分偏差，可为负，不是原子数密度。体自由能密度f=A(c²−1)²/4，梯度能κ|∇c|²/2，化学势μ=A(c³−c)−κΔc，单位J/m3。动力学∂t c=∇·[M0(1+αc²)∇μ]，M0>0、α≥0。必须保留变量迁移率在散度内，不把它错误移到Δμ前，也不在每步重新投影均值。无对流、反应或热噪声，周期封闭系统保持c的空间均值。给定非线性多项式响应不裁剪c，演化中不强制c∈[−1,1]。

二维连续周期矩形Ω=[0,Lx)×[0,Ly)，x、y单位m。场及本题动力学涉及的全部阶空间导数在两对边周期匹配；没有墙面、流入／流出或隐藏表面能。材料系数均匀、恒定，没有外驱。

## 参数全集

physics.parameters恰含下表全部项，每项仅value和unit；所有数值有限，布尔不可作数值，整数必须JSON整数。

| 参数 | 单位 | 定义及范围 |
|---|---|---|
| `length_x` | `m` | 周期长度Lx>0；1e-09≤value；value≤0.001 |
| `length_y` | `m` | 周期长度Ly>0；1e-09≤value；value≤0.001 |
| `energy_scale` | `J/m3` | 自由能系数A>0；1.0≤value；value≤1000000000.0 |
| `gradient` | `J/m` | 梯度能系数κ>0 |
| `mobility` | `m5/(J.s)` | M0>0，按本题守恒动力学定义；1e-30≤value；value≤1e-06 |
| `mobility_contrast` | `1` | 非线性迁移率系数α≥0，允许0；0.0≤value；value≤4.0 |

## 对象与身份

spatial_dimension=2；meshes和geometries必须为空，不存在未给定空间网格。locations恰含system、modes、probes：system为entities且IDs恰[0]；modes为entities，1..32个系数对象，IDs非负严格递增，可不连续；probes为points，1..128个真实坐标，coordinates为float64[N,2]，0≤x<Lx、0≤y<Ly，IDs非负严格递增，不要求坐标排序。探针不是内部计算网格，重复坐标允许，但身份独立。

## 初态的连续定义

令状态向量u的分量顺序为[c]，s=1。在全部连续周期矩形上严格定义u_a(x,y,0)=m_a+Σ_j[a_ja cosθ_j+b_ja sinθ_j]，θ_j=2π(kx_j x/Lx+ky_j y/Ly)。m取offset，a、b取series.amplitude，波矢取series.wave；不能把模态ID当波数，也不按探针重建初态。每个波矢必须为非零、各分量绝对值≤8的精确整数，规范方向为kx>0或kx=0且ky>0；波矢对两两不同。模态按IDs行序对应系数，无强制频率排序。允许所有系数为0，因此均匀初态合法；没有未给定随机扰动。逐分量R_a=Σ_j sqrt(a_ja²+b_ja²)，要求|m_a|+R_a≤1，只限定初态，不对演化场裁剪或重新缩放。此有限三角级数仅定义初态；求解对象为连续非线性初边值问题，非线性产生的新谐波不得截断到输入模态集合。内部空间分辨率、基函数及时间步由考生选择并控制误差。

## 时间与场数组

time_axes恰含static和requests。static引用float64[1]的[0.0]。requests引用float64[T]，1≤T≤256，严格递增、首项≥0、末项t_end>0；不要求包含0。初态总在物理t=0，输出只在requests时刻，内部步长自由。时间单位s，数组key自由。初始及材料字段引用static，输出全部引用requests。

所有字段float64，shape=[T,N,*component_shape]；T按字段time_axis，N按location IDs。scalar的component_shape=[1]、components=["value"]；components类型按表shape，components标签为按行优先展开的c1..cL，末轴变化最快。所有value_kind=point；entities字段是对象自身系数，不是空间平均或探针值。data只接受{"field":"逻辑字段名"}；fields记录的array才是HDF5 key，两种名称自由。字段与引用必须同location及所定时间轴；quantity等于data键名，value例外等于该条件variable。fields恰为实际被引用项，无内联常量、选项或隐式广播。

每个输入字段显式sampling：space=uniform（独立系数对象之间无插值）、extrapolation=forbid；static的time=constant。连续初态按上节公式，不能按sampling枚举猜测空间插值。

## 条件全集

conditions恰含2条记录，下列每种operator各一条，无其他条件；记录顺序自由。

### `offset`

conditions中该operator恰一条完整记录：role=`initial`，variable=`state_offset`，operator=`offset`，location=`system`，字段时间轴=`static`；data恰含下列全部键，无默认值：

| data键 | 类型、单位及含义 |
|---|---|
| `value` | components [1]；`1`；初态各分量空间均值m_a，顺序[c] |

### `series`

conditions中该operator恰一条完整记录：role=`initial`，variable=`initial_series`，operator=`series`，location=`modes`，字段时间轴=`static`；data恰含下列全部键，无默认值：

| data键 | 类型、单位及含义 |
|---|---|
| `wave` | components [2]；`1`；整数波矢(kx,ky)，由float64精确整数存储，不是物理波数 |
| `amplitude` | components [1,2]；`1`；每状态的cos／sin系数，shape=[s,2]最内层依次a、b |

## 输出

每种quantity至少一次，可重复请求；逻辑字段名及array key自由。均为probes上连续解的指定时刻点值，float64、value_kind=point、time_axis=requests、无sampling；shape及分量标签遵循上节，不是空间／时间平均。

| quantity | 类型、单位与含义 |
|---|---|
| `composition` | scalar [1]；`1`；c，成分偏差点值 |
| `chemical_potential` | scalar [1]；`J/m3`；μ或μc，按本题公式的绝对势，无任意常量平移 |

结果仅含输出array及其输入probes IDs／requests时间数组的精确副本；不导出坐标、输入模态、内部离散或其他数组。势和驱动力必须按给定绝对公式输出，不能借动力学只依赖导数而加常量；不旋转、平移组织或拟合幅度。

## 接收限制

令ℓ0=min(Lx,Ly)，A=energy_scale。要求max(Lx,Ly)/ℓ0≤4、0<t_end≤1e9 s。每个梯度系数κ都满足κ/(Aℓ0²)∈[0.0025,0.1]。τc=M0 A t_end/ℓ0²≤1。上述接收范围包含端点，用于限定界面尺度、长宽比与演化跨度。全部请求的连续观测可表示为有限float64，并可在公开资源预算内达到评分精度。

输入场及输出场总分量分别≤2000000。所有浮点值有限，初态的保守范围按上节逐项检查。
