# 2.9.1 数据说明

本题与[通用数据协议](../../../../docs/CONTRACT.md)共同定义输入输出；任务、资源与评分见[本题 instruction](instruction.md)。`spatial_dimension=2`；`physics.model` 精确为 `fluid-reduced-fully-wet-steady-v1`，`physics.parameters` 使用下述集合，不声明 `contract_version`、`profile`、`analysis`、`materials`，无隐含参数或自动单位换算。

## 文件、几何与采样

输入 `problem.json` 引用一个 Gmsh MSH 4.1 ASCII 一阶三角形网格及边界线段和一个扁平 HDF5；计算域连通且固定。坐标 m，时间 s，二维采用全局xy平面。`locations.domain` 是恰含全部网格节点的 mesh/node location。所有外边界必须导出；法向 n 指向域外。边界条件使用真实 mesh/element、dimension=1 的 location，以不相交分区恰好覆盖全部外边界；位置名不决定物理。本题平面是实际水平面积，不再乘单位出平面厚度。

数组遵循通用契约 `[T,N,*component_shape]`，IDs 为身份而非行号。域节点输入 `value_kind=point`、`sampling.space=piecewise_linear`，使用网格线性形函数连续重建；边界输入 `value_kind=average`、`sampling.space=piecewise_constant`，每个边界面常值。所有输入场显式提供 `sampling`，`extrapolation=forbid`。

域条件 location=`domain`，data 恰含 `value`：字段表示 `{"value":{"field":"字段名"}}`，非初态标量亦可用 `{"value":{"value":数值,"unit":"单位"}}`。物理初态必须引用场。矢量只能引用字段，禁止 JSON 内联数组。边界字段 location 与其条件完全一致。每个输入场必须被一个或多个条件引用。域字段 quantity 等于所引用变量名；边界 `data.value` 的字段 quantity 等于 condition.variable，其他 data 键的字段 quantity 等于该键名。均匀标量采用 `{value,unit}`，不作隐式换算。

稳态所有时间轴恰为单帧 `[0]`，所有输入 `sampling.time=constant`，无物理初态。连续条件交界处必须物理相容。

## 参数与域条件

所有参数为 `{value:有限数,unit:规定代码}`，精确包含下列集合，不可省略或添加。`drag_rate`非负；其余参数严格正。

参数：`density` (kg/m3)；`gravity` (m/s2)；`drag_rate` (1/s)。

必需域条件（每项恰一次，data只含value；括号依次为 role/operator、单位、分量类型、值域）：

- `bed`：`material/geometry`，`m`，scalar，finite。

值域 `positive` 为严格正，`finite` 为有限。域条件每项恰一次，除列出的条件与边界外无额外源项或物性字段。

bed 是固定地形；其输入必须为单帧、sampling.time=constant，在整个物理区间保持不变，不包含移动床做功。

## 连续模型与闭合

以下为连续求解目标，数值算法自选。∇、div 在实际求解坐标计算。除下述重力或壁面驱动外无体力、质量源、热源、粗糙度、旋转或反应。

g=gravity。底高程b=bed，向上为正；水深h≥0、自由面η=b+h、q=h u。单层：div(hu)=0；div(hu⊗u+g h²I/2)=−g h∇b−drag_rate·hu。材料恒密度，气压均匀并消去，无科氏力、风、降雨、入渗或黏性横向扩散。全湿题h严格正。床面连续分片线性。不连续水流采用满足物理能量不增的熵弱解。节点点值只在唯一连续迹存在处请求；数据保证观测节点不落在激波/接触跳跃或速度无唯一极限的干湿前沿上，不能用某个数值单元平均冒充点值。

水墙为不可穿透自由滑移（u·n=0）。储槽边界data给出外部状态，按法向一维浅水Riemann问题连接内部和储槽状态，只注入入射特征；流出特征取内部状态，切向速度随入流取储槽、出流取内部。单层不把全部储槽状态一律强制为Dirichlet。稳态至少有一个储槽，不纳入欠定的闭池总水量问题。

## 边界条件

每项 `role=boundary`。下列 variable、operator 和 data 键精确固定，所有列出键必需，不得添加。scalar 可为同 location 标量场或带单位常数；vector/tensor 必须为同 location 字段；option 使用 `{"option":"规定值"}`。

- operator=`water_wall`，variable=`water`；data：`mode`=option(impermeable)。
- operator=`water_reservoir`，variable=`water`；data：`depth`=scalar m positive; `velocity`=vector m/s finite。

## 输出与观测

`outputs` 至少请求 `depth`, `velocity`；其余仅可从下表选择。字段名任意，quantity 必须符合表列，所有输出 float64。完整数组、分量标签和复制 IDs/时间轴规则按通用契约，不得隐式换算。

| quantity | unit | kind |
|---|---|---|
| `depth` | `m` | scalar |
| `velocity` | `m/s` | vector |
| `water_flux` | `m2/s` | vector |
| `water_volume` | `m3` | scalar |

除 water_volume 外的域观测为真实网格节点点值，可使用节点子集，value_kind=point。只在物理场有唯一连续迹的位置和时刻请求点观测。边界分区交点及奇异角点若有多重迹或无界交换，不请求点值。不得把单元平均当作点值。

water_volume=∫h dA，使用 aggregate/source 指向恰含全部域单元的 location，operation=sum、value_kind=integral、单位m3；其余输出不使用 aggregate。water_flux=hu，沿xy分量，单位m2/s。

可直接按通用契约读写，无需SDK。可选 `caeoj.fluid_reduced.reduced_parameters(problem)` 读取常数；内部离散、无量纲化、插值与求解由考生负责。
