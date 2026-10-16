# shunted-piezoelectric-rod 数据契约

入口problem.json及data_file引用的扁平HDF5；路径相对清单。physics恰含model、parameters，model=`multiphysics-shunted-piezoelectric-rod-v1`；task可省略，出现须为`shunted-piezoelectric-rod`。禁止profile、contract_version、analysis、materials混用。未列出的参数、位置、条件、字段、源或初态均不接受。

## 物理定义

采用Re[fhat exp(+i omega t)]，所有负载及输出为峰值复相量。S=u_x，Ef=−phi_x，sigma=(E+i omega eta)S−e Ef，D=e S+eps Ef。
sigma_x=−rho omega²u，D_x=0；左端u=phi=0，右端sigma=s，phi(L)=V为未知电极电压。
右电极自由电荷Q=−A D(L)，对地并联电导G与电容Cs，注入电极的外部电流I满足(G+i omega Cs)V+i omega Q=I。该电流方向与右电极电荷符号固定，不可改用Q=+A D。

eta>0排除无损机械极点；omega>0、eps>0，理想电极覆盖整个端面。数据保证唯一有限响应且|u_x|≤0.01。不计电磁传播或体漏电。

## 参数全集

parameters恰含下表所有键；每项恰含value、unit，value为有限JSON实数（布尔不算数值），unit严格按表，不隐式换单位。下列符号用于本题方程，未另列的源均为0。

| 参数 | 单位 | 定义与范围 |
|---|---|---|
| `length` | `m` | L，区间长度；严格正 |
| `young_modulus` | `Pa` | E，本题一维轴向弹性模量；不再作三维平面应变换算；严格正 |
| `piezo_coefficient` | `C/m2` | e，有符号应力电荷耦合系数；任意有限实数 |
| `permittivity` | `F/m` | eps，定应变介电常数；严格正 |
| `density` | `kg/m3` | rho，体密度；严格正 |
| `viscosity` | `Pa.s` | eta，轴向Kelvin黏性；严格正 |
| `omega` | `rad/s` | omega，角频率；严格正 |
| `area` | `m2` | A，均匀压电杆截面积，同时为理想电极覆盖的端面面积；严格正 |
| `shunt_conductance` | `S` | G，并联电导；非负 |
| `shunt_capacitance` | `F` | Cs，并联电容；非负 |


## 空间与身份

spatial_dimension=1；geometries与meshes为空对象。连续体区间由length=L定义，没有未提供的CAD或求解网格。locations恰含domain、left、right。domain为points，2..2048个真实物理采样点，coordinates为float64[N,1]，单位m，x∈[0,L]，坐标两两不同，可不含端点且不按x排序；IDs为非负严格递增int64[N]。数组行始终依IDs，不按坐标重排输出。left、right各为entities、各一项非负int64 ID，代表x=0／x=L处实际端口或端面；无coordinates或空间插值。两端ID相同也不表示同一对象，不跨location匹配。无其他locations或几何。域采样只定义输出点，不指定内部网格或离散模型。

## 时间与数组

time_axes恰含state，引用float64[1]=[0.0]，输入和输出均用state。0仅是存储标记，不是物理初态或频率。

输入场、输出场均float64，数组完整shape=[T,N,*component_shape]，本题统一采用components、component_shape=[2]、components=["real","imag"]，末轴为峰值复数实部／虚部，value_kind=point。每个复字段按Re[fhat exp(+i omega t)]解释，omega只由参数给定，禁止幅相或RMS布局。逻辑field名和HDF5 array key可不同且自由；条件field引用前者，array引用后者。fields恰为条件实际引用的场，可由多个条件共享符合声明的同一场；不能按长度从其他位置借数据。

输入场sampling恰为space=uniform、time=constant、extrapolation=forbid。uniform只表示单个端口的值，不在不同端口之间插值；没有域输入场。quantity等于条件data键名，unit按下表，location与该条件相同，time_axis=state，dtype、kind、shape、components和value_kind按上述固定格式。所有data项必须用field引用；复常量也编码为一帧field。

## 条件全集

每个下列端口恰一条条件；未列端口按物理定义的固定零值闭合，不添加条件。role=boundary、variable=coupled_boundary、operator=prescribed、location为对应端口；data恰含该端口下表全部键，无额外键。condition本身恰含这五项。不同端口不能合并为一条条件。

### `right`

| data键 | unit | 物理值 |
|---|---|---|
| `traction` | `Pa` | 复应力s |
| `current` | `A` | 外部向右电极注入的复电流I |

field表示片段（逻辑名可变，完整清单还需其他必填项）：

```json
{"data":{"traction":{"field":"boundary_value"}}}
```

## 输出全集

每个quantity至少请求一次，可重复请求，逻辑输出名与array key自由但不得重复占用数组key。均为上文类型、shape、components、float64及point，不带sampling，time_axis=`state`。domain输出是连续解在真实坐标的点值；端点取域内唯一迹，端面实体上的输出是该真实对象状态，不是区域积分。

| quantity | unit | location | 定义 |
|---|---|---|---|
| `displacement` | `m` | `domain` | 复u(x) |
| `electric_potential` | `V` | `domain` | 复phi(x) |

结果HDF5恰含所有输出array及所需locations的IDs、所需时间轴；严格复制输入轴和身份。domain坐标、输入场及不被输出使用的端口IDs不写入结果。不导出新网格或额外数组。

## 接收与验证边界

输入场／输出场各至多2000000数值分量（含时间和分量轴，重复输出也计入）。除可由声明检查器验证的参数、单位、轴和组合外，正式数据制作还须核验本题模型适用与小扰动／小应变接收条件、解与观测存在唯一性、参考精度及预算可达性；声明通过不构成这些证据。无正式数据时不能把协议fixture当物理参考。
