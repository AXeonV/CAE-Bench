# 2.5.2 数据契约

本文件与[本题要求](instruction.md)、[通用契约](../../../../docs/CONTRACT.md) 定义本题输入输出。`spatial_dimension` 必须为 3，`physics.model` 必须为 `fluid-multiphase-free-surface-v1`；task 不携带物理含义。采用 `physics: {model, parameters}`，禁止同时出现 `profile`、`contract_version`、`analysis`、`materials`。

## 全局参数

`physics.parameters` 必须恰含下表各项，每项为 `{value: 有限数, unit: 表中代码}`。不接受选项、场引用、单位转换、额外物理参数或求解器控制参数。

| name | unit | 范围与含义 |
|---|---|---|
| time_start | s | 物理积分起点，任意有限实数 |
| time_end | s | 物理积分终点，严格大于 time_start |
| density_a | kg/m3 | a 相常密度，严格正 |
| viscosity_a | Pa.s | a 相动力黏度，严格正 |
| pressure_reference | Pa | 绝对压力基准，严格正 |

## 网格、位置与采样

恰好一个固定 Gmsh MSH 4.1 ASCII 一阶 D 维、按公共面连通的域；允许四面体、六面体、棱柱、金字塔，外边界必须导出一阶三角形或平面四边形。一个全域 location（名称可变）恰覆盖全部 D 维单元，初态、acceleration 和全部输出共用它。边界 location 恰好分割全部外边界，不重叠；不得用内部面。所有条件位置均为 mesh element，不使用独立点或节点条件。实体 ID 是身份，不按读取行号配对。

全部场为 float64、`value_kind: average`，表示给定单元或边界实体上的物理平均。标量 kind=scalar、component_shape=[1]、components=["value"]、shape=[T,N,1]；向量 kind=vector、component_shape=[D]、components=["x","y","z"]、shape=[T,N,D]。不可省略轴、展平或广播。

每个输入场显式声明 `sampling={space: uniform或piecewise_constant, time: constant或linear, extrapolation: forbid}`。空间重建为实体内常值；uniform 还要求同一帧所有实体值相等。constant 轴恰一个时刻，其值在物理区间内恒定（初态单帧仅作初态标记）；linear 轴至少覆盖 time_start—time_end，相邻样本线性插值，禁止外推。初态场时间轴恰含 time_start。输出时刻不规定内部时间步。

## 字段与条件

允许的 quantity、类型、单位如下；不接受其他 quantity 或单位，不转换单位。输入字段须被条件引用，quantity 必须匹配条件要求；字段对象名与 array 键可不同，均按显式引用解释。

| quantity | kind | unit | 含义 |
|---|---|---|---|
| alpha | scalar | 1 | a 相体积分数 α，0≤α≤1 |
| velocity | vector | m/s | 本题物理响应中定义的 Euler 速度场 |
| acceleration | vector | m/s2 | 各相共同外部体加速度 g，含全部重力；无隐含地球重力 |
| pressure | scalar | Pa | 绝对静压，非去静水压 |

条件仅用 CONTRACT 规定键，data 不得为空；没有 material 条件。标量数值使用 `{value: 数值, unit: 对应单位}` 或 `{field: 输入字段对象名}`；向量只允许场引用，不允许 JSON 内联数组。标量常数在整个作用区域和时间内均匀恒定。option 不可代替数值或场。引用场的 location 必须与条件相同。

全域初态变量恰为 **alpha, velocity**，各恰好一条 `role=initial, variable=变量名, operator=assign, location=全域, data={value: 数值数据}`。向量 value 必须为场引用。

每例恰好一条 `role=source, variable=acceleration, operator=assign, location=全域, data={value:{field:字段名}}`。即使零加速度也必须显式给零向量场。

初始 α 只能为 0 或 1，表示每个输入体单元内精确相指示量，单元边界集合确定初始界面，不能自选亚单元界面；初始两相都存在。后续 α 是精确相指示函数的单元体积平均。

每个外边界实体恰被一条 `role=boundary, variable=flow` 条件覆盖；不能用不同 tag 对同一几何面叠加条件，不按组名称猜物理。允许的 operator 与完整 data 为：

| operator | data 与物理含义 |
|---|---|
| wall | `{mechanical:{option:no_slip}}`；静止固壁；无滑移 |

仅支持 wall。液气界面外压为 pressure_reference；气区输出速度扩展为零、压力扩展为 pressure_reference。

初态须满足本题散度、边界及材料范围约束；不会通过数值投影偷偷修改初态。全程适用范围与连续问题相容性是输入保证，结构检查不能代替其物理证据。

## 输出与观测

必需输出 quantity 恰为 **alpha, pressure, velocity**，逐项一份，均使用初态同一全域 location、float64、average 和上述单位/分量。全部共用同一请求时间轴，位于 [time_start,time_end] 内，末时刻必须为 time_end。

pressure 在 time_start 若被请求，必须是连续问题确定且有证据的有限、唯一右迹（包括单元平均）。无此保证时，公共输出轴必须全部严格晚于 time_start 开始；不能用低残差、离散步长有限值、任意初始压力或差分率替代连续右迹。

穿界面单元的 velocity/pressure 为含前述气区扩展的全单元平均，不是液体内条件平均。α 的真实单元平均乘体积可线性复算相体积及常相密度下的相质量。含 rho*u的乘积量，不能由各因子的单元均值精确恢复，只能作带重建误差的近似，不据此严格守恒判分。界面总面积不能由含率数组唯一确定，不要求未定义的面积重建。不要求模型内部平滑变量或额外观测，不为整体量伪造点坐标；压力不重新定零。

结果仅含 outputs.array 所声明 dataset 及其引用的 IDs、时间数组，支持轴与输入逐值一致，共享键只写一次；禁止额外数组或属性、网格、点坐标和包外文件。可用 `caeoj.sdk.load_problem/write_result` 结构读写，物理求解由程序承担。
