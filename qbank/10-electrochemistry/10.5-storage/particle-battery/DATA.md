# particle-battery 数据契约

入口problem.json及data_file引用的扁平HDF5，路径相对清单。顶层采用CONTRACT结构，physics恰含model、parameters；model=`electrochemistry-particle-battery-v1`，task可省略，出现须为`particle-battery`。禁止profile、contract_version、analysis、materials混用；不接受未列参数、条件、字段或位置。

## 物理定义与支持组合

恒温双电极锂插层单颗粒电池，每极一个代表性球颗粒。i=n,p；∂t c_i=D_i r⁻² ∂r(r²∂r c_i)，中心取正则球对称解∂r c_i(0)=0。a_i=3ε_i/R_i为单位电极体积真实活性面积；J按电池几何截面积计、放电为正，j_n=J/(a_n L_n)、j_p=−J/(a_p L_p)。表面向外锂摩尔通量−D_i∂r c_i(R_i)=j_i/F，初态c_i=θ_i0 cmax_i均匀，J(0)=0。θ_i,s=c_i(R_i)/cmax_i；j0_i=b_i√(θ_i,s(1−θ_i,s))，η_i=2RT/F·asinh(j_i/(2j0_i))。U_i由输入三次多项式在表面θ求值，两个OCP使用同一电位参考。Vcell=U_p+η_p−U_n−η_n−J RΩ，正极端子减负极端子。忽略电解液浓度／电势梯度、双电层、机械和热反馈；RΩ已含指定串联欧姆贡献，不另加任意电阻或过电位。全过程颗粒浓度须在[1e−6,1−1e−6]cmax内，由正式数据独立验证；输入初态合法不证明全过程适用。

## 全局参数

parameters恰含下表全部项；各项只有value、unit，数值有限，布尔不能作数值，JSON整数要求不得用浮点数替代。全部无缺省。

| 参数 | 单位 | 含义与值域 |
|---|---|---|
| `temperature` | `K` | 恒定温度T>0 |
| `gas_constant` | `J/(mol.K)` | 输入明确给定气体常数R>0 |
| `faraday` | `C/mol` | 输入明确给定法拉第常数F>0 |
| `area_resistance` | `Ohm.m2` | 电池单位几何截面积串联电阻RΩ≥0 |

## 位置、几何及身份

spatial_dimension=1，meshes、geometries均为空。entities表示真实有限对象，无虚构坐标；维度1表示球内径向坐标。IDs为int64、非负、严格递增，身份仅在location内有效，字段N轴按IDs行序对应，不按ID数值作数组下标。points坐标为float64[N,1]、单位m，表示从相应球心测得的半径r，不是笛卡尔直线上的平面扩散坐标。

| location | kind、数量 | 完整语义 |
|---|---|---|
| `electrodes` | entities，2..2项 | IDs必须恰[0,1]；0负极n、1正极p，含两种代表性球形固体颗粒 |
| `cell` | entities，1..1项 | 唯一电池；驱动电流密度按几何截面积计 |
| `negative_probes` | points，1..256项 | 该电极颗粒内真实径向坐标r，0≤r≤对应R，允许表面／中心及重复坐标 |
| `positive_probes` | points，1..256项 | 该电极颗粒内真实径向坐标r，0≤r≤对应R，允许表面／中心及重复坐标 |

## 时间、数组及重建

time_axes恰含initial、drive、observe。initial引用float64[1]=[0.0]；observe引用float64[T]，1≤T≤129，首项≥0且末项H>0；drive引用float64[B]，2≤B≤129、首项0且末项H，中间严格递增。输出只用observe，材料与初态用initial，驱动条件用drive。驱动逐对象在相邻时刻线性插值，覆盖[0,H]，不外推；输出请求不是内部时间步。

场均float64，完整形状[T,N,*component_shape]。scalar为[1]、components=["value"]；components按表中shape行优先展平标签为c1..cL（L为分量总数）。OCP的c1..c4依次为0..3次多项式系数。

所有data只允许{"field":"逻辑字段名"}，禁止内联数值、option或数组。fields恰为实际被引用场；quantity等于data键名，键value例外等于该条件variable；逻辑字段名与array key自由且区分。字段必须在对应条件同location及上表规定时间轴，不能借相同数组长度配对其他身份。每字段均point，sampling显式，space=uniform、extrapolation=forbid；drive场time=linear，其他场time=constant。uniform表示各对象上给定值，不要求不同对象行相同，不作实体或观测点之间插值；连续物理解由方程求出，禁止把输入采样当内部解网格。

## 条件全集

### `particles`

role=`material`，variable=`particle`，operator=`particles`，location=`electrodes`；所引用字段均为time_axis=`initial`（条件记录本身不含time_axis键）。恰一条，完整覆盖该位置。data恰含：

| 键 | 类型、单位及含义 |
|---|---|
| `radius` | scalar [1]，`m`；球颗粒半径R_i>0 |
| `diffusivity` | scalar [1]，`m2/s`；固相恒定D_i>0 |
| `maximum_concentration` | scalar [1]，`mol/m3`；固体体积最大浓度cmax_i>0 |
| `solid_fraction` | scalar [1]，`1`；电极固相体积分数ε_i，0<ε_i≤1 |
| `thickness` | scalar [1]，`m`；电极厚度L_i>0 |
| `exchange_scale` | scalar [1]，`A/m2`；按真实活性面积计的b_i>0，j0_i=b_i√(θ_i,s(1−θ_i,s)) |
| `ocp` | components [4]，`V`；OCP三次多项式系数b0,b1,b2,b3；U_i(θ)=b0+b1θ+b2θ²+b3θ³，两极共用电位参考 |
### `initial`

role=`initial`，variable=`stoichiometry`，operator=`initial`，location=`electrodes`；所引用字段均为time_axis=`initial`（条件记录本身不含time_axis键）。恰一条，完整覆盖该位置。data恰含：

| 键 | 类型、单位及含义 |
|---|---|
| `value` | scalar [1]，`1`；各颗粒初始均匀θ_i0，1e−6≤θ_i0≤1−1e−6 |
### `current`

role=`source`，variable=`applied_current`，operator=`current`，location=`cell`；所引用字段均为time_axis=`drive`（条件记录本身不含time_axis键）。恰一条，完整覆盖该位置。data恰含：

| 键 | 类型、单位及含义 |
|---|---|
| `value` | scalar [1]，`A/m2`；几何截面积放电为正的J(t)；t=0必须为0 |

## 输出

每个下列quantity至少出现一次，可重复请求；逻辑名及array key自由。全部float64、point、observe轴，无sampling，分量规则同上。必须使用表中完整location及全部对象，不能新增输出位置、重排身份或省略分量。输出是瞬时状态，不是时间平均、单元平均或整体积分。

| quantity | 类型、单位、含义 | location |
|---|---|---|
| `solid_concentration_negative` | scalar [1]，`mol/m3`；该颗粒内c_i(r,t)，按固体体积计 | `negative_probes` |
| `solid_concentration_positive` | scalar [1]，`mol/m3`；该颗粒内c_i(r,t)，按固体体积计 | `positive_probes` |
| `surface_stoichiometry` | scalar [1]，`1`；每极表面θ_i,s=c_i(R_i,t)/cmax_i | `electrodes` |
| `cell_voltage` | scalar [1]，`V`；正极端子减负极端子电压Vcell | `cell` |

结果HDF5只含输出array和必需IDs／时间轴，严格复制输入支持数组；不输出输入场、坐标、网格或额外数组。t=0固相浓度与表面θ由均匀初态给出，J(0)=0，端电压为两极初始OCP之差。

## 接收限制

electrodes IDs严格为[0,1]；negative_probes对应负极第0行、positive_probes对应正极第1行的半径，两个径向域互不拼接。首帧J精确为0。正式数据须核验全过程浓度范围，不以参考截断或表面θ投影使平方根合法。

对象数量、参数及场值范围见各表；输入和输出场各≤2000000数值分量。正式数据还须独立核验本题模型及材料适用、给定条件相容、所请求观测存在、参考精度与预算内可达性。涉及浓度场或库存演化时须验证全过程非负与适定性，排除任意病态尺度和无限刚性组合。声明检查不证明物理解、参考或数值准确性。不从目录、来源软件或隐藏配置补题意。
