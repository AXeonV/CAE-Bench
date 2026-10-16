# magnetic-diffusion-elasticity 数据契约

入口problem.json及data_file引用的扁平HDF5；路径相对清单。physics恰含model、parameters，model=`multiphysics-magnetic-diffusion-elasticity-v1`；task可省略，出现须为`magnetic-diffusion-elasticity`。禁止profile、contract_version、analysis、materials混用。未列出的参数、位置、条件、字段、源或初态均不接受。

## 物理定义

厚度方向x∈[0,L]，横向剪切位移u沿y，偏置附近的小信号磁场H沿y。Re[fhat exp(+i omega t)]峰值复相量。
剪切应变S=u_x，tau=(Gm+i omega eta)S−b H，B=b S+mu H；tau_x=−rho omega²u，H_xx=i omega sigma0 B。
后一式来自准静态导电磁扩散，忽略位移电流；b是指定偏置点的线性互易系数，不是无偏置材料的任意磁致伸缩常数。机械左端u(0)=0。H方向始终沿+y，非端面外法向。

无额外体力、自由体电流源或电磁波入射；表面磁场已指定。eta>0，数据核验小信号与小应变有效性，不求非线性磁滞和饱和。

## 参数全集

parameters恰含下表所有键；每项恰含value、unit，value为有限JSON实数（布尔不算数值），unit严格按表，不隐式换单位。下列符号用于本题方程，未另列的源均为0。

| 参数 | 单位 | 定义与范围 |
|---|---|---|
| `length` | `m` | L，区间长度；严格正 |
| `density` | `kg/m3` | rho，体密度；严格正 |
| `shear_modulus` | `Pa` | Gm，厚度剪切弹性模量；严格正 |
| `viscosity` | `Pa.s` | eta，剪切Kelvin黏性；严格正 |
| `magnetic_permeability` | `H/m` | mu，定应变小信号磁导率；严格正 |
| `magneto_coefficient` | `T` | b，有符号偏置线性磁弹性系数；任意有限实数 |
| `electric_conductivity` | `S/m` | sigma0，参考温度电导率；严格正 |
| `omega` | `rad/s` | omega，角频率；严格正 |


## 空间与身份

spatial_dimension=1；geometries与meshes为空对象。连续体区间由length=L定义，没有未提供的CAD或求解网格。locations恰含domain、left、right。domain为points，2..2048个真实物理采样点，coordinates为float64[N,1]，单位m，x∈[0,L]，坐标两两不同，可不含端点且不按x排序；IDs为非负严格递增int64[N]。数组行始终依IDs，不按坐标重排输出。left、right各为entities、各一项非负int64 ID，代表x=0／x=L处实际端口或端面；无coordinates或空间插值。两端ID相同也不表示同一对象，不跨location匹配。无其他locations或几何。域采样只定义输出点，不指定内部网格或离散模型。

## 时间与数组

time_axes恰含state，引用float64[1]=[0.0]，输入和输出均用state。0仅是存储标记，不是物理初态或频率。

输入场、输出场均float64，数组完整shape=[T,N,*component_shape]，本题统一采用components、component_shape=[2]、components=["real","imag"]，末轴为峰值复数实部／虚部，value_kind=point。每个复字段按Re[fhat exp(+i omega t)]解释，omega只由参数给定，禁止幅相或RMS布局。逻辑field名和HDF5 array key可不同且自由；条件field引用前者，array引用后者。fields恰为条件实际引用的场，可由多个条件共享符合声明的同一场；不能按长度从其他位置借数据。

输入场sampling恰为space=uniform、time=constant、extrapolation=forbid。uniform只表示单个端口的值，不在不同端口之间插值；没有域输入场。quantity等于条件data键名，unit按下表，location与该条件相同，time_axis=state，dtype、kind、shape、components和value_kind按上述固定格式。所有data项必须用field引用；复常量也编码为一帧field。

## 条件全集

每个下列端口恰一条条件；未列端口按物理定义的固定零值闭合，不添加条件。role=boundary、variable=coupled_boundary、operator=prescribed、location为对应端口；data恰含该端口下表全部键，无额外键。condition本身恰含这五项。不同端口不能合并为一条条件。

### `left`

| data键 | unit | 物理值 |
|---|---|---|
| `magnetic_field` | `A/m` | H(0) |

### `right`

| data键 | unit | 物理值 |
|---|---|---|
| `magnetic_field` | `A/m` | H(L) |
| `traction` | `Pa` | tau(L)，作用于右面沿+y牵引 |

field表示片段（逻辑名可变，完整清单还需其他必填项）：

```json
{"data":{"magnetic_field":{"field":"boundary_value"}}}
```

## 输出全集

每个quantity至少请求一次，可重复请求，逻辑输出名与array key自由但不得重复占用数组key。均为上文类型、shape、components、float64及point，不带sampling，time_axis=`state`。domain输出是连续解在真实坐标的点值；端点取域内唯一迹，端面实体上的输出是该真实对象状态，不是区域积分。

| quantity | unit | location | 定义 |
|---|---|---|---|
| `displacement` | `m` | `domain` | 复u_y(x)，左端u(0)=0 |
| `magnetic_field` | `A/m` | `domain` | 复H_y(x) |

结果HDF5恰含所有输出array及所需locations的IDs、所需时间轴；严格复制输入轴和身份。domain坐标、输入场及不被输出使用的端口IDs不写入结果。不导出新网格或额外数组。

## 接收与验证边界

输入场／输出场各至多2000000数值分量（含时间和分量轴，重复输出也计入）。除可由声明检查器验证的参数、单位、轴和组合外，正式数据制作还须核验本题模型适用与小扰动／小应变接收条件、解与观测存在唯一性、参考精度及预算可达性；声明通过不构成这些证据。无正式数据时不能把协议fixture当物理参考。
