# 输入字段与连续条件

本文是题目输入约定，供程序实现数据接口。条件类型与数值按 JSON/NPZ 读取，不依赖文件名、边界名称或测试点编号判断物理含义。

## 参数、位置与场

`physics.model=incompressible_navier_stokes`。`parameters` 中每项是 `{value,unit}`：`density`（kg/m3）、`dynamic_viscosity`（Pa.s）、`x0`、`y0`、`length_x`、`length_y`（m）。采用动力粘度，运动粘度为 μ/ρ。

`main` 网格是声明矩形上的等距点阵及其一阶三角形；两方向各有 n+1 个节点，n∈{4,16,24,32,48,64}。节点按 tag 关联，网格读取顺序不等于 NPZ 行号。三角形方向和编号不限定。`domain` 为二维 Physical Group；四条边为一维 Physical Groups，名称只是辅助信息。

所有位置明确声明 IDs，壁面位置采用该组的节点集。场形状 `[T,N,2]` 的最后一轴固定为全局 x、y 分量；压力为 `[T,N,1]`。`conditions` 时间轴为单元素 `[0.0]`，其边界和体加速度值作用于整个求解区间，不是只在该采样时刻有效。

## 条件记录

| role / variable / operator | data 与程序应实施的语义 |
|---|---|
| `source / velocity / acceleration` | `value:{field:...}` 引用 domain 上的矢量场，单位 m/s2；方程右端是 **+ρa**，不是 +a。当前输入保证全域恒定。 |
| `boundary / velocity / dirichlet` | `value:{field:...}` 引用当前壁面节点上的速度矢量，单位 m/s。每条边开区间为恒定速度；方腔运动边角点单独取零，其他边一致静止。 |
| `boundary / velocity_pressure / periodic` | 该 location 是从边；`master_physical_tag:{value:JSON整数,unit:"1"}` 指定主边的一维 Physical Group tag。两组实体及节点的对应关系、平移矩阵使用 Gmsh `$Periodic`，不按数组行号配对。速度、压力及其对应导数周期相等，压力跳跃为零。每对只在从边写一条记录。 |
| `boundary / pressure / mean` | location 为 domain，`value:{value:0,unit:"Pa"}` 规定 **域面积平均压力为零**；这是一项全局规范条件，不是在每个域节点施加 p=0，也不是壁面压力条件。 |

周期条件的完整结构示例：

```json
{
  "role": "boundary", "variable": "velocity_pressure", "location": "right",
  "operator": "periodic",
  "data": {"master_physical_tag": {"value": 2, "unit": "1"}}
}
```

对一维周期通道，壁面运动和体加速度均平行于周期方向；体加速度沿流向驱动，压力是周期的压力部分。若改写成压差驱动，总压力的线性部分为 `−ρ a·(x,y)`；输出只提交本清单要求的周期压力 p。

通道雷诺数为 `Re=UH/(μ/ρ)`，H 为两壁距离，U 为壁面速度与稳态流速的最大绝对值；方腔为 `Re=U_lid L/(μ/ρ)`。Re 是范围说明，不新增重复的材料参数。

方腔无体加速度，只存在四边速度条件和压力零均值约束。运动边可为任意一边；水平边沿 ±x，竖直边沿 ±y，运动方向直接由矢量字段决定。开区间速度严格恒定，两个角点的零值不表示运动壁在第一个网格区间缓慢加速。角点与其相邻边的取值均明确，不由条件列表顺序决定。

## 输出

`outputs` 是唯一要求，不默认添加压力、完整矢量或网格数据。`velocity` 是节点全局速度（m/s），`pressure` 是满足域面积零均值的压力（Pa）。`u_centerline` 是 vertical 独立点位置处的全局 x 速度，`v_centerline` 是 horizontal 位置处的全局 y 速度，均为标量场，单位 m/s。

采样点坐标由对应 location 指向输入数组；输出不复制点坐标，只复制这两个位置的 IDs 和输出时间数组。不得把 points IDs 当作 Gmsh tag。求解器负责在请求位置求值，校验器不插值、不重排，也不检查散度、边界条件或压力规范。

按 `caeoj.sdk.load_problem` 读取数据；标量项用 `read_constant`，`{field:...}` 用 `read_field`；`write_result` 自动附带要求的 IDs 和时间轴。Gmsh 周期对应关系使用其 `getPeriodicNodes` 接口读取。Schema 与校验器只检查结构，以上条件的数学含义由程序实施。
