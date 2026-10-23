# 输入与输出

每个输入包含 N 个相互独立的材料与有限元程序。它们是给定状态的局部算子检查，无时间演化，不是烧结形貌模拟。材料状态在每个程序内空间均匀；可信框架将它们赋给两个节点和实际积分点，不由独立采样点暗示插值规则。

## 材料与变量

只使用 PARABOLIC 固相自由能。令 φ 为孔隙序参量，η₀..ηₙ₋₁ 为 n 个晶粒序参量，w 为化学势，c 为总浓度。φ、η、c 无量纲，w 单位 J，T 为 K。输入均采用 SI，原样传入真实类；此分支不使用其他自由能分支中的固定 eV/K 热常数，不进行隐藏单位换算。

平衡空位浓度为

`ceq(η)=b0+Σ ai·ηi + (1/2)ΣiΣj Bij·ηi·ηj`。

B 为对称矩阵。JSON 只保存上三角 Bij；非对角项在上述双重求和中出现两次，因此在展开多项式中的系数为 Bij，不是 Bij/2。未使用的 η 及对应 a、B 行列全为零。

令 h(φ)=0（φ≤0）、1（φ≥1），在 0<φ<1 时为 `6φ⁵−15φ⁴+10φ³`，s=1−h。四个目标系数为：

|输出名称|数学定义|单位|真实属性|
|---|---|---|---|
|void_minimum，记 A|h|1|hv_c_min|
|solid_minimum，记 Bc|s·ceq|1|hs_c_min|
|void_response，记 C|h/(Va·kv)|1/J|hv_over_kVa|
|solid_response，记 D|s/(Va·ks)|1/J|hs_over_kVa|

Va 为原子体积 m³，kv、ks 为孔隙/固相抛物能量系数 J/m³。目标导数变量按固定顺序 `q=(φ,η0,η1,η2,η3)`；全部无量纲，因此每个系数的值、对 q 的梯度及 Hessian 单位相同。要求完整的 φ–η、η–η 交叉项及对称两侧。夹持函数在 φ=0、1 的一、二阶导数都为零。非 active η 的导数为零。系数不依赖 w；w 的影响通过下述实际约束算子单独检查。

保留四个原有材料值：

- `void_number_density = w/(Va² kv)+1/Va`，单位 1/m³。
- `solid_number_density = w/(Va² ks)+ceq/Va`，单位 1/m³。
- `void_grand_potential = −w²/(2Va² kv)−w/Va`，单位 J/m³。
- `solid_grand_potential = −w²/(2Va² ks)−w·ceq/Va`，单位 J/m³。

strict_mass_conservation=0 或 1 都使用以上 PARABOLIC 定义；两者在本题观察量上同义。φ 可略越过 [0,1]，表示材料 API 的试探状态及夹持检查；不把所有试探值都解释为已收敛的物理体积分数。

## 真实有限元程序

每个程序有独立的一维线段 `[0,L]`，L=probe_length，单位 m，两个节点依次为 left、right。实际批处理线段可沿 x 平移到 `[3iL,(3i+1)L]`，互不连接；平移只用于分离程序。没有面积、厚度或体积因子。使用两个节点的 FIRST LAGRANGE 标量基函数 `Nleft=1−x/L`、`Nright=x/L`，两点 Gauss 求积，无边界约束、无消去的自由度。

上述全部状态在两个节点均取本程序输入值。材料约束残量固定为

`Ri=∫₀ᴸ Ni·[c−A−Bc−(C+D)w] dx`。

这是检查局部质量约束及其线性化的一维测试算子，不含界面梯度能或时间项。Ri 单位 m。Jacobian 对每一个节点上的 φ、η、w、c 自由度求偏导；两端值虽在基态相同，导数时仍分别扰动单个自由度并按上述基函数插值。输出仅含浓度约束行，行/列节点顺序都是 left、right。真实驱动使用 Reaction(c)、两个 MatBodyForce 及两个 MatReaction(c,v=w) 形成此符号。其他变量的 Reaction/BodyForce 行仅用于保持所给状态的检查系统，其行不计分；不把一次检查迭代后的状态当输入状态重新评分。

原生 PETSc 的第一个残量向量和 hand-coded/analytic Jacobian 是观察对象，不以其有限差分矩阵替换。实际 libMesh DOF 映射决定读取位置，不从变量数猜测编号。材料属性在 INITIAL 状态读取，时间零只是存储索引。

变量命名还检查真实耦合接口。variable_name_set=0 的内部名称依次为 `phi,eta0,eta1,eta2,eta3,w,c,T`；=1 时依次为 `pore_state,grain_a,grain_b,grain_c,grain_d,mu_state,fraction_state,thermal_state`。逻辑量、导数和输出顺序始终按本文件，不随内部名称改变。材料必须使用其真实配置的耦合变量名。

## 声明与输入数组

`task="grand-potential-derivatives-repair"`，`spatial_dimension=1`，`physics.model="grand-potential-material-programs-v1"`。`geometries`、`meshes` 为 `{}`，`conditions=[]`。位置唯一为 `programs={"kind":"entities","ids":"program_ids"}`，program_ids 是 1..8 个严格递增正整数的 int64 一维数组；它们标识独立程序，不引用实际网格标签。`time_axes={"instant":"times"}`，times 是 float64 `[0]`。

输入字段均为 float64、`location="programs"`、`time_axis="instant"`、`value_kind="point"`，采样为 `{"space":"uniform","time":"constant","extrapolation":"forbid"}`。各项 `array` 等于名称，标量 kind=scalar、component_shape=[1]、components=["value"]；eta 为 kind=components、component_shape=[4]、components=["eta0","eta1","eta2","eta3"]。

|名称|形状|quantity|unit|合法范围|
|---|---|---|---|---|
|phi|(1,N,1)|void_order_parameter|1|−0.1..1.1|
|eta|(1,N,4)|grain_order_parameters|1|0..1，inactive 项严格零|
|potential|(1,N,1)|chemical_potential|J|绝对值≤0.1·Va·min(ks·ceq,kv)|
|temperature|(1,N,1)|temperature|K|250..2000|
|concentration|(1,N,1)|total_concentration|1|0..1|

`physics.parameters` 恰含下列带单位有限标量，使用 `{"value":数值,"unit":单位}`。计数/选择为整数值，不使用 option 对象。物理浓度约束逐程序检查 `0.02≤ceq≤0.95`；化学势界保证原有两相数密度为正。

|参数|unit|范围/定义|
|---|---|---|
|grain_count|1|active η 数 n=1..4|
|strict_mass_conservation|1|0 或 1|
|variable_name_set|1|0 或 1|
|atomic_volume|m3|1e−30..1e−28，Va|
|void_energy_coefficient, solid_energy_coefficient|各 J/m3|各 1e8..1e11，kv、ks|
|surface_energy, grainboundary_energy|各 J/m2|各 0.01..5，原样材料参数|
|interface_width|m|1e−10..1e−8，原样 int_width|
|surface_switch_value|1|0.1..0.9，原样材料参数|
|probe_length|m|0.25..4，L|
|equilibrium_constant|1|0.05..0.8，b0|
|equilibrium_linear_0..3|各 1|ai，绝对值≤0.15，i≥n 时严格零|
|equilibrium_hessian_00,01,02,03,11,12,13,22,23,33|各 1|Bij 上三角，绝对值≤0.1，任一索引≥n 时严格零|

界面宽度与表面/晶界能是目标类的材料参数；该测试段长度不是烧结粒径，以上局部约束不使用界面梯度能来补充未知 PDE。其他自由能分支及其全部导数不在范围内。

HDF5 输入恰含 program_ids、times 和上表五个字段，无额外数组。没有用户表达式、额外源项、时间步或网格文件。真实平衡浓度材料由给定数值多项式设置，不由工具补充目标系数导数。

## 输出数组

全部结果为 float64，均位于 programs/instant，形状 `(1,N,C)`。`array` 等于名称，`value_kind="point"`；标量 C=1 使用 scalar/[1]/["value"]，其余使用 components/[C]。Hessian 和局部矩阵都是明确的变量/节点分量，不声明为笛卡尔空间 tensor。输出还须按 CONTRACT 原样复制 program_ids 和 times。

四个系数的值名称见首表。每个名称还分别有 `_gradient`（C=5）和 `_hessian`（C=25）。gradient 的 components 固定为 `phi,eta0,eta1,eta2,eta3`；hessian 按该顺序的行优先次序，名称为 `行_列`，如 `phi_phi,phi_eta0,...,eta3_eta3`。

|输出组|quantity|unit|
|---|---|---|
|A、Bc 值|phase_concentration_coefficient|1|
|A、Bc gradient / hessian|phase_concentration_gradient / phase_concentration_hessian|1|
|void_response 值 / gradient / hessian|void_response_coefficient / void_response_gradient / void_response_hessian|1/J|
|solid_response 值 / gradient / hessian|solid_response_coefficient / solid_response_gradient / solid_response_hessian|1/J|
|void_number_density, solid_number_density|各 number_density|1/m3|
|void_grand_potential, solid_grand_potential|各 grand_potential_density|J/m3|

最后四项有限元输出为：

|名称|C / components 顺序|quantity|unit|
|---|---|---|---|
|constraint_residual|2：left,right|concentration_constraint_residual|m|
|constraint_state_jacobian|20：依次对 phi,eta0,eta1,eta2,eta3，每个变量按行节点再列节点，名称如 phi_left_left、phi_left_right、phi_right_left、phi_right_right，随后 eta0..eta3|constraint_state_jacobian|m|
|constraint_potential_jacobian|4：left_left,left_right,right_left,right_right|constraint_potential_jacobian|m/J|
|constraint_concentration_jacobian|4：同上|constraint_concentration_jacobian|m|

所有输出保持原单位；逆能量系数误差的特征能量尺度只用于 instruction 规定的计分，不改变实际返回值。必须有限且包含全部程序和分量；不能只返回范数、对角项、差分 Jacobian 或局部点值来替代所定义的积分项。
