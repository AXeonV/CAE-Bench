# 输入与输出约定

本文是题目的一部分。`physics.model=advection_1d`，`physics.parameters.velocity={value:0.8,unit:"m/s"}`，表示全局 x 正方向的传播速度。

`main` 网格覆盖 `[0,1] m`。`cells` 引用 Physical Group `(1,1)` 的全部一阶线单元。各单元场的第 i 行对应该 location 的 IDs 数组第 i 项，单元的空间位置由网格端点坐标决定。

u 为无量纲标量，`kind=scalar`、`component_shape=[1]`、`components=["value"]`、`value_kind=average`。输入初始场的每个值定义所属单元在 t=0 时的常数值；单元间可不连续。周期延拓该初值，区间外不另给数据。

| 条件 | 数据 | 数学含义 |
|---|---|---|
| `role=initial`、`operator=assign` | `data.value={field:"initial_state"}` | 对整个 `cells` 赋初值；字段数值 shape 为 `[1,N,1]` |
| `role=boundary`、`operator=periodic` | `data.period={value:1.0,unit:"m"}` | 此一维区域的左右端点相连，`u(x+1,t)=u(x,t)`，在所有时刻生效 |

周期记录作用于整个 `cells` 区域，端点由其覆盖区间的最小和最大坐标确定；它不是对每个单元分别施加周期边界。条件记录不依赖网格组的名称。

`time_axes.initial` 为 `[0]`；`time_axes.output` 为全部请求时刻。求解使用数组中的实际时刻，输出原样复制，不能用十进制间隔另造时间数组。

读取条件中的初值引用可用 `read_field(problem, condition["data"]["value"])`，读取带单位标量可用 `read_constant`。输出的数值 key 由 `outputs.state.array` 指定；`write_result` 可附带要求的 IDs 和时间数组。输出不包含初始场或初始时间轴。

校验器只检查结构、引用和数组关联。
